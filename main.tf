resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = var.log_analytics_workspace_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = var.log_analytics_sku
  retention_in_days   = 30
}

resource "azurerm_recovery_services_vault" "this" {
  name                = "${var.vm_name}-rsv"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "Standard"
  soft_delete_enabled = true
}

resource "azurerm_backup_policy_vm" "daily" {
  name                = "${var.vm_name}-daily-policy"
  resource_group_name = azurerm_resource_group.this.name
  recovery_vault_name = azurerm_recovery_services_vault.this.name

  timezone = "UTC"

  backup {
    frequency = "Daily"
    time      = "23:00"
  }

  retention_daily {
    count = 30
  }
}

resource "azurerm_virtual_network" "this" {
  name                = "${var.vm_name}-vnet"
  address_space       = [var.virtual_network_cidr]
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
}

resource "azurerm_subnet" "this" {
  name                 = "${var.vm_name}-subnet"
  resource_group_name  = azurerm_resource_group.this.name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes     = [var.subnet_cidr]
}

resource "azurerm_network_security_group" "winrm" {
  name                = "${var.vm_name}-nsg"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  security_rule {
    name                       = "allow-winrm"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5986"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-rdp"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3389"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_public_ip" "this" {
  name                = "${var.vm_name}-pip"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_network_interface" "this" {
  name                = "${var.vm_name}-nic"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.this.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.this.id
  }
}

resource "azurerm_network_interface_security_group_association" "this" {
  network_interface_id      = azurerm_network_interface.this.id
  network_security_group_id = azurerm_network_security_group.winrm.id
}

resource "azurerm_windows_virtual_machine" "this" {
  name                  = var.vm_name
  location              = azurerm_resource_group.this.location
  resource_group_name   = azurerm_resource_group.this.name
  size                  = "Standard_D4s_v5"
  admin_username        = var.admin_username
  admin_password        = var.admin_password
  network_interface_ids = [azurerm_network_interface.this.id]

  enable_automatic_updates = false

  os_disk {
    name                 = "${var.vm_name}-osdisk"
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  source_image_reference {
    publisher = "MicrosoftWindowsServer"
    offer     = "WindowsServer"
    sku       = "2022-datacenter"
    version   = "latest"
  }
}

resource "azurerm_managed_disk" "ws2025_iso" {
  name                 = "${var.vm_name}-ws2025-iso"
  location             = azurerm_resource_group.this.location
  resource_group_name  = azurerm_resource_group.this.name
  storage_account_type = "Premium_LRS"
  create_option        = "Import"
  source_uri           = var.ws2025_iso_source_uri
  disk_size_gb         = var.iso_disk_size_gb
}

resource "azurerm_virtual_machine_data_disk_attachment" "ws2025_iso" {
  managed_disk_id    = azurerm_managed_disk.ws2025_iso.id
  virtual_machine_id = azurerm_windows_virtual_machine.this.id
  lun                = 10
  caching            = "ReadOnly"
}

resource "null_resource" "ws2025_upgrade" {
  depends_on = [azurerm_virtual_machine_data_disk_attachment.ws2025_iso]

  triggers = {
    iso_version = var.upgrade_trigger_version
  }

  connection {
    type        = "winrm"
    user        = var.admin_username
    password    = var.admin_password
    https       = true
    insecure    = true
    host        = azurerm_public_ip.this.ip_address
  }

  provisioner "file" {
    source      = "${path.module}/scripts/upgrade-ws2025.ps1"
    destination = "C:/Temp/upgrade-ws2025.ps1"
  }

  provisioner "remote-exec" {
    inline = [
      "powershell -ExecutionPolicy Bypass -Command \"New-Item -ItemType Directory -Path C:/Logs -Force | Out-Null\"",
      "powershell -ExecutionPolicy Bypass -File C:/Temp/upgrade-ws2025.ps1"
    ]
  }
}

resource "null_resource" "post_upgrade_configuration" {
  depends_on = [null_resource.ws2025_upgrade]

  triggers = {
    playbook_path = var.ansible_playbook_path
    dsc_path      = var.dsc_configuration_path
  }

  connection {
    type        = "winrm"
    user        = var.admin_username
    password    = var.admin_password
    https       = true
    insecure    = true
    host        = azurerm_public_ip.this.ip_address
  }

  provisioner "remote-exec" {
    inline = [
      "powershell -ExecutionPolicy Bypass -Command \"Start-DscConfiguration -Path '${var.dsc_configuration_path}' -Force -Wait -Verbose\"",
      "powershell -ExecutionPolicy Bypass -Command \"if (Test-Path '${replace(var.ansible_playbook_path, "\\", "\\\\")}') { ansible-playbook '${replace(var.ansible_playbook_path, "\\", "\\\\")}' } else { Write-Host 'Ansible playbook path not found, skipping.' }\""
    ]
  }
}

resource "azurerm_backup_protected_vm" "this" {
  resource_group_name = azurerm_resource_group.this.name
  recovery_vault_name = azurerm_recovery_services_vault.this.name
  source_vm_id        = azurerm_windows_virtual_machine.this.id
  backup_policy_id    = azurerm_backup_policy_vm.daily.id
}

resource "azurerm_monitor_diagnostic_setting" "vm" {
  name                       = "${var.vm_name}-diag"
  target_resource_id         = azurerm_windows_virtual_machine.this.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  metric {
    category = "AllMetrics"
    enabled  = true
  }

  log {
    category = "Administrative"
    enabled  = true
  }

  log {
    category = "Security"
    enabled  = true
  }

  log {
    category = "Alert"
    enabled  = true
  }
}

resource "azurerm_monitor_action_group" "backup_failures" {
  name                = "${var.vm_name}-backup-ag"
  resource_group_name = azurerm_resource_group.this.name
  short_name          = var.action_group_short_name

  email_receiver {
    name          = "backup-email"
    email_address = var.action_group_email
  }
}

resource "azurerm_monitor_activity_log_alert" "backup_failed" {
  name                = "${var.vm_name}-backup-failure"
  resource_group_name = azurerm_resource_group.this.name
  scopes              = [azurerm_recovery_services_vault.this.id]
  description         = "Alert when VM backup fails."

  criteria {
    category       = "Backup"
    operation_name = "Microsoft.RecoveryServices/vaults/backupFabrics/protectionContainers/protectedItems/backup/action"
    status         = "Failed"
  }

  action {
    action_group_id = azurerm_monitor_action_group.backup_failures.id
  }
}

resource "azurerm_network_interface" "this" {
  name                = "${var.name}-nic"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                          = "${var.name}-ipcfg"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Dynamic"
  }

  tags = var.tags
}

resource "azurerm_windows_virtual_machine" "this" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  size                = var.virtual_machine_size
  admin_username      = var.admin_username
  admin_password      = var.admin_password

  network_interface_ids = [azurerm_network_interface.this.id]

  provision_vm_agent     = true
  patch_assessment_mode  = "AutomaticByOS"
  patch_mode             = "AutomaticByOS"
  source_image_id        = var.source_image_id

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  tags = var.tags
}

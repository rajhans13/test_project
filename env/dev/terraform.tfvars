resource_group_name          = "rg-dev-shared"
key_vault_name               = "kv-dev-shared"
key_vault_resource_group     = "rg-dev-shared"
admin_password_secret_name   = "local-admin-password"
admin_username               = "devadmin"
vm_name                      = "ws2025-dev-01"
vm_size                      = "Standard_D4s_v5"
vnet_name                    = "dev-core-vnet"
vnet_address_space           = ["10.20.0.0/16"]
subnet_name                  = "vm"
subnet_address_prefix        = "10.20.1.0/24"
ws2025_image_id              = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-dev-shared/providers/Microsoft.Compute/galleries/shared-gallery/images/ws2025/versions/1.0.0"
tags = {
  environment = "dev"
  workload    = "ws2025-upgrade"
}

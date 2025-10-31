resource_group_name          = "rg-prod-shared"
key_vault_name               = "kv-prod-shared"
key_vault_resource_group     = "rg-prod-shared"
admin_password_secret_name   = "local-admin-password"
admin_username               = "prodadmin"
vm_name                      = "ws2025-prod-01"
vm_size                      = "Standard_D8s_v5"
vnet_name                    = "prod-core-vnet"
vnet_address_space           = ["10.30.0.0/16"]
subnet_name                  = "vm"
subnet_address_prefix        = "10.30.1.0/24"
ws2025_image_id              = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-prod-shared/providers/Microsoft.Compute/galleries/shared-gallery/images/ws2025/versions/1.0.0"
tags = {
  environment = "prod"
  workload    = "ws2025-upgrade"
}

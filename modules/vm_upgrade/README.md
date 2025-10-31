# VM Upgrade Module

Deploys a Windows Server 2025 virtual machine using Compute Gallery images.

<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

| Name | Version |
|------|---------|
| azurerm | ~> 3.102 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [azurerm_network_interface.this](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/network_interface) | resource |
| [azurerm_windows_virtual_machine.this](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/windows_virtual_machine) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| admin_password | Local administrator password retrieved from Key Vault. | `string` | n/a | yes |
| admin_username | Local administrator username. | `string` | n/a | yes |
| location | Azure region for the virtual machine. | `string` | n/a | yes |
| name | Name of the Windows virtual machine. | `string` | n/a | yes |
| resource_group_name | Resource group name for the virtual machine. | `string` | n/a | yes |
| source_image_id | Compute Gallery image identifier for the VM. | `string` | n/a | yes |
| subnet_id | Subnet identifier for the virtual machine's primary NIC. | `string` | n/a | yes |
| tags | Tags to apply to the VM resources. | `map(string)` | `{}` | no |
| virtual_machine_size | Azure VM size. | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| network_interface_id | Identifier of the network interface created for the VM. |
| virtual_machine_id | Identifier of the Azure Windows virtual machine. |
<!-- END_TF_DOCS -->

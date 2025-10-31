# Network Module

Reusable module that provisions a virtual network and subnet for Windows virtual machines.

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
| [azurerm_subnet.this](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/subnet) | resource |
| [azurerm_virtual_network.this](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/virtual_network) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| location | Azure region for the networking resources. | `string` | n/a | yes |
| resource_group_name | Resource group name for the networking resources. | `string` | n/a | yes |
| subnet_address_prefix | CIDR prefix of the subnet. | `string` | n/a | yes |
| subnet_name | Name of the subnet to create. | `string` | n/a | yes |
| tags | Tags to apply to the networking resources. | `map(string)` | `{}` | no |
| vnet_address_space | Address space for the virtual network. | `list(string)` | n/a | yes |
| vnet_name | Name of the virtual network to create. | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| subnet_id | Identifier of the created subnet. |
| vnet_id | Identifier of the created virtual network. |
<!-- END_TF_DOCS -->

locals {
  subscriptions = {
    dev = {
      display_name = "Development"
      alias        = "Dev"
      billing_scope = "/providers/Microsoft.Billing/billingAccounts/00000000/enrollmentAccounts/00000000"
      workload       = "Production"
      address_space  = ["10.10.0.0/16"]
      subnets = [
        {
          name   = "app"
          prefix = "10.10.1.0/24"
        },
        {
          name   = "data"
          prefix = "10.10.2.0/24"
        }
      ]
    }
    test = {
      display_name = "Test"
      alias        = "Test"
      billing_scope = "/providers/Microsoft.Billing/billingAccounts/00000000/enrollmentAccounts/00000001"
      workload       = "Production"
      address_space  = ["10.20.0.0/16"]
      subnets = [
        {
          name   = "app"
          prefix = "10.20.1.0/24"
        },
        {
          name   = "data"
          prefix = "10.20.2.0/24"
        }
      ]
    }
    prod = {
      display_name = "Production"
      alias        = "Prod"
      billing_scope = "/providers/Microsoft.Billing/billingAccounts/00000000/enrollmentAccounts/00000002"
      workload       = "Production"
      address_space  = ["10.30.0.0/16"]
      subnets = [
        {
          name   = "app"
          prefix = "10.30.1.0/24"
        },
        {
          name   = "data"
          prefix = "10.30.2.0/24"
        }
      ]
    }
    dr = {
      display_name = "Disaster Recovery"
      alias        = "DR"
      billing_scope = "/providers/Microsoft.Billing/billingAccounts/00000000/enrollmentAccounts/00000003"
      workload       = "Production"
      address_space  = ["10.40.0.0/16"]
      subnets = [
        {
          name   = "app"
          prefix = "10.40.1.0/24"
        },
        {
          name   = "data"
          prefix = "10.40.2.0/24"
        }
      ]
    }
  }

  hub_config = {
    name                  = "vnet-hub"
    address_space         = ["10.0.0.0/16"]
    firewall_subnet       = "10.0.255.0/26"
    resource_group_suffix = "network"
  }
}

resource "azurerm_resource_group" "network" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

resource "azurerm_management_group" "environments" {
  for_each                 = local.subscriptions
  display_name             = upper(each.key)
  name                     = "mg-${each.key}"
  parent_management_group_id = var.root_management_group_id
}

resource "azapi_resource" "subscription" {
  for_each  = local.subscriptions
  type      = "Microsoft.Subscription/aliases@2020-09-01"
  name      = lower(each.value.alias)
  parent_id = "/providers/Microsoft.Subscription"

  body = jsonencode({
    properties = {
      displayName = each.value.display_name
      workload    = each.value.workload
      billingScope = each.value.billing_scope
      subscriptionId = null
      tenantId       = var.tenant_id
      additionalProperties = {
        managementGroupId = azurerm_management_group.environments[each.key].id
      }
    }
  })
}

resource "azurerm_management_group_policy_assignment" "baseline" {
  for_each             = var.policy_definition_ids
  name                 = "baseline-${each.key}"
  policy_definition_id = each.value
  management_group_id  = var.root_management_group_id

  enforcement_mode = "Default"
}

resource "azurerm_management_group_policy_assignment" "environment" {
  for_each             = {
    for env_key, env_val in local.subscriptions : env_key => env_val
  }
  name                 = "${each.key}-governance"
  policy_definition_id = var.policy_definition_ids["auditBaseline"]
  management_group_id  = azurerm_management_group.environments[each.key].id

  depends_on = [azurerm_management_group_policy_assignment.baseline]
}

module "hub" {
  source              = "../../common/modules/hub"
  name                = local.hub_config.name
  location            = var.location
  resource_group_name = azurerm_resource_group.network.name
  address_space       = local.hub_config.address_space
  firewall_subnet_prefix = local.hub_config.firewall_subnet
  tags                = var.tags
}

module "spokes" {
  for_each            = local.subscriptions
  source              = "../../common/modules/vnet"
  name                = "vnet-${each.key}-hubspoke"
  location            = var.location
  resource_group_name = azurerm_resource_group.network.name
  address_space       = each.value.address_space
  subnets             = each.value.subnets
  firewall_private_ip = module.hub.firewall_private_ip
  hub_vnet_id         = module.hub.virtual_network_id
  tags                = merge(var.tags, { environment = each.key })
}

output "subscription_aliases" {
  description = "Provisioned subscription alias resource IDs"
  value = {
    for name, alias in azapi_resource.subscription : name => alias.id
  }
}

output "spoke_vnets" {
  description = "Map of spoke VNet IDs by environment"
  value = {
    for name, mod in module.spokes : name => mod.virtual_network_id
  }
}

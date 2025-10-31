locals {
  compute_gallery_images = {
    windows_server_2025 = var.windows_server_2025_image_id
  }
}

output "windows_server_2025_image_id" {
  description = "Compute Gallery image ID for Windows Server 2025."
  value       = local.compute_gallery_images["windows_server_2025"]
}

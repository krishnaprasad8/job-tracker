output "server_ip" {
  description = "Public IPv4. Changes on every rebuild."
  value       = hcloud_server.app.ipv4_address
}

output "app_url" {
  description = "Give cloud-init two or three minutes after apply before this responds."
  value       = "http://${hcloud_server.app.ipv4_address}/docs"
}

output "ssh_command" {
  value = "ssh root@${hcloud_server.app.ipv4_address}"
}

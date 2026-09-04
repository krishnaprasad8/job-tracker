output "server_ip" {
  description = "Reserved IPv4 address. Stable across server rebuilds."
  value       = hcloud_primary_ip.app.ip_address
}

output "ssh_command" {
  description = "Ready to paste."
  value       = "ssh root@${hcloud_primary_ip.app.ip_address}"
}

output "server_status" {
  value = hcloud_server.app.status
}

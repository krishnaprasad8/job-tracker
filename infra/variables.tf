variable "hcloud_token" {
  description = "Hetzner Cloud API token with Read & Write permission."
  type        = string
  sensitive   = true
}

variable "server_name" {
  description = "Name used for the server and as a prefix for related resources."
  type        = string
  default     = "job-tracker"
}

variable "server_type" {
  description = "cx33 = 4 vCPU, 8 GB RAM, 80 GB disk."
  type        = string
  default     = "cx33"
}

variable "location" {
  description = "Hetzner location. nbg1 = Nuremberg, fsn1 = Falkenstein, hel1 = Helsinki."
  type        = string
  default     = "nbg1"
}

variable "image" {
  description = "Base OS image."
  type        = string
  default     = "ubuntu-24.04"
}

variable "ssh_public_key_path" {
  description = "Public half of the key pair used to reach the server."
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "allowed_ssh_ips" {
  description = <<-EOT
    CIDRs permitted to reach SSH. Defaults to the whole internet because a
    home IP usually changes; narrow it to "your.ip.here/32" when you can.
  EOT
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

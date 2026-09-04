resource "hcloud_ssh_key" "me" {
  name       = "${var.server_name}-key"
  public_key = file(pathexpand(var.ssh_public_key_path))
}

# auto_delete = false is the whole point of this resource: the address is
# reserved to the account rather than to a server, so tearing the server down
# between demos keeps the IP and any DNS pointing at it.
resource "hcloud_primary_ip" "app" {
  name        = "${var.server_name}-ipv4"
  type        = "ipv4"
  location    = var.location
  auto_delete = false
}

# Hetzner firewalls deny all inbound traffic that no rule permits, and allow
# all outbound. Only these three ports are reachable from the internet.
resource "hcloud_firewall" "app" {
  name = "${var.server_name}-firewall"

  rule {
    direction   = "in"
    protocol    = "tcp"
    port        = "22"
    source_ips  = var.allowed_ssh_ips
    description = "SSH"
  }

  rule {
    direction   = "in"
    protocol    = "tcp"
    port        = "80"
    source_ips  = ["0.0.0.0/0", "::/0"]
    description = "HTTP"
  }

  rule {
    direction   = "in"
    protocol    = "tcp"
    port        = "443"
    source_ips  = ["0.0.0.0/0", "::/0"]
    description = "HTTPS"
  }
}

resource "hcloud_server" "app" {
  name         = var.server_name
  server_type  = var.server_type
  image        = var.image
  location     = var.location
  ssh_keys     = [hcloud_ssh_key.me.id]
  firewall_ids = [hcloud_firewall.app.id]

  public_net {
    ipv4_enabled = true
    ipv4         = hcloud_primary_ip.app.id
    ipv6_enabled = true
  }

  labels = {
    project = var.server_name
  }
}

resource "hcloud_ssh_key" "me" {
  name       = "${var.server_name}-key"
  public_key = file(pathexpand(var.ssh_public_key_path))
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

  # No reserved Primary IP: the address is created and destroyed with the
  # server, so nothing bills once the server is gone. The trade-off is a new
  # IP on every rebuild, which rules out stable DNS.
  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  # Runs on first boot: installs Docker, starts the app, puts Nginx in front.
  user_data = file("${path.module}/cloud-init.sh")

  labels = {
    project = var.server_name
  }
}

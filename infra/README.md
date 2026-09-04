# Infrastructure

Terraform configuration that provisions the Hetzner Cloud server this project
deploys to, and brings the application up on first boot.

## What it creates

| Resource | Purpose |
| --- | --- |
| `hcloud_ssh_key` | Uploads your public key so you can reach the server |
| `hcloud_firewall` | Denies all inbound except SSH (22), HTTP (80) and HTTPS (443) |
| `hcloud_server` | CX33 — 4 vCPU, 8 GB RAM, 80 GB disk — Ubuntu 24.04, Nuremberg |

The server runs `cloud-init.sh` on first boot, which installs Docker and Nginx,
clones this repository, generates a database password, starts the Compose
stack and configures Nginx to proxy port 80 to the app. No SSH required.

## Prerequisites

- Terraform >= 1.6
- A Hetzner Cloud account with a payment method
- An SSH key pair at `~/.ssh/id_ed25519`

## Setup

Generate an API token: Hetzner Console → your project → **Security** →
**API tokens** → **Generate API token** → **Read & Write**. It is shown once.

```bash
cp terraform.tfvars.example terraform.tfvars
# paste the token into terraform.tfvars
```

`terraform.tfvars` is gitignored and must never be committed. To avoid keeping
the token on disk, export it instead and skip the file:

```bash
export TF_VAR_hcloud_token="your-token"
```

## Usage

```bash
terraform init      # download the Hetzner provider, once
terraform plan      # show what would be created; costs nothing
terraform apply     # create it — billing starts here
```

`apply` finishes in about 40 seconds, but cloud-init needs a further two to
three minutes to install everything. The `app_url` output is not reachable
until that finishes.

Watch the bootstrap if you want to see it happen:

```bash
ssh root@$(terraform output -raw server_ip) 'tail -f /var/log/cloud-init-output.log'
```

## Running on demand

The server bills hourly (~$0.016/h for a CX33), and a *stopped* server still
bills — only deleting it stops the charge. So destroy it when you are not
using it:

```bash
terraform destroy
```

Cost when destroyed is **zero**. Nothing is left behind.

Bringing it back is a single `terraform apply`, and cloud-init rebuilds
everything. Roughly three minutes from nothing to a working API.

### The trade-off

There is deliberately **no reserved Primary IP**, because one would cost
€0.50/month whether or not a server exists. The consequence is that the
**IP address changes on every rebuild**, so a domain name cannot stay pointed
at it and HTTPS via Certbot is impractical. Demos run over `http://<ip>/docs`
using whatever address the current `apply` produced.

Adding `hcloud_primary_ip` with `auto_delete = false` back into `main.tf` would
give a stable address for that €0.50/month, and would then need
`terraform destroy -target=hcloud_server.app` so the teardown left the IP
alone.

### The database does not survive

The Postgres volume is destroyed with the server, so every rebuild starts with
an empty database and a freshly generated password. That is fine for demos;
anything worth keeping needs `pg_dump` before teardown.

## Notes

- **`.terraform.lock.hcl` is committed** deliberately — it pins provider
  versions so the same configuration produces the same result later.
- **State is local.** `terraform.tfstate` is gitignored because it records
  everything created and can contain secrets in plain text. A remote backend
  would be the next improvement.
- **SSH is open to the internet** by default, because home IP addresses
  usually change. Narrow `allowed_ssh_ips` to your own address if it is stable.

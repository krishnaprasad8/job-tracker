# Infrastructure

Terraform configuration provisioning the Hetzner Cloud server this project
deploys to.

## What it creates

| Resource | Purpose |
| --- | --- |
| `hcloud_ssh_key` | Uploads your public key so you can reach the server |
| `hcloud_primary_ip` | A reserved IPv4 address, **not** tied to the server's lifecycle |
| `hcloud_firewall` | Denies all inbound except SSH (22), HTTP (80) and HTTPS (443) |
| `hcloud_server` | CX33 — 4 vCPU, 8 GB RAM, 80 GB disk — Ubuntu 24.04, Nuremberg |

## Prerequisites

- Terraform >= 1.6
- A Hetzner Cloud account with a payment method
- An SSH key pair at `~/.ssh/id_ed25519`

## Setup

Generate an API token: Hetzner Console → your project → **Security** →
**API tokens** → **Generate API token** → **Read & Write**. It is shown once.

```bash
cp terraform.tfvars.example terraform.tfvars
# then edit terraform.tfvars and paste the token in
```

`terraform.tfvars` is gitignored and must never be committed. If you prefer not
to keep the token on disk at all, export it instead and skip the file:

```bash
export TF_VAR_hcloud_token="your-token"
```

## Usage

```bash
terraform init      # download the Hetzner provider, once
terraform plan      # show what would be created; costs nothing
terraform apply     # create it — billing starts here
```

`apply` prints the server's IP and a ready-to-paste SSH command.

## Running on demand

The server bills hourly (~$0.016/h for a CX33), and a *stopped* server still
bills — only deleting it stops the charge. So for a project that only needs to
be live occasionally, destroy the server between uses:

```bash
terraform destroy -target=hcloud_server.app   # server gone, IP kept
terraform apply                               # back again, same IP
```

The `-target` matters. A plain `terraform destroy` also removes the reserved
IP, and the next `apply` would hand you a different address — breaking any DNS
pointing at it. Use the untargeted form only when you are finished with the
project entirely.

Steady-state cost with the server destroyed is the reserved IP alone, about
**€0.50/month**. A three-hour demo adds roughly five cents.

## Notes

- **The Primary IP and the server share one `location` variable**, so they are
  always created in the same place. They have to be, for the IP to attach.
- **`.terraform.lock.hcl` is committed** deliberately. It pins provider
  versions so the same configuration produces the same result later.
- **State is local.** `terraform.tfstate` is gitignored because it records
  everything that was created and can contain secrets in plain text. A remote
  backend would be the next improvement.
- **SSH is open to the internet** by default, because home IPs usually change.
  Narrow `allowed_ssh_ips` to your own address if it is stable.

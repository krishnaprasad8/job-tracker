#!/bin/bash
# Runs once on first boot, as root, via cloud-init.
# Output goes to /var/log/cloud-init-output.log on the server.
set -euxo pipefail

REPO="https://github.com/krishnaprasad8/job-tracker.git"
APP_DIR="/opt/job-tracker"

# Ubuntu runs unattended-upgrades at boot, which holds the apt lock. Wait it
# out rather than racing it and failing.
wait_for_apt() {
  while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do sleep 3; done
}

wait_for_apt
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git nginx

# Docker's official install script; brings the compose plugin with it.
curl -fsSL https://get.docker.com | sh

git clone --depth 1 "$REPO" "$APP_DIR"
cd "$APP_DIR"

# Generate a database password on the box. It never leaves the server and is
# regenerated on every rebuild, since the volume does not survive either.
cp .env.example .env
DB_PASSWORD="$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 32)"
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${DB_PASSWORD}|" .env

docker compose up -d

cat > /etc/nginx/sites-available/default <<'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

nginx -t
systemctl reload nginx

# Don't report success until the app actually answers.
for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "cloud-init: app is healthy"
    exit 0
  fi
  sleep 5
done

echo "cloud-init: app did not become healthy in time" >&2
exit 1

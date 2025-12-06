#!/bin/bash
set -e

# Minimal EC2 userdata to install Docker and Docker Compose
# Keeps things idempotent and suitable for Ubuntu-based AMIs

export DEBIAN_FRONTEND=noninteractive

# Update packages and install required packages
apt-get update -y
apt-get install -y --no-install-recommends docker.io docker-compose curl python3

# Start and enable Docker
systemctl enable --now docker

# Add 'ubuntu' user to docker group if it exists (UID 1000 commonly)
if id -u ubuntu >/dev/null 2>&1; then
  usermod -aG docker ubuntu || true
  chown -R 1000:1000 /home/ubuntu || true
fi

# Wait for Docker socket to become available
for i in 1 2 3 4 5; do
  if [ -S /var/run/docker.sock ]; then
    break
  fi
  echo "Waiting for Docker socket... ($i/5)"
  sleep 2
done

# Create useful directories for later mounts (non-sensitive defaults)
mkdir -p /home/ubuntu/SSHKEYALTERNATE /home/ubuntu/certs
chown -R 1000:1000 /home/ubuntu/SSHKEYALTERNATE /home/ubuntu/certs || true
chmod 755 /home/ubuntu/SSHKEYALTERNATE || true
chmod 700 /home/ubuntu/certs || true

# Print short status for debugging
echo "--- Docker status ---"
systemctl status docker --no-pager || true

echo "--- Docker info ---"
docker --version || true

echo "Userdata script completed: Docker and docker-compose installed."

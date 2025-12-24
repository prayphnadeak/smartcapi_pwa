#!/bin/bash

# deploy_backend.sh (CentOS Version)
# Deploys the SmartCAPI Backend to /var/www/smartcapi/backend

set -e

# FAILSAFE: Install dependencies here since setup_remote.sh might be skipped
echo ">>> [BACKEND] Ensuring Dependencies..."
dnf config-manager --set-enabled crb || true
dnf install -y epel-release dnf-plugins-core
dnf install -y --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-$(rpm -E %rhel).noarch.rpm || true
dnf install -y --nogpgcheck https://mirrors.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-$(rpm -E %rhel).noarch.rpm || true
dnf install -y pkgconf pkgconf-pkg-config ffmpeg ffmpeg-devel python3-devel gcc gcc-c++ || true

# FAILSAFE: Ensure Redis is installed and running (Critical for Real-time)
echo ">>> [BACKEND] Ensuring Redis is installed..."
dnf install -y redis || true
systemctl enable --now redis || true

# Stop services first to release file locks
echo ">>> Stopping services before deployment..."
systemctl stop smartcapi-api smartcapi-workers || true

TARGET_DIR="/var/www/smartcapi/backend"
USER="root"

echo ">>> Setting up Backend in $TARGET_DIR..."

if [ ! -d "$TARGET_DIR" ]; then
    mkdir -p "$TARGET_DIR"
fi

# We are in /root/deploy_temp
if [ -d "smartcapi-backend" ]; then
    echo ">>> Copying files from smartcapi-backend to $TARGET_DIR..."
    
    # CRITICAL: Clean target directory first to remove old/ghost files
    # But preserve .venv and database which are heavy/stateful
    find "$TARGET_DIR" -mindepth 1 -maxdepth 1 ! -name ".venv" ! -name "smartcapi.db" ! -name ".env" -exec rm -rf {} +
    
    cp -r smartcapi-backend/. "$TARGET_DIR"
else
    echo "ERROR: smartcapi-backend directory not found in $(pwd)"
    exit 1
fi

cd "$TARGET_DIR"

echo ">>> Setting up Python Environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
echo ">>> Installing Requirements..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Verify Dependencies
echo ">>> Verifying Python Dependencies..."
python -c "import fastapi, uvicorn, sqlalchemy, celery, redis; print('Dependencies OK')" || {
    echo "ERROR: Critical dependencies missing or broken!"
    exit 1
}

echo ">>> Configuring .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    # Update DB URL for SQLite
    sed -i 's|DATABASE_URL=.*|DATABASE_URL=sqlite:////var/www/smartcapi/backend/smartcapi.db|' .env
fi

# FORCE UPDATE API KEY (Fix for 401 Error)
# The .env file on VPS has the placeholder, so we must overwrite it with the real key
sed -i 's|OPENAI_API_KEY=.*|OPENAI_API_KEY=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|' .env

echo ">>> Setting Permissions for SQLite..."
# Explicitly set permissions for the directory and database
# Even though we run as root, ensuring generic unix perms is good practice
chmod 755 "$TARGET_DIR"
touch smartcapi.db
chmod 664 smartcapi.db
chown $USER:$USER smartcapi.db
chown $USER:$USER .

# Try to set SELinux context, but don't fail if we can't
# Some VPS have SELinux disabled completely which causes chcon to error
echo ">>> Attempting SELinux Context Update (ignoring failures)..."
chcon -t httpd_sys_rw_content_t smartcapi.db 2>/dev/null || true
chcon -t httpd_sys_rw_content_t . 2>/dev/null || true

# FIX: Ensure proper permissions for Nginx user
echo ">>> Setting Permissions for Nginx User..."
chown -R nginx:nginx "$TARGET_DIR"
# Allow nginx to write to the db file specifically if SELinux is permissive, but standard is good.
chmod -R 755 "$TARGET_DIR"

echo ">>> Creating Admin User..."
python tests/create_admin.py || echo "WARNING: Admin creation failed, but continuing..."

echo ">>> Creating Systemd Services..."

# API Service
cat <<EOF > /etc/systemd/system/smartcapi-api.service
[Unit]
Description=SmartCAPI FastAPI Backend
After=network.target mysql.service redis.service

[Service]
Type=simple
User=nginx
WorkingDirectory=$TARGET_DIR
Environment="PATH=$TARGET_DIR/.venv/bin"
ExecStart=$TARGET_DIR/.venv/bin/python run_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Worker Service
cat <<EOF > /etc/systemd/system/smartcapi-workers.service
[Unit]
Description=SmartCAPI Celery Workers
After=network.target redis.service

[Service]
Type=simple
User=nginx
WorkingDirectory=$TARGET_DIR
Environment="PATH=$TARGET_DIR/.venv/bin"
ExecStart=$TARGET_DIR/.venv/bin/python run_workers.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ">>> Reloading Systemd and Starting Services..."
systemctl daemon-reload
systemctl enable smartcapi-api smartcapi-workers
systemctl restart smartcapi-api smartcapi-workers

# Check status
systemctl status smartcapi-api --no-pager || true
systemctl status smartcapi-workers --no-pager || true

echo ">>> Backend Deployment Complete."

echo ">>> Waiting 5s for services to stabilize..."
sleep 5

echo "=============== BACKEND SERVICE STATUS ==============="
systemctl status smartcapi-api --no-pager || true
echo "=============== BACKEND LOGS (Last 50 lines) ==============="
journalctl -u smartcapi-api -n 50 --no-pager || true
echo "======================================================"
echo ">>> Backend Deployment Complete."

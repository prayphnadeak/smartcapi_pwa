#!/bin/bash

# deploy_frontend.sh (CentOS Version)
# Deploys the SmartCAPI Frontend to /var/www/smartcapi/frontend

set -e
echo ">>> [VERSION 1.5] Frontend Deploy - Pre-Restart Fix <<<"

# FAILSAFE: Install Node.js here to be sure
echo ">>> [FRONTEND] Ensuring Node.js..."
dnf module reset -y nodejs || true
dnf module enable -y nodejs:20 || true
dnf install -y nodejs npm

TARGET_DIR="/var/www/smartcapi/frontend"

echo ">>> Setting up Frontend in $TARGET_DIR..."

if [ ! -d "$TARGET_DIR" ]; then
    mkdir -p "$TARGET_DIR"
fi

# We are in /root/deploy_temp
if [ -d "smartcapi-client" ]; then
    echo ">>> Copying files from smartcapi-client to $TARGET_DIR..."
    cp -r smartcapi-client/. "$TARGET_DIR"
else
    echo "ERROR: smartcapi-client directory not found in $(pwd)"
    exit 1
fi

cd "$TARGET_DIR"

echo ">>> Installing dependencies and Building..."
npm install
npm run build


# FIX: Overwrite default nginx.conf to remove default server block conflict
echo ">>> Replacing default Nginx Config..."
cat <<EOF > /etc/nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                      '\$status \$body_bytes_sent "\$http_referer" '
                      '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Load modular configuration files from the /etc/nginx/conf.d directory.
    # See http://nginx.org/en/docs/ngx_core_module.html#include
    # for more information.
    include /etc/nginx/conf.d/*.conf;
}
EOF

# Ensure Firewall is open
echo ">>> Opening Firewall Port 80..."
firewall-cmd --permanent --add-service=http || true
firewall-cmd --reload || true

# REMOVE DEFAULT CONF if exists (Common culprit)
echo ">>> Nuking default config..."
rm -rf /etc/nginx/conf.d/default.conf
rm -rf /etc/nginx/default.d/*.conf || true

# Hide default index file to prove source
mv /usr/share/nginx/html/index.html /usr/share/nginx/html/index.html.bak || true

# Disable SELinux temporarily to rule out context issues
echo ">>> Setting SELinux to Permissive..."
setenforce 0 || true

echo ">>> Configuring Nginx Server Block..."
# ... (smartcapi.conf creation is here, skipped in replacement) ...

# Ensure Nginx loads conf.d (Default on CentOS/RHEL)

# (Premature block removed)
# CentOS uses conf.d, not sites-available/enabled by default usually.
# Using conf.d is safer.
DOMAIN="103.151.140.205.nip.io"
SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
    echo ">>> [NGINX] SSL Certificates Setup Found! Configuring HTTPS for $DOMAIN..."
    cat <<EOF > /etc/nginx/conf.d/smartcapi.conf
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl default_server;
    server_name $DOMAIN;

    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    root $TARGET_DIR/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Prevent caching of index.html
    location = /index.html {
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    # Prevent caching of service worker and manifest
    location ~* (service-worker\.js|manifest\.json)$ {
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        expires off;
    }

    # Explicitly return 404 for missing assets (CSS/JS/Images)
    # This prevents them from falling back to /index.html and breaking styles
    location ~ ^/assets/ {
        try_files \$uri =404;
        expires 1y;
        add_header Cache-Control "public, no-transform";
    }

    location /storage {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        client_max_body_size 50M;
    }
}
EOF
else
    echo ">>> [NGINX] No SSL Certificates found at $SSL_CERT. Configuring HTTP only."
    cat <<EOF > /etc/nginx/conf.d/smartcapi.conf
server {
    listen 80 default_server;
    server_name _;

    root $TARGET_DIR/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Prevent caching of index.html
    location = /index.html {
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    # Prevent caching of service worker and manifest
    location ~* (service-worker\.js|manifest\.json)$ {
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        expires off;
    }

    # Explicitly return 404 for missing assets
    location ~ ^/assets/ {
        try_files \$uri =404;
        expires 1y;
        add_header Cache-Control "public, no-transform";
    }

    location /storage {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        client_max_body_size 50M;
    }
}
EOF
fi

# Fix Permissions (Critical for 403 Forbidden)
# Ensure parent dirs are traversable
chmod 755 /var
chmod 755 /var/www
# Recursive fix for app dir (Strictly set owner and perms)
chown -R nginx:nginx /var/www/smartcapi
chmod -R 755 /var/www/smartcapi

echo ">>> Restarting Nginx (Applying Config & Permissions)..."
# Debug: Link the config if not present (Safety check)
ln -sf /etc/nginx/conf.d/smartcapi.conf /etc/nginx/sites-enabled/smartcapi.conf 2>/dev/null || true

nginx -t
systemctl restart nginx

echo ">>> Setting SELinux Contexts (Backgrounding to avoid blocking)..."
# Crucial for Nginx to read the files (SELinux)
# We use || true and suppress stderr to prevent script failure/spam
chcon -R -t httpd_sys_content_t $TARGET_DIR/dist 2>/dev/null || true

echo ">>> Frontend Deployment Complete."

echo "============================================="
echo ">>> DIAGNOSTICS (If 403 Persists) <<<"
echo "1. Process Owner:"
ps aux | grep nginx | grep -v grep
echo "2. Directory Permissions:"
ls -ld /var /var/www /var/www/smartcapi /var/www/smartcapi/frontend /var/www/smartcapi/frontend/dist
echo "3. Nginx Error Log (Last 20 lines):"
tail -n 20 /var/log/nginx/error.log
echo "============================================="

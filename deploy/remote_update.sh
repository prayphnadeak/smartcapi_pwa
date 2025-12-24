#!/bin/bash
set -e

echo ">>> [SERVER] Menerima Update..."

# 1. Install utils
dnf install -y unzip dos2unix > /dev/null

# 2. Unzip
rm -rf /root/deploy_temp
mkdir -p /root/deploy_temp
unzip -o /root/smartcapi_deploy.zip -d /root/deploy_temp > /dev/null
echo ">>> [SERVER] Unzip selesai."

# 3. Fix Line Endings
find /root/deploy_temp/deploy -name "*.sh" -exec dos2unix {} \;
chmod +x /root/deploy_temp/deploy/*.sh

# 4. Update Backend
echo ">>> [SERVER] Updating Backend..."
cd /root/deploy_temp
./deploy/deploy_backend.sh

# 5. Update Frontend
echo ">>> [SERVER] Updating Frontend..."
./deploy/deploy_frontend.sh

echo "=================================================="
echo "✅ UPDATE SELESAI!"
echo "Silakan cek: https://103.151.140.205.nip.io"
echo "=================================================="

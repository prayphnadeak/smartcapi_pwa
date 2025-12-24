#!/bin/bash

# setup_remote.sh (CentOS Stream 9 Version - Hardened)
# Sets up the VPS environment for SmartCAPI

set -e

echo ">>> Installing DNF Plugins..."
dnf install -y dnf-plugins-core

echo ">>> Enables CodeReady Builder (CRB) for devel packages..."
dnf config-manager --set-enabled crb || echo "Warning: Could not enable CRB via config-manager, trying subscription-manager or skipping..."
dnf update -y

echo ">>> Installing Repositories (EPEL, RPMFusion)..."
dnf install -y epel-release
dnf install -y --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-$(rpm -E %rhel).noarch.rpm
dnf install -y --nogpgcheck https://mirrors.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-$(rpm -E %rhel).noarch.rpm

echo ">>> Installing System Utilities & pkg-config..."
dnf install -y git curl wget tar unzip nano pkgconf pkgconf-pkg-config
dnf install -y gcc gcc-c++ make cmake

echo ">>> Installing Python 3 and Dev tools..."
dnf install -y python3 python3-devel python3-pip

echo ">>> Installing Redis..."
dnf install -y redis
systemctl enable --now redis

echo ">>> Installing Nginx..."
# REMOVE CONFLICTING APACHE (httpd)
echo ">>> Removing conflicting httpd (Apache)..."
systemctl stop httpd || true
systemctl disable httpd || true
dnf remove -y httpd || true

dnf install -y nginx
systemctl enable --now nginx

echo ">>> Installing FFmpeg Development Libraries..."
# Try multiple patterns for robustness
dnf install -y ffmpeg ffmpeg-devel || echo "Warning: ffmpeg-devel install returned error, checking if installed..."

echo ">>> Verifying FFmpeg headers..."
if pkg-config --exists libavformat; then
    echo ">>> libavformat found via pkg-config."
else
    echo ">>> ERROR: libavformat NOT found. 'av' package will fail to build."
    # Fallback attempt
    echo ">>> Attempting to continue without explicit devel packages..."
fi

echo ">>> Checking for Swap..."
if [ ! -f /swapfile ]; then
    echo ">>> Creating 4GB Swap File..."
    dd if=/dev/zero of=/swapfile bs=128M count=32
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
else
    echo ">>> Swap already exists."
fi

echo ">>> Installing Node.js (v20)..."
dnf module reset -y nodejs
dnf module enable -y nodejs:20
dnf install -y nodejs npm

echo ">>> Verifying Node.js..."
node -v
npm -v

echo ">>> Configuring SELinux..."
setsebool -P httpd_can_network_connect 1

echo ">>> Setup complete."

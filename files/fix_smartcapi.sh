#!/bin/bash
# fix_smartcapi.sh - Script khusus untuk SmartCAPI PWA deployment
# Disesuaikan dengan arsitektur: FastAPI + SQLite + Celery + Redis

set -e

echo "============================================="
echo "SmartCAPI PWA - Backend Fix Script"
echo "Struktur: FastAPI + SQLite + Celery + Redis"
echo "============================================="

BACKEND_DIR="/var/www/smartcapi/backend"
VENV_PATH="$BACKEND_DIR/.venv"

# 1. Cek directory backend
if [ ! -d "$BACKEND_DIR" ]; then
    echo "ERROR: Backend directory tidak ditemukan di $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR"

# 2. Cek virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo ">>> Membuat Python Virtual Environment..."
    python3 -m venv "$VENV_PATH"
fi

echo ">>> Aktivasi Virtual Environment..."
source "$VENV_PATH/bin/activate"

# 3. Upgrade pip dan install dependencies
echo ">>> Updating pip..."
pip install --upgrade pip --quiet

echo ">>> Installing Python Dependencies..."
pip install -r requirements.txt --quiet

# 4. Cek dan setup .env file
echo ">>> Checking .env configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo ">>> Copying .env.example to .env..."
        cp .env.example .env
    else
        echo ">>> Creating .env file..."
        cat > .env << 'ENVEOF'
# Database Configuration (SQLite)
DATABASE_URL=sqlite:///./smartcapi.db

# JWT Configuration
SECRET_KEY=smartcapi-secret-key-change-in-production-2024
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Server Configuration
HOST=0.0.0.0
PORT=8000

# File Storage
UPLOAD_DIR=uploads
AUDIO_DIR=audio_files
MODEL_DIR=models
ENVEOF
    fi
    echo "⚠️  PENTING: Edit .env dan masukkan OPENAI_API_KEY Anda!"
fi

# 5. Cek apakah .env sudah dikonfigurasi dengan benar
if grep -q "your-openai-api-key-here" .env; then
    echo "⚠️  WARNING: OPENAI_API_KEY belum dikonfigurasi di .env"
    echo "   Edit file: $BACKEND_DIR/.env"
fi

# 6. Setup direktori untuk uploads, audio, models
echo ">>> Setting up directories..."
mkdir -p uploads audio_files models
chown -R nginx:nginx uploads audio_files models
chmod -R 775 uploads audio_files models

# 7. Setup SQLite database permissions
if [ -f "smartcapi.db" ]; then
    echo ">>> SQLite database ditemukan"
    chown nginx:nginx smartcapi.db
    chmod 664 smartcapi.db
else
    echo ">>> SQLite database akan dibuat saat aplikasi pertama kali dijalankan"
fi

# 8. Cek Redis
echo ">>> Checking Redis service..."
if ! systemctl is-active --quiet redis; then
    echo ">>> Starting Redis..."
    systemctl start redis
    systemctl enable redis
else
    echo "✓ Redis sudah berjalan"
fi

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis connection OK"
else
    echo "✗ Redis connection failed"
    systemctl status redis
fi

# 9. Buat systemd service untuk FastAPI Backend
echo ">>> Creating systemd service for FastAPI Backend..."
cat > /etc/systemd/system/smartcapi-api.service << 'EOF'
[Unit]
Description=SmartCAPI FastAPI Backend (run_server.py)
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=nginx
Group=nginx
WorkingDirectory=/var/www/smartcapi/backend
Environment="PATH=/var/www/smartcapi/backend/.venv/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/var/www/smartcapi/backend/.venv/bin/python run_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# SQLite needs write access
ReadWritePaths=/var/www/smartcapi/backend

[Install]
WantedBy=multi-user.target
EOF

# 10. Buat systemd service untuk Celery Workers
echo ">>> Creating systemd service for Celery Workers..."
cat > /etc/systemd/system/smartcapi-workers.service << 'EOF'
[Unit]
Description=SmartCAPI Celery Workers (run_workers.py)
After=network.target redis.service smartcapi-api.service
Wants=redis.service

[Service]
Type=simple
User=nginx
Group=nginx
WorkingDirectory=/var/www/smartcapi/backend
Environment="PATH=/var/www/smartcapi/backend/.venv/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/var/www/smartcapi/backend/.venv/bin/python run_workers.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# SQLite needs write access
ReadWritePaths=/var/www/smartcapi/backend

[Install]
WantedBy=multi-user.target
EOF

# 11. Set ownership dan permissions untuk seluruh backend
echo ">>> Setting ownership and permissions..."
chown -R nginx:nginx "$BACKEND_DIR"
chmod -R 755 "$BACKEND_DIR"

# Pastikan .venv executable
chmod +x "$VENV_PATH/bin/python"
chmod +x "$VENV_PATH/bin/pip"

# 12. Reload systemd
echo ">>> Reloading systemd daemon..."
systemctl daemon-reload

# 13. Stop services yang mungkin sedang berjalan
echo ">>> Stopping existing services..."
systemctl stop smartcapi-api smartcapi-workers 2>/dev/null || true

# Kill proses Python yang mungkin masih jalan
pkill -f "python.*run_server.py" 2>/dev/null || true
pkill -f "python.*run_workers.py" 2>/dev/null || true

sleep 2

# 14. Start services
echo ""
echo "============================================="
echo "STARTING SERVICES"
echo "============================================="

echo ">>> Starting SmartCAPI API (FastAPI)..."
systemctl start smartcapi-api
systemctl enable smartcapi-api

sleep 3

echo ">>> Starting SmartCAPI Workers (Celery)..."
systemctl start smartcapi-workers
systemctl enable smartcapi-workers

sleep 3

# 15. Check status
echo ""
echo "============================================="
echo "SERVICE STATUS"
echo "============================================="

echo ""
echo "=== SmartCAPI API Service ==="
if systemctl is-active --quiet smartcapi-api; then
    echo "✓ API Service: RUNNING"
    systemctl status smartcapi-api --no-pager -l | head -20
else
    echo "✗ API Service: FAILED"
    systemctl status smartcapi-api --no-pager -l | tail -20
fi

echo ""
echo "=== SmartCAPI Workers Service ==="
if systemctl is-active --quiet smartcapi-workers; then
    echo "✓ Workers Service: RUNNING"
    systemctl status smartcapi-workers --no-pager -l | head -20
else
    echo "✗ Workers Service: FAILED"
    systemctl status smartcapi-workers --no-pager -l | tail -20
fi

# 16. Test API endpoint
echo ""
echo "============================================="
echo "API CONNECTIVITY TEST"
echo "============================================="
sleep 2

# Test root endpoint
if curl -f -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
    echo "✓ API responding at http://127.0.0.1:8000/"
else
    echo "✗ API not responding at http://127.0.0.1:8000/"
fi

# Test docs endpoint
if curl -f -s http://127.0.0.1:8000/docs > /dev/null 2>&1; then
    echo "✓ API Docs available at http://127.0.0.1:8000/docs"
else
    echo "✗ API Docs not available"
fi

# Test health endpoint (if exists)
if curl -f -s http://127.0.0.1:8000/api/v1/health > /dev/null 2>&1; then
    echo "✓ Health endpoint OK"
fi

# 17. Check ports
echo ""
echo "============================================="
echo "PORT STATUS"
echo "============================================="
netstat -tulpn 2>/dev/null | grep -E '(8000|6379)' || echo "⚠️  Warning: Expected ports not found"

# 18. Database check
echo ""
echo "============================================="
echo "DATABASE STATUS"
echo "============================================="
if [ -f "$BACKEND_DIR/smartcapi.db" ]; then
    echo "✓ SQLite Database: EXISTS"
    ls -lh "$BACKEND_DIR/smartcapi.db"
    
    # Cek jumlah user di database
    USER_COUNT=$(sqlite3 "$BACKEND_DIR/smartcapi.db" "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
    echo "  Total users in database: $USER_COUNT"
    
    if [ "$USER_COUNT" = "0" ]; then
        echo "  ⚠️  No users found. You may need to create admin user."
    fi
else
    echo "⚠️  SQLite Database: NOT FOUND (will be created on first run)"
fi

# 19. Final summary
echo ""
echo "============================================="
echo "SETUP COMPLETE!"
echo "============================================="
echo ""

if systemctl is-active --quiet smartcapi-api && systemctl is-active --quiet smartcapi-workers; then
    echo "✓ All services are running successfully!"
    echo ""
    echo "🎉 SmartCAPI Backend is ready!"
    echo ""
    echo "Access the application at:"
    echo "  → http://103.151.140.205"
    echo ""
    echo "Login credentials (default):"
    echo "  Username: admincapi"
    echo "  Password: supercapi"
    echo ""
    echo "API Documentation:"
    echo "  → http://103.151.140.205/docs"
    echo ""
else
    echo "⚠️  Some services failed to start"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs:"
    echo "     journalctl -u smartcapi-api -n 50"
    echo "     journalctl -u smartcapi-workers -n 50"
    echo ""
    echo "  2. Verify .env configuration:"
    echo "     cat $BACKEND_DIR/.env"
    echo ""
    echo "  3. Check if port 8000 is in use:"
    echo "     lsof -i :8000"
fi

echo "============================================="

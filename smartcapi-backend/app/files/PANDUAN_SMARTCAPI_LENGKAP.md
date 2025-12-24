# PANDUAN LENGKAP - SmartCAPI PWA Deployment & Troubleshooting

## 📋 Arsitektur SmartCAPI

**Frontend:**
- Vue.js 3 (Composition API)
- Vite Build Tool
- Pinia State Management
- IndexedDB (Offline Storage)

**Backend:**
- FastAPI (Python)
- SQLite Database (SQLAlchemy ORM)
- Celery + Redis (Background Jobs)
- OpenAI Whisper (Transcription)
- OpenAI GPT-4o-mini (Extraction)

**Infrastructure:**
- Nginx (Reverse Proxy)
- systemd (Service Management)
- CentOS Stream 9

---

## 🔧 QUICK FIX - Gunakan Script Otomatis

### Cara Paling Mudah (RECOMMENDED):

1. **Download 3 file:**
   - `fix_smartcapi.sh`
   - `fix_smartcapi.ps1`
   - `verify_and_create_admin.py`

2. **Jalankan PowerShell script:**
   ```powershell
   .\fix_smartcapi.ps1
   ```

3. **Login credentials:**
   - Username: `admincapi`
   - Password: `supercapi`
   - Role: `admin`

---

## 🔍 MASALAH & SOLUSI BERDASARKAN LOG ANDA

### Masalah Teridentifikasi:

1. ✗ **Backend API tidak running di port 8000**
   - Error: `Connection refused to http://127.0.0.1:8000`
   
2. ✗ **Service systemd belum dibuat/configured**
   - Script deployment tidak membuat service untuk backend

3. ✗ **Script mencoba start MariaDB**
   - Padahal menggunakan SQLite

---

## 🛠️ MANUAL TROUBLESHOOTING

### Langkah 1: Verify Services

SSH ke server:
```bash
ssh root@103.151.140.205
```

**Cek status services:**
```bash
# Backend API
systemctl status smartcapi-api

# Celery Workers
systemctl status smartcapi-workers

# Redis (required)
systemctl status redis

# Nginx (frontend)
systemctl status nginx
```

### Langkah 2: Verify Backend Files

```bash
cd /var/www/smartcapi/backend

# Cek struktur
ls -la

# Expected files:
# - run_server.py      (FastAPI launcher)
# - run_workers.py     (Celery workers launcher)
# - smartcapi.db       (SQLite database)
# - .env               (Configuration)
# - .venv/             (Virtual environment)
# - app/               (Application code)
```

### Langkah 3: Check Configuration

```bash
# Verify .env file
cat /var/www/smartcapi/backend/.env
```

**Required configuration:**
```env
DATABASE_URL=sqlite:///./smartcapi.db
SECRET_KEY=smartcapi-secret-key-change-in-production-2024
OPENAI_API_KEY=Your Own Open AI API Key
REDIS_URL=redis://localhost:6379/0
HOST=0.0.0.0
PORT=8000
```

### Langkah 4: Manual Start (for debugging)

```bash
cd /var/www/smartcapi/backend
source .venv/bin/activate

# Test import
python -c "from app.main import app; print('✓ Import OK')"

# Start server manually (untuk lihat error)
python run_server.py
```

**Jika ada error:**
- **ModuleNotFoundError**: `pip install -r requirements.txt`
- **Permission denied**: `chmod 664 smartcapi.db`
- **Redis connection error**: `systemctl start redis`
- **Port already in use**: `lsof -i :8000` → kill process

### Langkah 5: Create/Verify Admin User

```bash
cd /var/www/smartcapi/backend
source .venv/bin/activate

# Upload verify_and_create_admin.py ke server
# Lalu jalankan:
python verify_and_create_admin.py
```

Atau gunakan script bawaan (jika ada):
```bash
python tests/create_admin.py
```

### Langkah 6: Verify Database

```bash
cd /var/www/smartcapi/backend

# Cek database exists
ls -lh smartcapi.db

# Query users
sqlite3 smartcapi.db "SELECT username, role, email FROM users;"

# Check admin user
sqlite3 smartcapi.db "SELECT * FROM users WHERE username='admincapi';"
```

---

## 📊 DIAGNOSTICS COMMANDS

### Check All Services:
```bash
systemctl status smartcapi-api smartcapi-workers redis nginx --no-pager
```

### Check Ports:
```bash
netstat -tulpn | grep -E '(8000|6379|80)'

# Expected:
# - Port 8000: Python (FastAPI)
# - Port 6379: Redis
# - Port 80: Nginx
```

### Check Processes:
```bash
ps aux | grep -E '(python|redis|nginx)' | grep -v grep
```

### Check Logs:
```bash
# API logs
journalctl -u smartcapi-api -n 50 --no-pager

# Worker logs
journalctl -u smartcapi-workers -n 50 --no-pager

# Nginx logs
tail -f /var/log/nginx/error.log

# Real-time monitoring
journalctl -u smartcapi-api -f
```

---

## 🔧 COMMON ERRORS & SOLUTIONS

### Error: "Connection refused to port 8000"

**Cause:** Backend tidak jalan

**Solution:**
```bash
# Start service
systemctl start smartcapi-api

# Or manual start for debugging
cd /var/www/smartcapi/backend
source .venv/bin/activate
python run_server.py
```

### Error: "ModuleNotFoundError: No module named 'app'"

**Cause:** Dependencies tidak terinstall atau PYTHONPATH salah

**Solution:**
```bash
cd /var/www/smartcapi/backend
source .venv/bin/activate
pip install -r requirements.txt
```

### Error: "unable to open database file"

**Cause:** SQLite permission issue

**Solution:**
```bash
cd /var/www/smartcapi/backend
chown nginx:nginx smartcapi.db
chmod 664 smartcapi.db
chmod 775 .  # Directory juga harus writable
```

### Error: "Redis connection refused"

**Cause:** Redis tidak jalan

**Solution:**
```bash
systemctl start redis
systemctl enable redis
redis-cli ping  # Should return PONG
```

### Error: "Port 8000 already in use"

**Cause:** Ada proses lain di port 8000

**Solution:**
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>

# Or kill all Python processes (careful!)
pkill -f "python.*run_server.py"
```

### Error: "Login failed" di frontend

**Possible causes:**

1. **Backend tidak jalan:**
   ```bash
   curl http://127.0.0.1:8000/docs
   ```

2. **Admin user belum ada:**
   ```bash
   python verify_and_create_admin.py
   ```

3. **Password salah:**
   - Default: `admincapi` / `supercapi`

4. **Nginx proxy error:**
   ```bash
   cat /etc/nginx/nginx.conf | grep -A 10 "location /api"
   systemctl restart nginx
   ```

---

## 🎯 DEPLOYMENT CHECKLIST

Sebelum declare "deployment sukses", verify:

- [ ] **Redis running**: `systemctl status redis`
- [ ] **Backend API running**: `systemctl status smartcapi-api`
- [ ] **Workers running**: `systemctl status smartcapi-workers`
- [ ] **Port 8000 listening**: `netstat -tulpn | grep 8000`
- [ ] **API responding**: `curl http://127.0.0.1:8000/docs`
- [ ] **Database exists**: `ls -lh smartcapi.db`
- [ ] **Admin user exists**: `sqlite3 smartcapi.db "SELECT * FROM users WHERE role='admin';"`
- [ ] **Nginx running**: `systemctl status nginx`
- [ ] **Frontend accessible**: Visit http://103.151.140.205
- [ ] **Login works**: Try login dengan `admincapi` / `supercapi`

---

## 🚀 PRODUCTION RECOMMENDATIONS

### 1. Security
```bash
# Generate secure SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env dengan key baru
nano /var/www/smartcapi/backend/.env
```

### 2. Monitoring
```bash
# Setup log rotation
cat > /etc/logrotate.d/smartcapi << 'EOF'
/var/log/smartcapi/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

### 3. Backup Database
```bash
# Backup SQLite
cp /var/www/smartcapi/backend/smartcapi.db \
   /var/www/smartcapi/backend/backups/smartcapi_$(date +%Y%m%d).db

# Setup cron untuk auto backup
crontab -e
# Add: 0 2 * * * cp /var/www/smartcapi/backend/smartcapi.db /var/www/smartcapi/backend/backups/smartcapi_$(date +\%Y\%m\%d).db
```

### 4. Performance Tuning
```bash
# Optimize SQLite
sqlite3 /var/www/smartcapi/backend/smartcapi.db "VACUUM; ANALYZE;"

# Monitor resource usage
htop
```

---

## 📞 JIKA MASIH GAGAL

Kumpulkan informasi berikut:

```bash
# System info
uname -a
python3 --version

# Service status
systemctl status smartcapi-api smartcapi-workers redis nginx --no-pager

# Logs
journalctl -u smartcapi-api -n 100 --no-pager
journalctl -u smartcapi-workers -n 100 --no-pager

# Config
cat /var/www/smartcapi/backend/.env | grep -v "API_KEY\|SECRET"

# Database
ls -lh /var/www/smartcapi/backend/smartcapi.db
sqlite3 /var/www/smartcapi/backend/smartcapi.db "SELECT username, role FROM users;"

# Network
netstat -tulpn | grep -E '(8000|6379|80)'
curl -v http://127.0.0.1:8000/docs 2>&1 | head -20
```

---

## 💡 TIPS & BEST PRACTICES

1. **Selalu cek log saat ada error**
2. **Test backend manual sebelum pakai systemd**
3. **Verify Redis jalan sebelum start backend**
4. **Pastikan .env sudah configured dengan benar**
5. **Check database permissions (SQLite butuh write access)**
6. **Monitor resource usage (CPU, Memory, Disk)**
7. **Setup automated backups**
8. **Keep dependencies updated**
9. **Use HTTPS in production**
10. **Change default passwords immediately**

---

## 🔗 USEFUL COMMANDS REFERENCE

```bash
# Restart all services
systemctl restart smartcapi-api smartcapi-workers nginx

# View live logs
journalctl -u smartcapi-api -u smartcapi-workers -f

# Test API from command line
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admincapi","password":"supercapi"}'

# Database backup
sqlite3 smartcapi.db ".backup backup.db"

# Check disk space
df -h

# Check memory usage
free -h
```

---

**Created for SmartCAPI PWA by ITB-Bandung Institute of Technology**

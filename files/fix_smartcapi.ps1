# fix_smartcapi.ps1
# Script untuk deploy dan fix SmartCAPI PWA Backend

param(
    [string]$HostIP = "103.151.140.205",
    [string]$User = "root"
)

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "    SmartCAPI PWA - Backend Fixer" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target Server: $HostIP" -ForegroundColor Yellow
Write-Host "User: $User" -ForegroundColor Yellow
Write-Host ""

# Check if fix script exists
if (-not (Test-Path "fix_smartcapi.sh")) {
    Write-Error "File fix_smartcapi.sh tidak ditemukan!"
    Write-Host "Pastikan file ada di direktori yang sama dengan script ini."
    exit 1
}

# 1. Upload fix script
Write-Host ">>> Uploading fix script to VPS..." -ForegroundColor Yellow
scp fix_smartcapi.sh "$User@$HostIP`:/root/fix_smartcapi.sh"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Upload gagal!"
    exit 1
}

Write-Host "✓ Upload berhasil" -ForegroundColor Green
Write-Host ""

# 2. Execute fix script on server
Write-Host ">>> Executing fix script on VPS..." -ForegroundColor Yellow
Write-Host ""

$RemoteCommands = @"
# Fix line endings (convert CRLF to LF)
dos2unix /root/fix_smartcapi.sh 2>/dev/null || sed -i 's/\r$//' /root/fix_smartcapi.sh

# Make executable
chmod +x /root/fix_smartcapi.sh

# Execute
echo "Menjalankan fix script..."
echo ""
/root/fix_smartcapi.sh

# Additional diagnostics
echo ""
echo "=========================================="
echo "ADDITIONAL DIAGNOSTICS"
echo "=========================================="

echo ""
echo ">>> Process Check:"
ps aux | grep -E '(run_server|run_workers)' | grep -v grep || echo "No SmartCAPI processes found"

echo ""
echo ">>> Network Check:"
netstat -tulpn | grep -E '(8000|6379)' || echo "Ports 8000/6379 not listening"

echo ""
echo ">>> Recent API Logs (last 15 lines):"
journalctl -u smartcapi-api -n 15 --no-pager 2>/dev/null || echo "No API logs available"

echo ""
echo ">>> Recent Worker Logs (last 15 lines):"
journalctl -u smartcapi-workers -n 15 --no-pager 2>/dev/null || echo "No worker logs available"
"@

ssh "$User@$HostIP" $RemoteCommands

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "    Fix Process Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Silakan coba login di:" -ForegroundColor Cyan
Write-Host "  → http://$HostIP" -ForegroundColor White
Write-Host ""
Write-Host "Credentials:" -ForegroundColor Cyan
Write-Host "  Username: admincapi" -ForegroundColor White
Write-Host "  Password: supercapi" -ForegroundColor White
Write-Host ""
Write-Host "Jika masih gagal, cek diagnostics di atas ↑" -ForegroundColor Yellow
Write-Host ""

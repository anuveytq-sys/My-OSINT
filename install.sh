#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "=============================================="
echo "           MY OSINT TOOL - INSTALLER"
echo "=============================================="
echo
echo "This installer will install/setup the components"
echo "required by My OSINT:"
echo
echo "  [1] Holehe"
echo "  [2] user-scanner 1.5.2"
echo "  [3] Trio + HTTPX"
echo "  [4] Bundled PhoneInfoga"
echo "  [5] Bundled SpiderFoot"
echo
echo "These third-party components are used by My OSINT."
echo

read -r -p "Continue with installation? [y/N]: " answer

case "$answer" in
    y|Y|yes|YES)
        ;;
    *)
        echo "Installation cancelled."
        exit 0
        ;;
esac

echo
echo "[+] Updating Termux package information..."
pkg update -y

echo
echo "[+] Installing required Termux packages..."
pkg install -y python

echo
echo "[+] Installing Python dependencies..."
python -m pip install holehe
python -m pip install "user-scanner==1.5.2"
python -m pip install trio httpx

echo
echo "[+] Installing My OSINT Python requirements..."
if [ -f requirements.txt ]; then
    python -m pip install -r requirements.txt
fi

echo
echo "[+] Setting up PhoneInfoga..."

mkdir -p "$HOME/phoneinfoga"

if [ -f "third_party/phoneinfoga/phoneinfoga" ]; then
    cp "third_party/phoneinfoga/phoneinfoga" "$HOME/phoneinfoga/phoneinfoga"
    chmod +x "$HOME/phoneinfoga/phoneinfoga"
else
    echo "[ERROR] Bundled PhoneInfoga binary not found."
    exit 1
fi

echo
echo "[+] Setting up SpiderFoot..."

if [ -d "third_party/spiderfoot" ]; then
    rm -rf "$HOME/spiderfoot"
    cp -r "third_party/spiderfoot" "$HOME/spiderfoot"
else
    echo "[ERROR] Bundled SpiderFoot directory not found."
    exit 1
fi

echo
echo "[+] Installing SpiderFoot dependencies..."

if [ -f "$HOME/spiderfoot/requirements.txt" ]; then
    python -m pip install -r "$HOME/spiderfoot/requirements.txt"
fi

echo
echo "[+] Verifying installation..."

python - <<'PY'
import importlib.util
import os
import sys

checks = {
    "Holehe": "holehe",
    "Trio": "trio",
    "HTTPX": "httpx",
}

failed = False

for name, module in checks.items():
    if importlib.util.find_spec(module):
        print("[OK] " + name)
    else:
        print("[FAIL] " + name)
        failed = True

phoneinfoga = os.path.expanduser("~/phoneinfoga/phoneinfoga")
spiderfoot = os.path.expanduser("~/spiderfoot/sf.py")

if os.path.isfile(phoneinfoga):
    print("[OK] PhoneInfoga")
else:
    print("[FAIL] PhoneInfoga")
    failed = True

if os.path.isfile(spiderfoot):
    print("[OK] SpiderFoot")
else:
    print("[FAIL] SpiderFoot")
    failed = True

if failed:
    print("\n[ERROR] Installation verification failed.")
    sys.exit(1)

print("\n[OK] All required components are installed.")
PY

echo
echo "=============================================="
echo "       MY OSINT INSTALLATION COMPLETE"
echo "=============================================="
echo
echo "Run:"
echo
echo "  python main.py -e \"test@example.com\""
echo "  python main.py -p \"+919876543210\""
echo "  python main.py -u \"example_username\""
echo

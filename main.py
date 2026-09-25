#!/usr/bin/env python3
import argparse
import subprocess
from core.engine import run_modules
from core.result import Result

# Email modules
from email_modules.github import validate_github
from email_modules.reddit import validate_reddit
from email_modules.instagram import validate_instagram
from email_modules.twitter import validate_twitter

# Phone modules
from phone_modules.basic_info import validate_phone
from phone_modules.enhanced_info import validate_phone_enhanced

EMAIL_MODULES = [
    validate_github,
    validate_reddit,
    validate_instagram,
    validate_twitter
]

PHONE_MODULES = [
    validate_phone,
    validate_phone_enhanced
]

def print_results(results):
    print("-" * 55)
    for r in results:
        if r.exists is True:
            status = "FOUND     "
        elif r.exists is False:
            status = "NOT FOUND "
        else:
            status = "ERROR     "
        
        print(f"{status} | {r.site}")
        if r.info:
            for key, value in r.info.items():
                print(f"           → {key}: {value}")
        if r.error:
            print(f"           → Error: {r.error}")
        print("-" * 55)

def run_username_scan(username: str):
    """Run username scan - hide banner, keep colors as much as possible"""
    print(f"\n[*] Scanning username: {username}")
    print("-" * 55)
    
    try:
        process = subprocess.Popen(
            ["user-scanner", "-u", username],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        skip_banner = True
        for line in process.stdout:
            lower = line.lower()

            # Skip the big banner and version lines
            if skip_banner:
                if "checking username" in lower or line.strip().startswith("=="):
                    skip_banner = False
                else:
                    continue

            # Also skip any remaining tool name mentions
            if "user-scanner" in lower or "user scanner" in lower:
                continue

            print(line, end="")

        process.wait()

    except Exception as e:
        print(f"[ERROR] Username scan failed: {e}")
    
    print("-" * 55)

def main():
    parser = argparse.ArgumentParser(description="My OSINT Tool (Email + Phone + Username)")
    parser.add_argument("-e", "--email", help="Email to scan")
    parser.add_argument("-p", "--phone", help="Phone number (with country code)")
    parser.add_argument("-u", "--username", help="Username to scan")
    args = parser.parse_args()

    if args.email:
        print(f"\n[*] Scanning email: {args.email}\n")
        results = run_modules(args.email, EMAIL_MODULES)
        print_results(results)

    if args.phone:
        print(f"\n[*] Scanning phone: {args.phone}\n")
        results = run_modules(args.phone, PHONE_MODULES)
        print_results(results)

    if args.username:
        run_username_scan(args.username)

    if not any([args.email, args.phone, args.username]):
        parser.print_help()

if __name__ == "__main__":
    main()

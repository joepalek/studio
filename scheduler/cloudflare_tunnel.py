"""
Cloudflare Tunnel setup for mobile access to studio sidebar.

Cloudflare Tunnel provides:
- HTTPS by default
- Authentication via Cloudflare Access
- No port forwarding needed
- Persistent subdomain

Prerequisites:
1. Cloudflare account (free tier works)
2. Domain on Cloudflare (or use *.cfargotunnel.com for testing)
3. cloudflared installed: winget install cloudflare.cloudflared

Usage:
    python cloudflare_tunnel.py setup       # Initial setup
    python cloudflare_tunnel.py start       # Start tunnel
    python cloudflare_tunnel.py status      # Check status
    python cloudflare_tunnel.py config      # Show config file
"""

import os
import sys
import json
import subprocess
from pathlib import Path

STUDIO = os.environ.get("STUDIO_PATH", "G:/My Drive/Projects/_studio")
TUNNEL_NAME = "studio-sidebar"
CONFIG_DIR = Path.home() / ".cloudflared"
CONFIG_FILE = CONFIG_DIR / "config.yml"


def check_cloudflared() -> bool:
    """Check if cloudflared is installed."""
    try:
        result = subprocess.run(
            ["cloudflared", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ cloudflared installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("✗ cloudflared not found")
    print("  Install: winget install cloudflare.cloudflared")
    return False


def check_login() -> bool:
    """Check if logged in to Cloudflare."""
    cert_file = CONFIG_DIR / "cert.pem"
    if cert_file.exists():
        print("✓ Cloudflare credentials found")
        return True
    print("✗ Not logged in to Cloudflare")
    return False


def login():
    """Login to Cloudflare."""
    print("Opening browser for Cloudflare login...")
    subprocess.run(["cloudflared", "tunnel", "login"])


def create_tunnel() -> str:
    """Create a new tunnel."""
    print(f"Creating tunnel: {TUNNEL_NAME}")
    
    result = subprocess.run(
        ["cloudflared", "tunnel", "create", TUNNEL_NAME],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✓ Tunnel created")
        # Extract tunnel ID from output
        for line in result.stdout.split('\n'):
            if "Created tunnel" in line:
                print(f"  {line}")
        return TUNNEL_NAME
    else:
        if "already exists" in result.stderr:
            print(f"✓ Tunnel already exists")
            return TUNNEL_NAME
        print(f"✗ Failed: {result.stderr}")
        return None


def get_tunnel_id() -> str:
    """Get tunnel ID."""
    result = subprocess.run(
        ["cloudflared", "tunnel", "list", "--output", "json"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        tunnels = json.loads(result.stdout)
        for tunnel in tunnels:
            if tunnel.get("name") == TUNNEL_NAME:
                return tunnel.get("id")
    return None


def create_config(domain: str = None):
    """Create config.yml for the tunnel."""
    tunnel_id = get_tunnel_id()
    
    if not tunnel_id:
        print("✗ Could not find tunnel ID")
        return
    
    # Use trycloudflare.com for quick testing if no domain
    if not domain:
        domain = f"{TUNNEL_NAME}.trycloudflare.com"
        print(f"No domain specified, using: {domain}")
    
    config = f"""# Cloudflare Tunnel config for Studio Sidebar
tunnel: {tunnel_id}
credentials-file: {CONFIG_DIR}/{tunnel_id}.json

ingress:
  # Main sidebar endpoint
  - hostname: {domain}
    service: http://localhost:11435
    originRequest:
      noTLSVerify: true
  
  # Fallback
  - service: http_status:404
"""
    
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(config)
    print(f"✓ Config written to {CONFIG_FILE}")
    print(f"\nYour sidebar will be at: https://{domain}")


def route_dns(domain: str):
    """Create DNS route for tunnel."""
    print(f"Creating DNS route for {domain}...")
    
    result = subprocess.run(
        ["cloudflared", "tunnel", "route", "dns", TUNNEL_NAME, domain],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✓ DNS route created: {domain} -> {TUNNEL_NAME}")
    else:
        print(f"✗ Failed: {result.stderr}")


def start_tunnel():
    """Start the tunnel."""
    if not CONFIG_FILE.exists():
        print("✗ Config not found. Run: python cloudflare_tunnel.py setup")
        return
    
    print(f"Starting tunnel...")
    print(f"Config: {CONFIG_FILE}")
    print("\nPress Ctrl+C to stop\n")
    
    subprocess.run(
        ["cloudflared", "tunnel", "--config", str(CONFIG_FILE), "run"],
    )


def quick_tunnel():
    """Start a quick tunnel (no account needed, temporary URL)."""
    print("Starting quick tunnel (temporary URL, no account needed)...")
    print("This will give you a random *.trycloudflare.com URL")
    print("\nPress Ctrl+C to stop\n")
    
    subprocess.run(
        ["cloudflared", "tunnel", "--url", "http://localhost:11435"]
    )


def show_status():
    """Show tunnel status."""
    print("=== Cloudflare Tunnel Status ===\n")
    
    check_cloudflared()
    check_login()
    
    # List tunnels
    result = subprocess.run(
        ["cloudflared", "tunnel", "list"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"\nTunnels:\n{result.stdout}")
    
    if CONFIG_FILE.exists():
        print(f"Config file: {CONFIG_FILE}")
    else:
        print("Config file: not created")


def show_config():
    """Show config file contents."""
    if CONFIG_FILE.exists():
        print(f"=== {CONFIG_FILE} ===\n")
        print(CONFIG_FILE.read_text())
    else:
        print("Config not created. Run: python cloudflare_tunnel.py setup")


def setup(domain: str = None):
    """Full setup process."""
    print("=== Cloudflare Tunnel Setup ===\n")
    
    if not check_cloudflared():
        print("\nInstall cloudflared first:")
        print("  winget install cloudflare.cloudflared")
        return
    
    if not check_login():
        print("\nLogging in to Cloudflare...")
        login()
    
    print()
    create_tunnel()
    
    print()
    create_config(domain)
    
    print("\n=== Setup Complete ===")
    print(f"\nTo start tunnel:")
    print(f"  python cloudflare_tunnel.py start")
    print(f"\nOr for quick testing (temporary URL):")
    print(f"  python cloudflare_tunnel.py quick")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cloudflare_tunnel.py setup [domain]  # Full setup")
        print("  python cloudflare_tunnel.py start           # Start tunnel")
        print("  python cloudflare_tunnel.py quick           # Quick temp tunnel")
        print("  python cloudflare_tunnel.py status          # Show status")
        print("  python cloudflare_tunnel.py config          # Show config")
        return
    
    command = sys.argv[1]
    
    if command == "setup":
        domain = sys.argv[2] if len(sys.argv) > 2 else None
        setup(domain)
    elif command == "start":
        start_tunnel()
    elif command == "quick":
        quick_tunnel()
    elif command == "status":
        show_status()
    elif command == "config":
        show_config()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Simple local network server for testing
"""

import socket
from flask import Flask

def get_local_ip():
    """Get the local IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a dummy address
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("="*60)
    print("🏠 LOCAL NETWORK SERVER")
    print("="*60)
    print(f"\n📍 Your IP Address: {local_ip}")
    print(f"\n🔗 Local URL for your friend:")
    print(f"   http://{local_ip}:5000/manager/api/employee/create")
    print(f"\n📱 Web Interface:")
    print(f"   http://{local_ip}:5000")
    print("\n⚠️ Note: Both computers must be on same WiFi")
    print("="*60)
    
    # You still need to run Flask separately
    print("\n💡 Remember to also run: python app.py")
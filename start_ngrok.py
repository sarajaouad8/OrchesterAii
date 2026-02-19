#!/usr/bin/env python
"""
Simple script to start ngrok and expose Flask app publicly
"""

from pyngrok import ngrok
import webbrowser
import time

# Set your ngrok authtoken here (get from https://dashboard.ngrok.com)
NGROK_AUTH_TOKEN = input("Enter your ngrok auth token (from https://dashboard.ngrok.com): ")

try:
    # Kill all existing tunnels first
    print("🛑 Stopping any existing ngrok tunnels...")
    ngrok.kill()
    time.sleep(2)
    
    # Set auth token
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    
    # Start ngrok tunnel
    print("🚀 Starting fresh ngrok tunnel...")
    public_url = ngrok.connect(5000, "http")
    
    print("\n" + "="*60)
    print("✅ Ngrok is running!")
    print("="*60)
    print(f"\n📱 Your PUBLIC URL:")
    print(f"   {public_url}")
    print(f"\n🔗 Full API URL for your friend:")
    print(f"   {public_url}/manager/api/employee/create")
    print("\n" + "="*60)
    print("Keep this script running while testing!")
    print("Press Ctrl+C to stop ngrok")
    print("="*60 + "\n")
    
    # Keep ngrok running
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n\nStopping ngrok...")
    ngrok.kill()
    print("✅ Ngrok stopped")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure Flask is running on port 5000!")

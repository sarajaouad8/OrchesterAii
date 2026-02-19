#!/usr/bin/env python
"""
Simple ngrok script that just works
"""

from pyngrok import ngrok
import time
import requests

def simple_ngrok():
    # Your auth token
    NGROK_AUTH_TOKEN = "39hdqJZ9nN4hu3EXe7xUIeLbZeB_4MjMyeYRByodY2rQ4wNF7"
    
    try:
        # Set auth token
        ngrok.set_auth_token(NGROK_AUTH_TOKEN)
        
        # Kill existing tunnels
        print("🛑 Cleaning up existing tunnels...")
        ngrok.kill()
        time.sleep(2)
        
        # Start tunnel
        print("🚀 Starting ngrok tunnel...")
        tunnel = ngrok.connect(5000, "http")
        
        # Get the URL
        public_url = tunnel.public_url
        print(f"🌐 Raw tunnel object: {tunnel}")
        print(f"🔗 Extracted URL: {public_url}")
        
        # Simple test
        print(f"🧪 Testing {public_url}...")
        time.sleep(3)
        
        try:
            response = requests.get(public_url, timeout=10)
            print(f"✅ Test result: {response.status_code}")
            
            if response.status_code == 200:
                print("\n" + "="*60)
                print("✅ SUCCESS! Your ngrok is working!")
                print("="*60)
                print(f"\n📱 Your URL: {public_url}")
                print(f"\n🔗 For your friend:")
                print(f"   {public_url}/manager/api/employee/create")
                print("\n" + "="*60)
                print("Keep this terminal open!")
                print("Press Ctrl+C to stop ngrok")
                print("="*60)
                
                # Keep running
                while True:
                    time.sleep(60)
            else:
                print(f"❌ HTTP {response.status_code} - Something wrong with Flask")
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            print(f"URL: {public_url}")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping ngrok...")
        ngrok.kill()
        print("✅ Stopped!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure Flask is running!")

if __name__ == "__main__":
    simple_ngrok()
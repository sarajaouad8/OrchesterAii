#!/usr/bin/env python
"""
Robust ngrok script with auto-reconnection and health checks
"""

from pyngrok import ngrok
import time
import requests
import webbrowser

def start_reliable_ngrok():
    # Your auth token
    NGROK_AUTH_TOKEN = "39hdqJZ9nN4hu3EXe7xUIeLbZeB_4MjMyeYRByodY2rQ4wNF7"
    
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    
    while True:
        try:
            print("🛑 Stopping any existing tunnels...")
            ngrok.kill()
            time.sleep(3)
            
            print("🚀 Starting ngrok tunnel...")
            tunnel = ngrok.connect(5000, "http")
            
            # Extract the actual URL string from the tunnel object
            public_url = str(tunnel.public_url)
            
            # Test if tunnel works
            test_url = f"{public_url}/debug/webhook-test"
            print(f"🧪 Testing tunnel: {public_url}")
            
            time.sleep(5)  # Wait for tunnel to stabilize
            
            try:
                response = requests.get(f"{public_url}/", timeout=10)
                if response.status_code == 200:
                    print("\n" + "="*70)
                    print("✅ TUNNEL IS WORKING PERFECTLY!")
                    print("="*70)
                    print(f"\n📱 Your WORKING URL:")
                    print(f"   {public_url}")
                    print(f"\n🔗 Send this to your friend:")
                    print(f"   {public_url}/manager/api/employee/create")
                    print("\n" + "="*70)
                    print("✅ Tunnel tested and confirmed working!")
                    print("Press Ctrl+C to stop")
                    print("="*70 + "\n")
                    
                    # Keep monitoring tunnel health
                    while True:
                        time.sleep(30)  # Check every 30 seconds
                        try:
                            health_check = requests.get(f"{public_url}/", timeout=5)
                            if health_check.status_code != 200:
                                print("⚠️ Tunnel unhealthy, restarting...")
                                break
                        except:
                            print("❌ Tunnel died, restarting...")
                            break
                            
                else:
                    print(f"❌ Tunnel not working (status: {response.status_code}), retrying...")
                    time.sleep(10)
                    
            except Exception as e:
                print(f"❌ Tunnel connection failed: {e}")
                print("🔄 Retrying in 10 seconds...")
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping ngrok...")
            ngrok.kill()
            print("✅ Ngrok stopped")
            break
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("🔄 Retrying in 15 seconds...")
            time.sleep(15)

if __name__ == "__main__":
    print("🚀 Starting RELIABLE ngrok tunnel...")
    start_reliable_ngrok()
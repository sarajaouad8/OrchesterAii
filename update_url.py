#!/usr/bin/env python
"""
Update your public URL in config when you get a new ngrok URL
"""

import re

def update_public_url():
    new_url = input("Enter your new ngrok URL (e.g., https://abc123.ngrok-free.dev): ").strip()
    
    # Validate URL format
    if not new_url.startswith('https://') or 'ngrok' not in new_url:
        print("❌ Invalid URL format. Should be like: https://abc123.ngrok-free.dev")
        return
    
    # Read config file
    try:
        with open('config.py', 'r') as f:
            content = f.read()
        
        # Replace the PUBLIC_URL line
        pattern = r"PUBLIC_URL = os\.getenv\('PUBLIC_URL', '[^']*'\)"
        replacement = f"PUBLIC_URL = os.getenv('PUBLIC_URL', '{new_url}')"
        
        new_content = re.sub(pattern, replacement, content)
        
        # Write back
        with open('config.py', 'w') as f:
            f.write(new_content)
        
        print(f"✅ Updated PUBLIC_URL to: {new_url}")
        print("🔄 Restart Flask to apply changes")
        
        print(f"\n📋 Tell your friend n8n should send results to:")
        print(f"   {new_url}/manager/api/employee/create")
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")

if __name__ == "__main__":
    print("🔧 Public URL Updater")
    print("=" * 50)
    update_public_url()
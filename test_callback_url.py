#!/usr/bin/env python
"""
Test callback URL generation to verify it uses PUBLIC_URL instead of localhost
"""

import sys
sys.path.append('.')

from flask import Flask, url_for
from config import Config

# Create a test Flask app
app = Flask(__name__)
app.config.from_object(Config)

print("🔍 Testing Callback URL Generation")
print("=" * 50)
print(f"📡 PUBLIC_URL from config: {app.config.get('PUBLIC_URL', 'Not set')}")

with app.test_request_context():
    # This simulates what happens in the route
    if app.config.get('PUBLIC_URL'):
        callback_url = app.config['PUBLIC_URL'] + '/manager/api/employee/create'
    else:
        callback_url = url_for('manager.api_create_employee', _external=True)
    
    print(f"🔗 Generated callback URL: {callback_url}")
    
    if 'localhost' in callback_url or '127.0.0.1' in callback_url:
        print("❌ PROBLEM: URL still contains localhost/127.0.0.1!")
        print("   n8n won't be able to reach this URL from external network")
    else:
        print("✅ GOOD: URL uses public address!")
        print("   n8n should be able to reach this callback URL")
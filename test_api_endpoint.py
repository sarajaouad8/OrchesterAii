#!/usr/bin/env python
"""
Test your Flask API endpoint to make sure HTTP is working correctly
This will simulate what n8n should send to your API
"""

import requests
import json

print("🧪 TESTING YOUR FLASK API ENDPOINT")
print("=" * 60)

# Your API endpoint
url = "https://untrumpeted-prenational-celeste.ngrok-free.dev/manager/api/employee/create"

# Test data (simulating what n8n should send)
test_data = {
    "personal_info": {
        "full_name": "Test User",
        "email": "test@example.com",
        "phone": "+1234567890",
        "professional_headline": "Test Engineer"
    },
    "technical_skills": {
        "programming_languages": ["Python", "JavaScript"],
        "frameworks": ["Flask", "React"],
        "databases": ["PostgreSQL"],
        "tools": ["Docker", "Git"]
    },
    "certifications": [],
    "languages": [],
    "work_experience": []
}

print("📤 SENDING TEST REQUEST...")
print(f"🔗 URL: {url}")
print(f"📋 Data: {json.dumps(test_data, indent=2)}")
print("-" * 60)

try:
    # Send POST request
    response = requests.post(
        url, 
        json=test_data,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    
    print(f"✅ STATUS CODE: {response.status_code}")
    print(f"📨 RESPONSE HEADERS: {dict(response.headers)}")
    
    if response.status_code == 200:
        result = response.json()
        print("🎉 SUCCESS! API is working correctly!")
        print(f"📊 Response: {json.dumps(result, indent=2)}")
        
        if 'employee' in result:
            print("\n✅ EMPLOYEE CREATED:")
            emp = result['employee']
            print(f"   👤 Name: {emp.get('name')}")
            print(f"   📧 Email: {emp.get('email')}")
            print(f"   🔑 Username: {emp.get('username')}")
            print(f"   🔐 Password: {emp.get('password')}")
            print(f"   🛠️ Skills: {emp.get('technical_skills')}")
            
        if 'debug' in result:
            print("\n🔍 DEBUG INFO:")
            debug = result['debug']
            print(f"   📊 Skills received: {debug.get('skills_received')}")
            print(f"   💾 Skills stored: {debug.get('skills_stored_in_db')}")
        
    else:
        print("❌ ERROR RESPONSE:")
        try:
            error_data = response.json()
            print(f"📋 Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"📋 Raw response: {response.text}")

except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR: Can't reach your Flask app!")
    print("💡 Make sure:")
    print("   1. Flask is running on port 5000")
    print("   2. ngrok tunnel is active")

except requests.exceptions.Timeout:
    print("❌ TIMEOUT ERROR: Flask took too long to respond")
    
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {e}")

print("\n" + "=" * 60)
print("📋 SUMMARY:")
print("=" * 60)
print("If you see '✅ SUCCESS!' above, your API is working!")
print("If you see errors, we need to fix your Flask setup first.")
print("\nThis test simulates exactly what n8n should send to your API.")
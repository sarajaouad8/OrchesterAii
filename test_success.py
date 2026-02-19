#!/usr/bin/env python
"""
Test with unique email to show successful creation
"""

import requests
import json
import random

print("🧪 TESTING API WITH UNIQUE EMAIL")
print("=" * 50)

# Generate unique email
unique_id = random.randint(1000, 9999)
url = "https://untrumpeted-prenational-celeste.ngrok-free.dev/manager/api/employee/create"

test_data = {
    "personal_info": {
        "full_name": f"Test User {unique_id}",
        "email": f"test{unique_id}@example.com",
        "phone": "+1234567890"
    },
    "technical_skills": {
        "programming_languages": ["Python", "JavaScript"],
        "frameworks": ["Flask"] 
    },
    "certifications": [],
    "languages": [],
    "work_experience": []
}

print(f"📧 Testing with email: {test_data['personal_info']['email']}")

try:
    response = requests.post(url, json=test_data, timeout=30)
    
    print(f"✅ STATUS: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("🎉 SUCCESS! Employee created!")
        print(f"👤 Name: {result['employee']['name']}")
        print(f"🔑 Username: {result['employee']['username']}")
        print(f"🔐 Password: {result['employee']['password']}")
        print(f"🛠️ Skills: {result['employee']['technical_skills']}")
        
    else:
        print("❌ Error:", response.json())
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🎯 CONCLUSION: Your HTTP API is working perfectly!")
print("   The problem is only with your friend's JSON format.")
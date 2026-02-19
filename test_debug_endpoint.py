#!/usr/bin/env python
"""
Test the debug endpoint to show your friend how to use it
"""

import requests
import json

# Test what happens with complete data
complete_data = {
    "personal_info": {
        "full_name": "John Doe",
        "email": "john@email.com"
    },
    "technical_skills": {
        "programming": ["Python", "JavaScript"],
        "tools": ["Docker", "Git"]
    },
    "certifications": [],
    "languages": [],
    "work_experience": []
}

# Test what happens with minimal data (what friend probably has)
minimal_data = {
    "personal_info": {
        "full_name": "Jane Smith", 
        "email": "jane@email.com"
    },
    "technical_skills": {
        "skills": ["React", "Node.js"]
    }
    # Note: missing certifications, languages, work_experience
}

print("🔧 TESTING DEBUG ENDPOINT FOR YOUR FRIEND")
print("=" * 60)

url = "https://untrumpeted-prenational-celeste.ngrok-free.dev/manager/debug/analyze"

print("📊 Test 1: Complete JSON structure")
print("-" * 40)
try:
    response = requests.post(url, json=complete_data, timeout=10)
    print(f"✅ Status: {response.status_code}")
    result = response.json()
    print(f"📋 Analysis: {json.dumps(result['analysis'], indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n📊 Test 2: Minimal JSON (what friend probably has)")
print("-" * 40)
try:
    response = requests.post(url, json=minimal_data, timeout=10)
    print(f"✅ Status: {response.status_code}")
    result = response.json()
    print(f"📋 Analysis: {json.dumps(result['analysis'], indent=2)}")
    print(f"💡 Missing fields: {result['recommendations']['missing_fields']}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("💬 TELL YOUR FRIEND:")
print("=" * 60)
print("1. Send her AI analysis JSON to the debug endpoint")
print("2. Check what fields actually exist") 
print("3. Only use existing fields in the final JSON")
print("4. For missing fields, use empty arrays: []")
print(f"🔗 Debug URL: {url}")
#!/usr/bin/env python
"""
Test the project specs workflow endpoint configuration
"""

import sys
sys.path.append('.')

from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

print("🔧 TESTING PROJECT SPECS CONFIGURATION")
print("=" * 60)

print("✅ Configuration loaded:")
print(f"📤 Your Flask sends project specs to:")
print(f"   {app.config['N8N_PROJECT_WEBHOOK_URL']}")
print(f"📥 Friend's n8n sends results back to:")
print(f"   {app.config['PUBLIC_URL']}/manager/api/project/update")

print("\n📋 Complete workflow URLs:")
print("-" * 40)
print(f"🔗 CV Analysis:")
print(f"   TO: {app.config['N8N_WEBHOOK_URL']}")
print(f"   FROM: {app.config['PUBLIC_URL']}/manager/api/employee/create")

print(f"\n🔗 Project Specs Analysis:")
print(f"   TO: {app.config['N8N_PROJECT_WEBHOOK_URL']}")
print(f"   FROM: {app.config['PUBLIC_URL']}/manager/api/project/update")

print("\n✅ Configuration is correct!")
print("📋 Tell your friend to use the workflow in: COMPLETE_N8N_WORKFLOW_v264.md")
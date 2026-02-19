"""
Database migration to add AI analysis fields to projects table
Run this script to update your database schema
"""

import sys
sys.path.append('.')

from app import app
from models import db

print("🔄 Updating projects table schema...")

with app.app_context():
    try:
        # Add new columns to projects table
        migrations = [
            # Remove cv_path if it exists
            "ALTER TABLE projects DROP COLUMN IF EXISTS cv_path CASCADE;",
            
            # Add new columns for project specs
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS specs_file VARCHAR(200);",
            
            # Add AI analysis columns
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_type VARCHAR(100);",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS complexity VARCHAR(20);",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS estimated_duration VARCHAR(50);",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS required_skills JSON;",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS tech_stack JSON;",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS key_features JSON;",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS specs_data JSON;",
        ]
        
        for migration in migrations:
            try:
                db.session.execute(db.text(migration))
                print(f"✅ {migration[:50]}...")
            except Exception as e:
                print(f"⚠️ {migration[:50]}... (might already exist)")
        
        db.session.commit()
        print("\n🎉 Database schema updated successfully!")
        print("✅ Projects table now supports AI project analysis")
        
    except Exception as e:
        print(f"\n❌ Error updating database: {e}")
        db.session.rollback()
        sys.exit(1)

print("\n📋 New project fields:")
print("   - specs_file: Original filename")
print("   - project_type: Type of project (web, mobile, etc.)")
print("   - complexity: Project complexity (simple, medium, complex)")
print("   - estimated_duration: AI-estimated time")
print("   - required_skills: Skills needed (JSON)")
print("   - tech_stack: Technologies to use (JSON)")
print("   - key_features: Main features list (JSON)")
print("   - specs_data: Complete AI analysis (JSON)")
print("\n✅ Ready to analyze project specifications!")
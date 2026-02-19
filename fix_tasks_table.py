"""
Fix Tasks Table - Rename old table and create new one
"""

from app import app, db
from sqlalchemy import text

def fix_tasks_table():
    """Rename old tasks table and create new one with correct structure"""
    with app.app_context():
        print("🔄 Fixing tasks table structure...")
        
        try:
            with db.engine.connect() as conn:
                # Rename old tasks table as backup
                print("📝 Renaming old tasks table to tasks_old...")
                conn.execute(text("""
                    ALTER TABLE IF EXISTS tasks RENAME TO tasks_old
                """))
                conn.commit()
                print("✅ Old table renamed")
                
                # Create new tasks table with correct structure
                print("📝 Creating new tasks table...")
                conn.execute(text("""
                    CREATE TABLE tasks (
                        id SERIAL PRIMARY KEY,
                        project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        task_id VARCHAR(50) NOT NULL,
                        nom VARCHAR(300) NOT NULL,
                        priorite VARCHAR(20),
                        dependances JSON,
                        duree_estimee_jours INTEGER,
                        status VARCHAR(50) DEFAULT 'not started',
                        sous_taches JSON,
                        assigned_employee_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        assigned_at TIMESTAMP,
                        match_score FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create indexes for better performance
                print("📝 Creating indexes...")
                conn.execute(text("""
                    CREATE INDEX idx_tasks_project_id ON tasks(project_id);
                    CREATE INDEX idx_tasks_assigned_employee_id ON tasks(assigned_employee_id);
                """))
                
                conn.commit()
                print("✅ New tasks table created with correct structure")
                print("ℹ️  Old table saved as 'tasks_old' (can be dropped later)")
            
            print("\n✅ Migration completed successfully!")
            print("🎯 You can now use the task management system!")
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
            raise

if __name__ == '__main__':
    fix_tasks_table()

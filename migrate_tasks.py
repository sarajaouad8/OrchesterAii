"""
Database Migration: Add Task Management System
- Creates tasks table with task breakdown from AI analysis
- Adds new fields to projects table for detailed CDC analysis
- Preserves existing data
"""

from app import app, db
from sqlalchemy import text

def migrate_database():
    """Add new columns and create tasks table"""
    with app.app_context():
        print("🔄 Starting database migration for task management...")
        
        try:
            with db.engine.connect() as conn:
                # Check if we need to add new columns to projects
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='projects' AND column_name='nom_projet'
                """))
                
                if not result.fetchone():
                    print("📝 Adding new columns to projects table...")
                    conn.execute(text("""
                        ALTER TABLE projects 
                        ADD COLUMN IF NOT EXISTS nom_projet VARCHAR(300),
                        ADD COLUMN IF NOT EXISTS resume TEXT,
                        ADD COLUMN IF NOT EXISTS livrables_attendus JSON,
                        ADD COLUMN IF NOT EXISTS besoins JSON,
                        ADD COLUMN IF NOT EXISTS taches_techniques JSON,
                        ADD COLUMN IF NOT EXISTS analyse_ressources JSON,
                        ADD COLUMN IF NOT EXISTS estimation_globale JSON
                    """))
                    conn.commit()
                    print("✅ New columns added to projects table")
                else:
                    print("ℹ️  Projects table already has new columns")
                
                # Check if tasks table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'tasks'
                    )
                """))
                
                tasks_exists = result.scalar()
                
                if not tasks_exists:
                    print("📝 Creating tasks table...")
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
                    conn.execute(text("""
                        CREATE INDEX idx_tasks_project_id ON tasks(project_id);
                        CREATE INDEX idx_tasks_assigned_employee_id ON tasks(assigned_employee_id);
                    """))
                    
                    conn.commit()
                    print("✅ Tasks table created with indexes")
                else:
                    print("ℹ️  Tasks table already exists")
            
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
            raise

if __name__ == '__main__':
    migrate_database()

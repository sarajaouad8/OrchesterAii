"""Check database structure"""
from app import app, db
from sqlalchemy import text

with app.app_context():
    with db.engine.connect() as conn:
        print("=" * 60)
        print("CHECKING DATABASE STRUCTURE")
        print("=" * 60)
        
        # Check if tasks table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'tasks'
            )
        """))
        print(f"\n✓ Tasks table exists: {result.scalar()}")
        
        # List all tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        print(f"\n📋 All tables:")
        for row in result:
            print(f"  - {row[0]}")
        
        # Check tasks table columns if it exists
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'tasks'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        if columns:
            print(f"\n📊 Tasks table columns:")
            for col_name, col_type in columns:
                print(f"  - {col_name}: {col_type}")
        else:
            print(f"\n⚠️  No columns found for tasks table (table doesn't exist)")

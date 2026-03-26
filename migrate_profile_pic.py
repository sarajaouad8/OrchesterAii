"""Add profile_pic column to users table in PostgreSQL."""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='orchestraai_db',
    user='postgres',
    password='sara123'
)
conn.autocommit = True
cursor = conn.cursor()

# Check if column exists
cursor.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name='users' AND column_name='profile_pic'
""")
if cursor.fetchone():
    print("✅ 'profile_pic' column already exists")
else:
    cursor.execute("ALTER TABLE users ADD COLUMN profile_pic VARCHAR(255)")
    print("✅ Added 'profile_pic' column to users table")

cursor.close()
conn.close()

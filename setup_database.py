#!/usr/bin/env python3
"""
Database setup script for FormMind-AI
Run this to create all database tables
"""
import psycopg2
import sys

def setup_database():
    """Create all database tables"""
    
    # Database connection parameters
    conn_params = {
        'host': 'localhost',
        'database': 'formmind_db',
        'user': 'formmind_user',
        'password': 'formmind_pass',
        'port': 5432
    }
    
    # SQL commands to create tables
    table_commands = [
        # 1. Tenants table
        """
        CREATE TABLE IF NOT EXISTS tenants (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        """,
        
        # 2. Users table
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
            email TEXT NOT NULL,
            name TEXT,
            password_hash TEXT,
            role TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            last_login_at TIMESTAMP WITH TIME ZONE
        );
        """,
        
        # 3. Forms table
        """
        CREATE TABLE IF NOT EXISTS forms (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            access_type TEXT NOT NULL DEFAULT 'public',
            single_submission BOOLEAN DEFAULT FALSE,
            submission_start TIMESTAMP WITH TIME ZONE,
            submission_end TIMESTAMP WITH TIME ZONE,
            public_token TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        """,
        
        # 4. Form versions table
        """
        CREATE TABLE IF NOT EXISTS form_versions (
            id SERIAL PRIMARY KEY,
            form_id INTEGER REFERENCES forms(id) ON DELETE CASCADE,
            version_number INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            is_active BOOLEAN DEFAULT TRUE
        );
        """,
        
        # 5. Questions table
        """
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            form_version_id INTEGER REFERENCES form_versions(id) ON DELETE CASCADE,
            label TEXT NOT NULL,
            placeholder TEXT,
            help_text TEXT,
            field_type TEXT,
            required BOOLEAN DEFAULT FALSE,
            default_value TEXT,
            order_index INTEGER DEFAULT 0,
            validation_min NUMERIC,
            validation_max NUMERIC,
            validation_regex TEXT
        );
        """,
        
        # 6. Question options table
        """
        CREATE TABLE IF NOT EXISTS question_options (
            id SERIAL PRIMARY KEY,
            question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
            label TEXT,
            value TEXT,
            order_index INTEGER DEFAULT 0
        );
        """,
        
        # 7. Submissions table
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id SERIAL PRIMARY KEY,
            form_id INTEGER REFERENCES forms(id) ON DELETE CASCADE,
            form_version_id INTEGER REFERENCES form_versions(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id),
            guest_token TEXT,
            submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            completion_time_ms INTEGER
        );
        """,
        
        # 8. Answers table
        """
        CREATE TABLE IF NOT EXISTS answers (
            id SERIAL PRIMARY KEY,
            submission_id INTEGER REFERENCES submissions(id) ON DELETE CASCADE,
            question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
            value TEXT
        );
        """,
        
        # 9. Templates table
        """
        CREATE TABLE IF NOT EXISTS templates (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            category TEXT,
            visibility TEXT DEFAULT 'private',
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        """
    ]
    
    try:
        # Connect to database
        print("🔌 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        print("✅ Connected successfully!")
        
        # Execute each table creation command
        print("\n📋 Creating tables...")
        for i, command in enumerate(table_commands, 1):
            table_name = command.split('TABLE IF NOT EXISTS')[1].split('(')[0].strip()
            try:
                cur.execute(command)
                print(f"✅ {i}. Created table: {table_name}")
            except Exception as e:
                print(f"❌ {i}. Failed to create table {table_name}: {e}")
                
        # Commit all changes
        conn.commit()
        print("\n💾 All changes committed!")
        
        # List all created tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print(f"\n🎉 Database setup complete! Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
            
        # Close connections
        cur.close()
        conn.close()
        print("\n✅ Database connection closed. Setup successful! 🚀")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FormMind-AI Database Setup")
    print("=" * 40)
    
    success = setup_database()
    
    if success:
        print("\n🎯 Next steps:")
        print("   1. Test the database connection")
        print("   2. Run: python -c \"from app.db import test_connection; test_connection()\"")
        print("   3. Start implementing the services!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Please check your PostgreSQL connection.")
        sys.exit(1)
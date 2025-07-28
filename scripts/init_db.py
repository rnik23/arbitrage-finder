#!/usr/bin/env python3
"""
Database initialization script for arbitrage finder
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def init_database():
    """Initialize the database schema"""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'arbitrage_finder'),
            user=os.getenv('DB_USER', 'arbitrage_user'),
            password=os.getenv('DB_PASSWORD', 'arbitrage_password')
        )
        
        # Read and execute SQL schema
        with open('database/init.sql', 'r') as sql_file:
            sql_commands = sql_file.read()
        
        cursor = conn.cursor()
        
        # Execute the SQL commands
        print("🗄️ Creating database schema...")
        cursor.execute(sql_commands)
        conn.commit()
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchall()
        
        print("✅ Database schema initialized successfully!")
        print(f"📊 Created tables: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    init_database()

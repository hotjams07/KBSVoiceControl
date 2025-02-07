import sqlite3
from database import Database

def inspect_database(db_path):
    try:
        # Connect to the database
        print(f"Attempting to connect to database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\nDatabase Tables:")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Show sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                print("\nSample row:")
                print(sample)
        
        # Show all commands
        show_all_commands(cursor)
                
    except sqlite3.Error as e:
        print(f"Error accessing database: {e}")
    finally:
        if conn:
            conn.close()

def show_all_commands(cursor):
    """Show all commands in the database"""
    cursor.execute("""
        SELECT id, command_name, shortcut, voice_command 
        FROM commands 
        ORDER BY command_name
    """)
    rows = cursor.fetchall()
    print("\nAll Commands:")
    for row in rows:
        print(f"ID: {row[0]}, Command: {row[1]}, Shortcut: {row[2]}, Voice Command: {row[3]}")

def cleanup_database(db_path):
    """Clean up database duplicates"""
    try:
        db = Database(db_path)
        if db.cleanup_duplicates():
            print("Database cleaned up successfully")
        else:
            print("Error cleaning up database")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    db_path = "/Users/jameswatson/Cursor AI Projects/Voice Contrl Project/V1/backups/2025-01-16_21-56/studio_one_commands_2025-01-16_21-56.db"
    
    # First show current state
    inspect_database(db_path)
    
    # Clean up database
    print("\nCleaning up database...")
    cleanup_database(db_path)
    
    # Show state after cleanup
    print("\nAfter cleanup:")
    inspect_database(db_path) 
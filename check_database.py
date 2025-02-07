import sqlite3

def view_database(db_path='studio_one_commands.db'):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                print(f"\nTable: {table_name}")
                print("-" * 40)
                
                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print("Columns:", ", ".join(column_names))
                
                # Get all records
                cursor.execute(f"SELECT * FROM {table_name}")
                records = cursor.fetchall()
                
                print(f"\nRecords ({len(records)} total):")
                for record in records:
                    print(record)
                    
    except sqlite3.Error as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    view_database() 
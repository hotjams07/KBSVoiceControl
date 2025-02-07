from database import Database
import sqlite3

def display_commands():
    db = Database()
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM commands')
            commands = cursor.fetchall()
            
            if not commands:
                print("No commands found in database.")
                return
            
            # Print header
            print("\nStudio One Commands Database:")
            print("-" * 80)
            print(f"{'ID':<5} {'Command Name':<30} {'Shortcut':<15} {'Category':<15} {'Voice Command':<15}")
            print("-" * 80)
            
            # Print each command
            for cmd in commands:
                print(f"{cmd[0]:<5} {cmd[1]:<30} {cmd[2] or '':<15} {cmd[3] or '':<15} {cmd[4] or '':<15}")
                
    except sqlite3.Error as e:
        print(f"Error accessing database: {e}")

def add_new_command():
    command_name = input("Enter command name: ")
    shortcut = input("Enter shortcut (or press Enter to skip): ") or None
    category = input("Enter category (or press Enter to skip): ") or None
    voice_command = input("Enter voice command (or press Enter to skip): ") or None
    
    db = Database()
    command_id = db.add_command(command_name, shortcut, category, voice_command)
    if command_id:
        print(f"Command added successfully with ID: {command_id}")
    else:
        print("Failed to add command")

def search_command():
    search_term = input("Enter command name to search: ")
    db = Database()
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM commands 
                WHERE command_name LIKE ?
            ''', (f'%{search_term}%',))
            
            commands = cursor.fetchall()
            
            if not commands:
                print(f"No commands found matching '{search_term}'")
                return
            
            # Print header
            print("\nMatching commands:")
            print("-" * 80)
            print(f"{'ID':<5} {'Command Name':<30} {'Shortcut':<15} {'Category':<15} {'Voice Command':<15}")
            print("-" * 80)
            
            for cmd in commands:
                print(f"{cmd[0]:<5} {cmd[1]:<30} {cmd[2] or '':<15} {cmd[3] or '':<15} {cmd[4] or '':<15}")
                
    except sqlite3.Error as e:
        print(f"Error searching database: {e}")

def menu():
    while True:
        print("\n1. Display all commands")
        print("2. Add new command")
        print("3. Search commands")
        print("4. Exit")
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            display_commands()
        elif choice == '2':
            add_new_command()
        elif choice == '3':
            search_command()
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    db = Database()
    db.initialize()
    menu() 
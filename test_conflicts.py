from database import Database
import sqlite3

def test_conflicts():
    print("Starting conflict test...")
    
    # Create database instance
    db = Database()
    
    try:
        # Initialize database if not exists
        db.initialize()
        print("Database initialized")
        
        # Add some test commands with potential conflicts
        test_commands = [
            {
                "command_name": "Play",
                "shortcut": "Space",
                "category": "Transport",
                "voice_command": "play"
            },
            {
                "command_name": "Stop",
                "shortcut": "Space",  # Deliberate conflict
                "category": "Transport",
                "voice_command": "stop"
            },
            {
                "command_name": "Record",
                "shortcut": "R",
                "category": "Transport",
                "voice_command": "play"  # Deliberate voice command conflict
            }
        ]
        
        # Add commands and check for conflicts
        for cmd in test_commands:
            command_id = db.add_command(**cmd)
            print(f"Added command '{cmd['command_name']}' with ID: {command_id}")
            
        # Check for shortcut conflicts
        print("\nChecking for shortcut conflicts...")
        conflicts = db.check_shortcut_conflicts()
        if conflicts:
            print("Found shortcut conflicts:")
            for conflict in conflicts:
                print(f"Shortcut '{conflict[0]}' is used by multiple commands")
        else:
            print("No shortcut conflicts found")
            
        # Check for voice command conflicts
        print("\nChecking for voice command conflicts...")
        voice_conflicts = db.check_voice_conflicts()
        if voice_conflicts:
            print("Found voice command conflicts:")
            for conflict in voice_conflicts:
                print(f"Voice command '{conflict[0]}' is used by multiple commands")
        else:
            print("No voice command conflicts found")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_conflicts() 
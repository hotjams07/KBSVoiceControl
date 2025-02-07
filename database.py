import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='studio_one_commands.db'):
        self.db_path = db_path
        self.conn = None
        
    def initialize(self):
        """Create the database and tables if they don't exist"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create the commands table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_name TEXT NOT NULL,
                    shortcut TEXT,
                    category TEXT,
                    voice_command TEXT,
                    conflict_flag BOOLEAN DEFAULT FALSE,
                    conflict_type TEXT,
                    conflict_with TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add new table for discovered actions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS discovered_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    program_name TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    api_endpoint TEXT,
                    shortcut TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add workflow table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT NOT NULL,
                    voice_trigger TEXT NOT NULL,
                    command_sequence TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add command usage tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_id INTEGER,
                    usage_count INTEGER DEFAULT 0,
                    last_used TIMESTAMP,
                    context TEXT,
                    FOREIGN KEY (command_id) REFERENCES commands (id)
                )
            ''')
            
            self.conn.commit()
            print("DEBUG: DB - Database initialized")
            
        except Exception as e:
            print(f"DEBUG: DB - Error initializing: {e}")
            raise
            
    def add_command(self, command_name, shortcut, category, voice_command=None):
        """Add a new command to the database with duplicate checking"""
        try:
            cursor = self.conn.cursor()
            
            # Check for duplicates
            cursor.execute("""
                SELECT id FROM commands 
                WHERE LOWER(command_name) = LOWER(?) 
                OR LOWER(voice_command) = LOWER(?)
            """, (command_name, voice_command))
            
            if cursor.fetchone():
                print(f"Warning: Command '{command_name}' or voice command '{voice_command}' already exists")
                return False
                
            # If no duplicate, add the command
            cursor.execute("""
                INSERT INTO commands (
                    command_name, shortcut, category, voice_command, 
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (command_name, shortcut, category, voice_command))
            
            return True
            
        except sqlite3.Error as e:
            print(f"Error adding command: {e}")
            return False
            
    def update_command(self, command_id, command_name, shortcut=None, category=None, voice_command=None):
        """Update an existing command"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE commands 
                SET command_name=?, shortcut=?, category=?, voice_command=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (command_name, shortcut, category, voice_command, command_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating command: {e}")
            return False
            
    def delete_command(self, command_id):
        """Delete a command"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM commands WHERE id=?', (command_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting command: {e}")
            return False 
            
    def export_commands(self, filename):
        """Export commands to CSV file"""
        import csv
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM commands')
            rows = cursor.fetchall()
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['id', 'command_name', 'shortcut', 'category', 
                               'voice_command', 'conflict_flag', 'conflict_type', 
                               'conflict_with', 'created_at', 'updated_at'])
                writer.writerows(rows)
            return True
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False 
            
    def get_categories(self):
        """Get list of unique categories"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM commands WHERE category IS NOT NULL')
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting categories: {e}")
            return [] 
            
    def backup_database(self, backup_path):
        """Create a backup of the database"""
        import shutil
        try:
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False 
            
    def check_shortcut_conflicts(self):
        """Check for commands that share the same shortcut"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT shortcut, GROUP_CONCAT(command_name) as commands, COUNT(*) as count
                FROM commands 
                WHERE shortcut IS NOT NULL
                GROUP BY shortcut
                HAVING count > 1
            ''')
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error checking shortcut conflicts: {e}")
            return []
            
    def check_voice_conflicts(self):
        """Check for commands that share the same voice command"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT voice_command, GROUP_CONCAT(command_name) as commands, COUNT(*) as count
                FROM commands 
                WHERE voice_command IS NOT NULL
                GROUP BY voice_command
                HAVING count > 1
            ''')
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error checking voice conflicts: {e}")
            return []

    def import_shortcuts_file(self, shortcuts, program_name):
        """Import shortcuts from parsed data"""
        try:
            cursor = self.conn.cursor()
            for shortcut in shortcuts:
                cursor.execute('''
                    INSERT INTO commands 
                    (command_name, shortcut, category, program_name)
                    VALUES (?, ?, ?, ?)
                ''', (
                    shortcut['command_name'],
                    shortcut['shortcut'],
                    shortcut.get('category'),
                    program_name
                ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error importing shortcuts: {e}")
            return False

    def cleanup_duplicates(self):
        """Remove duplicate commands and fix incorrect voice commands"""
        try:
            cursor = self.conn.cursor()
            
            # Fix Record command voice command
            cursor.execute("""
                UPDATE commands 
                SET voice_command = 'record'
                WHERE command_name = 'Record' AND voice_command = 'play'
            """)
            
            # Remove duplicate entries keeping lowest ID
            cursor.execute("""
                DELETE FROM commands 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM commands 
                    GROUP BY command_name
                )
            """)
            
            self.conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error cleaning up database: {e}")
            return False

    def add_command_mapping(self, command_name, voice_command):
        """Add or update a voice command mapping"""
        try:
            cursor = self.conn.cursor()
            
            # First check if command exists
            cursor.execute("""
                SELECT id FROM commands 
                WHERE command_name = ?
            """, (command_name,))
            
            result = cursor.fetchone()
            if result:
                # Update existing command
                cursor.execute("""
                    UPDATE commands 
                    SET voice_command = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE command_name = ?
                """, (voice_command, command_name))
                self.conn.commit()
                print(f"Updated voice command mapping: {command_name} -> {voice_command}")
                return True
            else:
                print(f"Command not found: {command_name}")
                return False
                
        except sqlite3.Error as e:
            print(f"Error adding command mapping: {e}")
            return False

    def cleanup(self):
        """Cleanup database resources"""
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
            print("DEBUG: DB - Connection closed")
        except Exception as e:
            print(f"DEBUG: DB - Error closing: {e}")

    def extract_kbs_command(self, command_text):
        """Extract the primary command word from KBS command text"""
        try:
            # Remove common prefixes/articles
            clean_text = command_text.lower().strip()
            words = clean_text.split()
            
            # First word is our command word
            if words:
                command_word = words[0]
                print(f"DEBUG: DB - Extracted command word: '{command_word}' from '{command_text}'")
                return command_word
            
            return None
            
        except Exception as e:
            print(f"DEBUG: DB - Error extracting command word: {e}")
            return None

    def import_kbs_commands(self, file_path):
        """Import commands from KBS file"""
        try:
            cursor = self.conn.cursor()
            
            # Read and parse KBS file
            with open(file_path, 'r') as f:
                # Assuming KBS file is line-based
                commands = []
                for line in f:
                    if line.strip():
                        # Parse KBS format
                        # Example: "Record New Track|Ctrl+R"
                        parts = line.strip().split('|')
                        if len(parts) >= 2:
                            commands.append({
                                'name': parts[0],
                                'shortcut': parts[1]
                            })
            
            for command in commands:
                command_name = command.get('name', '')
                # Extract command word
                command_word = self.extract_kbs_command(command_name)
                if command_word:
                    cursor.execute("""
                        UPDATE commands 
                        SET voice_command = ? 
                        WHERE command_name = ?
                    """, (command_word, command_name))
                
            self.conn.commit()
            print(f"DEBUG: DB - Imported KBS commands from {file_path}")
            
        except Exception as e:
            print(f"DEBUG: DB - Error importing KBS commands: {e}")
            return False
            
        return True

    def show_all_commands(self):
        """Display all commands in database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT command_name, shortcut, voice_command 
                FROM commands
                ORDER BY command_name
            """)
            
            print("\nCurrent Commands in Database:")
            print("Command Name | Shortcut | Voice Command")
            print("-" * 50)
            for row in cursor.fetchall():
                print(f"{row[0]} | {row[1]} | {row[2]}")
                
        except Exception as e:
            print(f"DEBUG: DB - Error showing commands: {e}")

    def clear_commands(self):
        """Clear all commands from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM commands")
            self.conn.commit()
            print("DEBUG: DB - Database cleared")
            return True
        except Exception as e:
            print(f"DEBUG: DB - Error clearing database: {e}")
            return False
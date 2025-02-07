"""Database backup utility"""
import os
from datetime import datetime
from database import Database

def create_backup():
    """Create a timestamped backup of the database"""
    try:
        # Setup paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        source_db = "studio_one_commands_2025-01-16_21-56.db"
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        backup_dir = f"/Users/jameswatson/Cursor AI Projects/Voice Contrl Project/V1/backups/{timestamp}"
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            print(f"DEBUG: BACKUP - Created directory: {backup_dir}")
        
        # Setup backup path
        backup_path = os.path.join(backup_dir, f"studio_one_commands_{timestamp}.db")
        
        # Initialize database and perform backup
        db = Database(source_db)
        success = db.backup_database(backup_path)
        
        if success:
            print("DEBUG: BACKUP - Database backup successful")
            print(f"DEBUG: BACKUP - Saved to: {backup_path}")
            return True
        else:
            print("DEBUG: BACKUP - Backup failed")
            return False
            
    except Exception as e:
        print(f"DEBUG: BACKUP - Error during backup: {e}")
        return False

if __name__ == "__main__":
    create_backup() 
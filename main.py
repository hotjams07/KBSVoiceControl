"""Main application entry point"""
import tkinter as tk
import sys
from system_init import (
    initialize_database,
    initialize_voice_system,
    initialize_training,
    initialize_gui,
    cleanup_system
)
from database import Database
from speech_recognition import SpeechRecognizer

# Database path configuration
DB_PATH = "studio_one_commands_2025-01-16_21-56.db"  # Simplified path

def main():
    """Main program entry point"""
    database = None
    voice_system = None
    training = None
    gui = None
    
    try:
        print("DEBUG: MAIN - Starting application initialization...")
        
        # 1. Initialize Database
        database = initialize_database(DB_PATH)
        
        # 1b. Import KBS commands
        print("DEBUG: MAIN - Importing KBS commands...")
        success = database.import_kbs_commands('test_commands.kbs')
        if success:
            print("DEBUG: MAIN - KBS commands imported successfully")
        else:
            print("DEBUG: MAIN - Error importing KBS commands")
        
        # 2. Initialize Voice System
        voice_system = initialize_voice_system(database)
        
        # 3. Initialize Training Module
        training = initialize_training(database, voice_system)
        
        # 4. Setup GUI
        root = tk.Tk()
        root.geometry("800x600+300+200")
        root.minsize(600, 400)
        
        # 5. Initialize GUI with dependencies
        gui = initialize_gui(root, database, voice_system, training)
        
        print("DEBUG: MAIN - Initialization complete, starting main loop")
        root.mainloop()
        
    except Exception as e:
        print(f"DEBUG: MAIN - Critical error: {e}")
        sys.exit(1)
        
    finally:
        print("DEBUG: MAIN - Starting cleanup sequence")
        cleanup_system(database, voice_system, training, gui)
        print("DEBUG: MAIN - Application terminated")

if __name__ == "__main__":
    main() 
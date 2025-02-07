import sqlite3
import pyaudio
from vosk import Model, KaldiRecognizer

class CommandTrainer:
    def __init__(self, db_path):
        self.model = Model("vosk-model-small-en-us")
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.audio = pyaudio.PyAudio()
        self.db_path = db_path
        
    def list_commands(self):
        """Display commands that need voice training"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, command_name, shortcut, category, voice_command 
            FROM commands 
            ORDER BY category, command_name
        """)
        commands = cursor.fetchall()
        
        print("\nAvailable Commands:")
        for cmd in commands:
            status = "🗣️" if cmd[4] else "❌"  # voice_command status
            print(f"{cmd[0]}. [{status}] {cmd[1]} ({cmd[2]}) - {cmd[3]}")
            
        conn.close()
        return commands
        
    def record_command(self, command_id):
        """Record and verify a voice command for a specific command ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get command details
        cursor.execute("SELECT command_name, shortcut FROM commands WHERE id = ?", (command_id,))
        command = cursor.fetchone()
        
        if not command:
            print("Command not found!")
            return False
            
        print(f"\nTraining voice command for: {command[0]} (Shortcut: {command[1]})")
        print("Press Enter when ready to speak...")
        input()
        
        # Setup audio stream
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000
        )
        
        print("Listening... (speak your command)")
        
        try:
            data = stream.read(4000, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = eval(self.recognizer.Result())
                command_text = result["text"]
                
                if command_text:
                    print(f"Recognized: '{command_text}'")
                    print("Is this correct? (y/n)")
                    if input().lower() == 'y':
                        cursor.execute("""
                            UPDATE commands 
                            SET voice_command = ?, updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        """, (command_text, command_id))
                        conn.commit()
                        print("Voice command saved!")
                        return True
                    
            print("Failed to recognize command clearly. Try again?")
            return False
            
        finally:
            stream.stop_stream()
            stream.close()
            conn.close()

def main():
    db_path = "/Users/jameswatson/Cursor AI Projects/Voice Contrl Project/V1/backups/2025-01-16_21-56/studio_one_commands_2025-01-16_21-56.db"
    trainer = CommandTrainer(db_path)
    
    while True:
        print("\nVoice Command Trainer")
        print("1. List commands")
        print("2. Train command")
        print("3. Exit")
        
        choice = input("Choose an option: ")
        
        if choice == '1':
            trainer.list_commands()
        elif choice == '2':
            commands = trainer.list_commands()
            if commands:
                cmd_id = input("\nEnter command ID to train: ")
                try:
                    trainer.record_command(int(cmd_id))
                except ValueError:
                    print("Invalid command ID")
        elif choice == '3':
            break

if __name__ == "__main__":
    main() 
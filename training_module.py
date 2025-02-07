from vosk import Model, KaldiRecognizer
import pyaudio
import json
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

class TrainingModule:
    def __init__(self, database, use_neural=False, model=None, recognizer=None):
        """Initialize training module with database connection"""
        self.db = database
        self.use_neural = use_neural and self._check_m1()
        self.neural_engine = NeuralEngine() if self.use_neural else None
        self.training_history = {}
        self.training_in_progress = False
        
        # Use existing model/recognizer if provided
        if model and recognizer:
            self.model = model
            self.recognizer = recognizer
        else:
            self.model = Model("vosk-model-small-en-us")
            self.recognizer = KaldiRecognizer(self.model, 16000)
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
    def clean_text(self, text):
        """Clean up recognized text"""
        try:
            # Remove common articles and clean up text
            words_to_remove = ['the', 'a', 'an', 'to', 'and', 'please', 'now', 'just', 'in']
            
            # Special case handling for known command phrases and common misrecognitions
            known_phrases = {
                'system check': 'systemcheck',
                'system shack': 'systemcheck',  # Add common misrecognition
                'system track': 'systemcheck',  # Add common misrecognition
                'clay': 'play',  # Add common misrecognition
                'just come': 'come'
            }
            
            # First check for known phrases
            text = text.lower().strip()
            for phrase, replacement in known_phrases.items():
                if phrase in text:
                    print(f"Matched phrase: '{text}' -> '{replacement}'")  # Debug print
                    return replacement
            
            # Otherwise clean individual words
            words = text.split()
            cleaned_words = [w for w in words if w not in words_to_remove]
            if not cleaned_words:  # Return None if no words left
                return None
            
            cleaned_text = ' '.join(cleaned_words)
            print(f"Cleaned text: '{text}' -> '{cleaned_text}'")
            return cleaned_text
            
        except Exception as e:
            print(f"Error cleaning text: {e}")
            return None
        
    def detect_training_need(self, spoken_text):
        """Detect if a command needs training"""
        try:
            cleaned_text = self.clean_text(spoken_text)
            if not cleaned_text:
                return False
                
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT command_name, voice_command 
                    FROM commands 
                    WHERE LOWER(voice_command) = LOWER(?)
                """, (cleaned_text,))
                result = cursor.fetchone()
                
                if not result:
                    print(f"Training needed: '{cleaned_text}' not found in commands")
                    return True
                return False
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        except Exception as e:
            print(f"Error in detect_training_need: {e}")
            return False
            
    def start_training_session(self, command_name):
        """Start an interactive training session for a command"""
        print(f"\nStarting training session for: {command_name}")
        print("Please speak the command when ready...")
        
        variations = []
        max_attempts = 3
        
        try:
            # Create a dedicated training stream with new PyAudio instance
            training_audio = pyaudio.PyAudio()
            training_stream = training_audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000
            )
            
            for i in range(max_attempts):
                print(f"\nAttempt {i+1} - Say '{command_name}' now...")
                if self._record_variation(command_name, training_stream):
                    variations.append(self._get_last_recognition())
                    print(f"Variation {i+1} recorded successfully")
                else:
                    print("Failed to record variation, try again")
                
        except Exception as e:
            print(f"Error in training session: {e}")
        finally:
            if 'training_stream' in locals():
                training_stream.stop_stream()
                training_stream.close()
            if 'training_audio' in locals():
                training_audio.terminate()
        
        return variations
        
    def _record_variation(self, command_name, stream):
        """Record a single variation of a command"""
        try:
            print("Listening for variation...")
            data = stream.read(4000, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if result.get("text"):
                    print(f"Recorded: {result['text']}")
                    return True
            return False
            
        except Exception as e:
            print(f"Error recording variation: {e}")
            return False
        
    def _get_last_recognition(self):
        """Get the last recognized text"""
        result = json.loads(self.recognizer.FinalResult())
        return result.get("text", "")
        
    def store_command_variation(self, command_name, variation):
        """Store a new variation of a command"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                # Store the variation
                cursor.execute("""
                    UPDATE commands 
                    SET voice_command = ?,
                        updated_at = CURRENT_TIMESTAMP 
                    WHERE command_name = ?
                """, (variation, command_name))
                conn.commit()
                
                # Update training history
                self.training_history[command_name] = {
                    'last_trained': datetime.now(),
                    'variations': variation
                }
                
                return True
                
        except sqlite3.Error as e:
            print(f"Error storing variation: {e}")
            return False

    def store_command_mapping(self, command_name, voice_command):
        """Store command mapping in database"""
        try:
            # Store in database
            self.db.add_command_mapping(command_name, voice_command)
            
            # If using Neural Engine, enhance recognition
            if self.neural_engine:
                self.neural_engine.enhance_recognition(command_name, voice_command)
                
            return True
        except Exception as e:
            print(f"Error storing command: {e}")
            return False

    def record_single_variation(self, command_name):
        """Record a single variation with feedback"""
        try:
            # Create dedicated audio stream
            training_audio = pyaudio.PyAudio()
            training_stream = training_audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000
            )
            
            # Record for up to 2 seconds
            for _ in range(5):  # 5 attempts at 0.4s each
                data = training_stream.read(4000, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    if result.get("text"):
                        return result["text"]
                    
            return None
            
        except Exception as e:
            print(f"DEBUG: TM - Error recording variation: {e}")
            return None
        finally:
            if 'training_stream' in locals():
                training_stream.stop_stream()
                training_stream.close()
            if 'training_audio' in locals():
                training_audio.terminate() 

    def stop_training(self):
        """Stop training session"""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            print("DEBUG: TM - Training session ended")
        except Exception as e:
            print(f"DEBUG: TM - Error stopping training: {e}")

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
        except Exception as e:
            print(f"Error during cleanup: {e}") 

    def cancel_training(self, dialog):
        try:
            dialog.destroy()
            self.training_in_progress = False
            print("DEBUG: TM - Training cancelled")
        except Exception as e:
            print(f"DEBUG: TM - Error cancelling training: {e}") 

    def start_training(self, command_text):
        """Start training for a new command"""
        try:
            print(f"DEBUG: TRAINING - Starting training for '{command_text}'")
            self.training_in_progress = True
            
            # For now, just acknowledge the training request
            messagebox.showinfo(
                "Training Mode",
                f"Training mode would start here for: {command_text}\n\n"
                "This feature will be implemented in the next version."
            )
            
            self.training_in_progress = False
            
        except Exception as e:
            print(f"DEBUG: TRAINING - Error starting training: {e}")
            self.training_in_progress = False 
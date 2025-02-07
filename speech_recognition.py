from vosk import Model, KaldiRecognizer
import pyaudio
from threading import Thread, Event
import queue
import json
import time
import sqlite3

class SpeechRecognizer:
    def __init__(self, database):
        print("DEBUG: SR - Initializing voice recognition system...")
        self.db = database
        self.model = Model("vosk-model-small-en-us")
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.audio = pyaudio.PyAudio()
        self.mic_index = self._find_microphone()
        self.command_samples = {}  # Store successful command samples
        self.known_commands = set()  # Store known commands
        self.MIN_CONFIDENCE = 50
        self.VARIATION_THRESHOLD = 75  # Higher bar for variations
        self.DIRECT_THRESHOLD = 90    # Clear speech threshold
        self.CLARIFICATION_THRESHOLD = 80  # When to ask for clarification
        self.REJECT_THRESHOLD = 60    # Below this, reject completely
        
        # Load known commands from database
        self.load_known_commands()
        
        print("DEBUG: SR - Setting up microphone...")
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=self.mic_index,
            frames_per_buffer=8000
        )
        print("DEBUG: SR - Microphone configured")
        self.stream.stop_stream()
        self.is_listening = False
        self.command_queue = queue.Queue()
        self.current_phrase = []
        self.last_word_time = 0
        self.last_command_time = 0
        self.command_cooldown = 0.5  # Seconds between commands
        self.state_changes = 0  # Track mic toggles
        
    def _find_microphone(self):
        """Find and remember the microphone index"""
        print("\nAvailable Audio Devices:")
        mac_mic_index = None
        for i in range(self.audio.get_device_count()):
            dev_info = self.audio.get_device_info_by_index(i)
            print(f"Device {i}: {dev_info['name']}")
            if "MacBook Air Microphone" in dev_info['name']:
                mac_mic_index = i
        return mac_mic_index
        
    def microphone_on(self):
        """Turn microphone on"""
        if self.is_listening:
            print("DEBUG: SR - Microphone already on")
            return
        
        print("DEBUG: SR - Turning microphone on")
        self.stream.start_stream()
        self.is_listening = True
        self.state_changes += 1
        print(f"DEBUG: SR - State change #{self.state_changes}")

    def microphone_off(self):
        """Turn microphone off"""
        if not self.is_listening:
            print("DEBUG: SR - Microphone already off")
            return
        
        print("DEBUG: SR - Turning microphone off")
        self.stream.stop_stream()
        self.is_listening = False
        self.state_changes += 1
        print(f"DEBUG: SR - State change #{self.state_changes}")

    def load_known_commands(self):
        """Load known commands from database"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT command_name, voice_command 
                FROM commands 
                WHERE voice_command IS NOT NULL
                AND voice_command != ''
            """)
            
            for row in cursor.fetchall():
                command_name, voice_command = row
                if voice_command:
                    print(f"DEBUG: SR - Loading command: {voice_command} -> {command_name}")
                    self.known_commands.add(voice_command.lower())
                    # Initialize with new structure
                    self.command_samples[voice_command.lower()] = {
                        'samples': [voice_command.lower()],
                        'last_success': time.time(),
                        'success_count': 1,
                        'is_golden': False
                    }
                    
            print(f"DEBUG: SR - Loaded {len(self.known_commands)} known commands")
            
        except Exception as e:
            print(f"DEBUG: SR - Error loading commands: {e}")

    def calculate_confidence(self, text):
        """Calculate confidence score for recognized text"""
        try:
            if not text:
                return 0
                
            text = text.lower()
            
            # Check for golden samples first
            if text in self.command_samples and self.command_samples[text]['is_golden']:
                return 100

            # Check similarity with stored samples
            best_score = 0
            for command, data in self.command_samples.items():
                if data['samples']:
                    for sample in data['samples']:
                        similarity = self.calculate_similarity(text, sample)
                        best_score = max(best_score, similarity)
                
            print(f"DEBUG: SR - Best similarity score for '{text}': {best_score}")
            return best_score

        except Exception as e:
            print(f"DEBUG: SR - Error calculating confidence: {e}")
            return 0

    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two texts"""
        try:
            text1 = text1.lower()
            text2 = text2.lower()
            
            if text1 == text2:
                return 100
                
            # Check if one is contained in the other
            if text1 in text2 or text2 in text1:
                return 75
                
            # Stricter character matching
            matches = 0
            total = max(len(text1), len(text2))
            for i in range(min(len(text1), len(text2))):
                if text1[i] == text2[i]:
                    matches += 1
                else:
                    # Penalize differences more
                    matches -= 0.5
                    
            score = (matches / total) * 100
            return max(0, score)  # Don't return negative scores
            
        except Exception as e:
            print(f"DEBUG: SR - Error calculating similarity: {e}")
            return 0

    def check_variations(self, text):
        """Check if text matches any known variations"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT command_name, voice_command 
                FROM commands 
                WHERE voice_command IS NOT NULL
            """)
            
            best_match = None
            best_score = 0
            
            for row in cursor.fetchall():
                command_name, voice_command = row
                similarity = self.calculate_similarity(text, voice_command)
                if similarity > best_score:
                    best_score = similarity
                    best_match = command_name
                    
            return best_match if best_score >= self.VARIATION_THRESHOLD else None
            
        except Exception as e:
            print(f"DEBUG: SR - Error checking variations: {e}")
            return None

    def get_next_command(self):
        """Check for and process next command"""
        if not self.is_listening or not self.stream:
            return None
            
        try:
            data = self.stream.read(4000, exception_on_overflow=False)
            
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip()
                
                if text:
                    current_time = time.time()
                    if current_time - self.last_command_time < self.command_cooldown:
                        return None  # Too soon after last command
                    
                    print(f"DEBUG: SR - Raw text: {text}")
                    
                    # Clean and separate commands
                    words = text.lower().split()
                    # Remove common articles and clean text
                    cleaned_words = []
                    i = 0
                    while i < len(words):
                        if words[i] not in ['the', 'a', 'an', 'to', 'and']:
                            # Check for two-word commands
                            if i + 1 < len(words):
                                pair = f"{words[i]} {words[i+1]}"
                                if self.is_known_command(pair):
                                    cleaned_words.append(pair)
                                    i += 2
                                    continue
                            cleaned_words.append(words[i])
                        i += 1
                    
                    # Take first potential command
                    if cleaned_words:
                        cleaned_text = cleaned_words[0]
                        print(f"DEBUG: SR - Cleaned command: {cleaned_text}")
                    
                    # Calculate confidence and check samples
                    confidence_score = self.calculate_confidence(cleaned_text)
                    print(f"DEBUG: SR - Confidence: {confidence_score}%")
                    
                    if confidence_score >= self.DIRECT_THRESHOLD:
                        # Store successful recognition
                        self.store_successful_sample(cleaned_text)
                        self.last_command_time = current_time
                        return {'voice_text': cleaned_text, 'confidence': confidence_score}
                        
                    elif confidence_score >= self.CLARIFICATION_THRESHOLD:
                        # Find closest matching command
                        closest_match = self.find_closest_command(cleaned_text)
                        if closest_match:
                            return {
                                'voice_text': cleaned_text,
                                'confidence': confidence_score,
                                'needs_training': True,
                                'suggested_match': closest_match
                            }
                            
                    elif confidence_score >= self.VARIATION_THRESHOLD:
                        # Check variations
                        mapped_command = self.check_variations(cleaned_text)
                        if mapped_command:
                            self.last_command_time = current_time
                            return {'voice_text': mapped_command, 'confidence': confidence_score}
                            
                    elif confidence_score >= self.MIN_CONFIDENCE:
                        # Potential training candidate
                        self.last_command_time = current_time
                        return {'voice_text': cleaned_text, 'confidence': confidence_score, 'needs_training': True}
                
        except Exception as e:
            print(f"DEBUG: SR - Error reading audio: {e}")
            
        return None

    def store_successful_sample(self, text):
        """Store successful recognition sample"""
        try:
            text = text.lower()
            current_time = time.time()
            
            # Initialize storage for this command if needed
            if text not in self.command_samples:
                self.command_samples[text] = {
                    'samples': [],
                    'last_success': current_time,
                    'success_count': 0,
                    'is_golden': False
                }
            
            command_data = self.command_samples[text]
            
            # Check if this is consistent with existing samples
            is_consistent = True
            for sample in command_data['samples']:
                if self.calculate_similarity(text, sample) < 85:
                    is_consistent = False
                    break
            
            if is_consistent:
                if len(command_data['samples']) < 4:  # Keep up to 4 samples
                    command_data['samples'].append(text)
                    command_data['success_count'] += 1
                    command_data['last_success'] = current_time
                    
                    # Mark as golden sample after 3 successful recognitions
                    if command_data['success_count'] >= 3:
                        command_data['is_golden'] = True
                        
                    print(f"DEBUG: SR - Stored sample for '{text}' (Success #{command_data['success_count']})")
                    if command_data['is_golden']:
                        print(f"DEBUG: SR - '{text}' is now a golden sample!")
            else:
                print(f"DEBUG: SR - Sample for '{text}' inconsistent with existing samples")
                
        except Exception as e:
            print(f"DEBUG: SR - Error storing sample: {e}")

    def cleanup(self):
        """Only called on program exit"""
        print("DEBUG: SR - Cleaning up voice system")
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

    def is_known_command(self, text):
        """Check if text matches any known command"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT 1 FROM commands 
                WHERE LOWER(command_name) = LOWER(?) 
                OR LOWER(voice_command) = LOWER(?)
            """, (text, text))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"DEBUG: SR - Error checking known command: {e}")
            return False 

    def find_closest_command(self, text):
        """Find the closest matching command"""
        try:
            best_match = None
            best_score = 0
            
            for command in self.known_commands:
                similarity = self.calculate_similarity(text, command)
                # Print all potential matches for debugging
                if similarity >= self.CLARIFICATION_THRESHOLD:
                    print(f"DEBUG: SR - Potential match: '{command}' ({similarity}%)")
                if similarity > best_score:
                    best_score = similarity
                    best_match = command
                    
            print(f"DEBUG: SR - Closest match for '{text}': {best_match} ({best_score}%)")
            # Return match if score is good enough
            return best_match if best_score >= self.CLARIFICATION_THRESHOLD else None
            
        except Exception as e:
            print(f"DEBUG: SR - Error finding closest command: {e}")
            return None 
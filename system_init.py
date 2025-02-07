"""System initialization and cleanup module"""
import tkinter as tk
from database import Database
from speech_recognition import SpeechRecognizer
from training_module import TrainingModule
from gui_viewer import DatabaseGUI

def initialize_database(db_path):
    """Initialize database system"""
    print("DEBUG: INIT - Setting up database...")
    try:
        database = Database(db_path)
        database.initialize()
        print("DEBUG: INIT - Database ready")
        return database
    except Exception as e:
        print(f"DEBUG: INIT - Database initialization failed: {e}")
        raise

def initialize_voice_system(database):
    """Initialize voice recognition system"""
    print("DEBUG: INIT - Setting up voice recognition...")
    try:
        voice_system = SpeechRecognizer(database)
        print("DEBUG: INIT - Voice system ready")
        return voice_system
    except Exception as e:
        print(f"DEBUG: INIT - Voice system initialization failed: {e}")
        raise

def initialize_training(database, voice_system):
    """Initialize training module"""
    print("DEBUG: INIT - Setting up training module...")
    try:
        training = TrainingModule(
            database,
            use_neural=False,
            model=voice_system.model,
            recognizer=voice_system.recognizer
        )
        print("DEBUG: INIT - Training module ready")
        return training
    except Exception as e:
        print(f"DEBUG: INIT - Training initialization failed: {e}")
        raise

def initialize_gui(root, database, voice_system, training):
    """Initialize GUI system"""
    print("DEBUG: INIT - Setting up GUI...")
    try:
        gui = DatabaseGUI(root, database, voice_system, training)
        print("DEBUG: INIT - GUI ready")
        return gui
    except Exception as e:
        print(f"DEBUG: INIT - GUI initialization failed: {e}")
        raise

def cleanup_system(database, voice_system, training, gui):
    """Clean shutdown of all systems"""
    print("DEBUG: CLEANUP - Starting system shutdown...")
    
    # 1. GUI Cleanup
    try:
        print("DEBUG: CLEANUP - Shutting down GUI...")
        if gui:
            gui.cleanup()
    except Exception as e:
        print(f"DEBUG: CLEANUP - GUI cleanup error: {e}")

    # 2. Training Module Cleanup
    try:
        print("DEBUG: CLEANUP - Shutting down training module...")
        if training:
            training.cleanup()
    except Exception as e:
        print(f"DEBUG: CLEANUP - Training cleanup error: {e}")

    # 3. Voice System Cleanup
    try:
        print("DEBUG: CLEANUP - Shutting down voice system...")
        if voice_system:
            voice_system.cleanup()
    except Exception as e:
        print(f"DEBUG: CLEANUP - Voice system cleanup error: {e}")

    # 4. Database Cleanup
    try:
        print("DEBUG: CLEANUP - Shutting down database...")
        if database:
            database.cleanup()
    except Exception as e:
        print(f"DEBUG: CLEANUP - Database cleanup error: {e}")

    print("DEBUG: CLEANUP - System shutdown complete") 
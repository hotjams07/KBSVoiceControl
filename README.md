<<<<<<< HEAD
# Voice Control System

## Overview
A voice-controlled command system with stable voice recognition, database management, and GUI interface.

## Current Status
- ✓ Stable core system
- ✓ Working voice recognition
- ✓ Clean microphone control
- ✓ Command database integration

## Key Features
- Single voice system instance (no restarts)
- Microphone toggle control
- Command highlighting
- Status feedback
- Clean error handling

## System Requirements
- Python 3.x
- Vosk speech recognition model
- SQLite database
- Tkinter for GUI

## Installation
1. Clone repository
2. Install dependencies:
   ```bash
   pip install vosk
   pip install pyaudio
   ```
3. Place Vosk model in project directory
4. Run: `python3 main.py`

## Usage
1. Launch application
2. Click "Turn Microphone On"
3. Speak commands (e.g., "play", "stop", "record")
4. Commands are highlighted in the interface
5. Click "Turn Microphone Off" when done

## Project Structure
```
Voice Control System/
├── main.py              # Entry point
├── system_init.py       # System initialization
├── gui_viewer.py        # GUI interface
├── speech_recognition.py # Voice processing
├── training_module.py   # Command training
└── database.py         # Data management
```

## Debug Messages
The system provides clear debug output:
```
DEBUG: MAIN - Starting application...
DEBUG: INIT - Setting up components...
DEBUG: GUI - Processing commands...
```

## Known Issues
- None currently blocking
- System is stable for core functions

## Next Steps
- Additional command training
- Custom shortcuts
- Command categories
- Workflow automation

## Contributing
Project is in active development. Current focus is on stability and core functionality.

## License
[Your License Here] 
=======
# KBSVoiceControl
>>>>>>> 53cf0239c832c75cf0614f0f616e90d4db91541d

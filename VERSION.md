# KBSVoiceControl Version History

Version 1.0.0 (2025-02-07)
Features:
- Voice command recognition and execution
- Studio One Keyscheme (.keyscheme) file import/parsing
- SQLite command database
- GUI interface with:
  - Microphone control
  - Command list view
  - Search functionality
  - Add/Edit/Delete commands
- Training module for new commands

Technical Details:
- Python 3.x
- Tkinter GUI
- SQLite database
- Vosk speech recognition

Core Components:
- gui_viewer.py (Main interface)
- database.py (Data management)
- speech_recognition.py (Voice control)
- training_module.py (Command learning)

Administration:
- Database Management:
  - Backup/restore (admin only)
  - Clear database (admin only)
  - Access password required
- Import Controls:
  - Validation checks
  - Conflict detection
  - Backup before import

Repository Information:
- GitHub: https://github.com/hotjams07/KBSVoiceControl
- Initial Upload: 2025-02-07
- Primary Development: MacBook Air

Development Environment Plans:
- Current: MacBook Air M1
  - 16GB RAM
  - 2TB SSD
  - 13" Display
  - Travel/Secondary Role

- Planned: MacBook Air M4
  - 32GB RAM
  - 2TB Storage
  - 15" Display
  - Primary Development Machine
  - Better visibility for development

Status: Stable working version 

Recent Changes:
- Added XML parsing for .keyscheme files
- Updated database schema
- Improved file format handling
- Added clear database for imports 
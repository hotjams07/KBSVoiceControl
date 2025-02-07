import platform
from database import Database

class ShortcutValidator:
    # System shortcuts that should never be overridden
    SYSTEM_SHORTCUTS = {
        'mac': [
            {'shortcut': 'Cmd+Q', 'description': 'Quit Application'},
            {'shortcut': 'Cmd+W', 'description': 'Close Window'},
            {'shortcut': 'Cmd+Tab', 'description': 'Switch Applications'},
            {'shortcut': 'Cmd+Space', 'description': 'Spotlight Search'},
            # Add more Mac shortcuts
        ],
        'windows': [
            {'shortcut': 'Alt+F4', 'description': 'Close Application'},
            {'shortcut': 'Win+D', 'description': 'Show Desktop'},
            {'shortcut': 'Ctrl+Alt+Delete', 'description': 'Task Manager'},
            # Add more Windows shortcuts
        ]
    }
    
    @staticmethod
    def is_system_shortcut(shortcut):
        """Check if shortcut is a system shortcut"""
        import platform
        system = 'mac' if platform.system() == 'Darwin' else 'windows'
        
        for sys_shortcut in ShortcutValidator.SYSTEM_SHORTCUTS[system]:
            if shortcut == sys_shortcut['shortcut']:
                return True, sys_shortcut['description']
        return False, None 
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import Database
import sqlite3
from speech_recognition import SpeechRecognizer
import os
from training_module import TrainingModule
import time

class DatabaseGUI:
    def __init__(self, root, database, speech_recognizer, training_module):
        """Initialize GUI with dependencies"""
        self.root = root
        self.root.title("Studio One Commands Viewer")
        self.db = database
        self.speech_recognizer = speech_recognizer
        self.training_module = training_module
        
        # Setup GUI
        self.setup_gui()
        
        # Initialize state
        self.training_in_progress = False

    def setup_gui(self):
        """Setup main GUI components"""
        self.root.resizable(True, True)
        print("DEBUG: GUI - Configuring interface components...")
        
        # Configure main window
        self.root.geometry("800x600")  # Set initial size
        self.root.minsize(600, 400)    # Set minimum size
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky='nsew')
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.show_status("Initializing interface...")
        
        # Top control frame for buttons and search
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        # Import KBS button
        self.import_btn = ttk.Button(control_frame, text="Import KBS File", command=self.import_kbs_file)
        self.import_btn.pack(side=tk.LEFT, padx=5)
        
        # Microphone control button
        self.voice_btn = ttk.Button(control_frame, text="Turn Microphone On", command=self.toggle_voice_control)
        self.voice_btn.pack(side=tk.LEFT, padx=5)
        self.voice_active = False  # Initialize microphone state
        
        # Search frame
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_records)  # Connect search
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Tree view in its own frame
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=0)  # For status bar
        self.root.grid_columnconfigure(0, weight=1)
        
        print("DEBUG: GUI - Interface configuration complete")
        self.show_status("Interface ready")
        
        # Create Treeview
        self.tree = ttk.Treeview(tree_frame, columns=(
            'id', 'command_name', 'shortcut', 'category', 
            'voice_command', 'conflict_flag', 'conflict_type', 
            'conflict_with', 'created_at', 'updated_at'
        ), show='headings')
        
        # Define column headings
        columns = {
            'id': 'ID',
            'command_name': 'Command Name',
            'shortcut': 'Shortcut',
            'category': 'Category',
            'voice_command': 'Voice Command',
            'conflict_flag': 'Conflict',
            'conflict_type': 'Conflict Type',
            'conflict_with': 'Conflicts With',
            'created_at': 'Created',
            'updated_at': 'Updated'
        }
        
        # Set column headings and widths
        for col, heading in columns.items():
            self.tree.heading(col, text=heading, 
                            command=lambda c=col: self.sort_column(c))  # Add sorting
            self.tree.column(col, width=100, minwidth=50)  # Add minimum width
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bottom button frame
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Refresh", command=self.refresh_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add New", command=self.show_add_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit", command=self.edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Quit", command=self.on_closing).pack(side=tk.LEFT, padx=5)
        
        # Configure window close button (X)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize tags for search highlighting
        self.setup_tags()
        
        # Setup keyboard bindings
        self.setup_bindings()
        
        # Add right-click menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_selected)
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Bind keyboard shortcuts
        self.root.bind('<Command-q>', lambda e: self.root.quit())  # Quit
        self.root.bind('<Command-r>', lambda e: self.refresh_data())  # Refresh
        self.root.bind('<Command-n>', lambda e: self.show_add_dialog())  # New
        self.root.bind('<Command-f>', lambda e: self.focus_search())  # Focus search
        self.root.bind('<Delete>', lambda e: self.delete_selected())  # Delete

        # Load initial data
        print("DEBUG: GUI - Loading command database...")
        self.refresh_data()
        print("DEBUG: GUI - Database loaded")

    def refresh_data(self, search_text=''):
        print("DEBUG: GUI - Refreshing command list...")
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            cursor = self.db.conn.cursor()
            print(f"DEBUG: GUI - Using database at: {self.db.db_path}")
            
            if search_text:
                cursor.execute('''
                    SELECT * FROM commands 
                    WHERE LOWER(command_name) LIKE ? 
                    OR LOWER(shortcut) LIKE ? 
                    OR LOWER(category) LIKE ?
                    OR LOWER(voice_command) LIKE ?
                ''', (f'%{search_text}%', f'%{search_text}%', 
                     f'%{search_text}%', f'%{search_text}%'))
            else:
                cursor.execute('SELECT * FROM commands')
                
            rows = cursor.fetchall()
            print(f"DEBUG: GUI - Found {len(rows)} commands")
            
            for row in rows:
                self.tree.insert('', tk.END, values=row)
                
            print("DEBUG: GUI - Command list updated")
            self.show_status(f"Loaded {len(rows)} commands")
            
        except Exception as e:
            print(f"DEBUG: GUI - Error loading commands from {self.db.db_path}: {e}")
            self.show_status("Error loading commands")
    
    def show_add_dialog(self):
        """Show dialog to add new command"""
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("Add New Command")
            dialog.geometry("400x300")
            dialog.transient(self.root)
            
            # Command Name
            ttk.Label(dialog, text="Command Name:").grid(row=0, column=0, padx=5, pady=5)
            name_var = tk.StringVar()
            name_entry = ttk.Entry(dialog, textvariable=name_var)
            name_entry.grid(row=0, column=1, padx=5, pady=5)
            
            # Shortcut section
            shortcut_frame = ttk.LabelFrame(dialog, text="Shortcut")
            shortcut_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
            
            # Key input first
            ttk.Label(shortcut_frame, text="Key:").pack(side=tk.LEFT, padx=5)
            key_var = tk.StringVar()
            key_entry = ttk.Entry(shortcut_frame, textvariable=key_var, width=10)
            key_entry.pack(side=tk.LEFT, padx=5)
            ttk.Button(shortcut_frame, text="Clear Key", 
                      command=lambda: key_var.set("")).pack(side=tk.LEFT, padx=5)
            
            # Modifier checkboxes
            modifier_frame = ttk.LabelFrame(dialog, text="Modifiers")
            modifier_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
            
            # Create a frame for checkboxes to keep them aligned
            checkbox_frame = ttk.Frame(modifier_frame)
            checkbox_frame.pack(side=tk.LEFT, padx=5, pady=5)
            
            ctrl_var = tk.BooleanVar()
            shift_var = tk.BooleanVar()
            alt_var = tk.BooleanVar()
            cmd_var = tk.BooleanVar()
            
            def update_shortcut(*args):
                mods = []
                if ctrl_var.get(): mods.append("Ctrl")
                if shift_var.get(): mods.append("Shift")
                if alt_var.get(): mods.append("Alt")
                if cmd_var.get(): mods.append("Cmd")
                key = key_var.get().strip()
                shortcut = "+".join(mods) + ("+" + key if key else "")
                shortcut_preview.set(shortcut)
            
            # Add checkboxes in a grid for better alignment
            ttk.Checkbutton(checkbox_frame, text="Ctrl", variable=ctrl_var, 
                           command=update_shortcut).grid(row=0, column=0, padx=5)
            ttk.Checkbutton(checkbox_frame, text="Shift", variable=shift_var,
                           command=update_shortcut).grid(row=0, column=1, padx=5)
            ttk.Checkbutton(checkbox_frame, text="Alt", variable=alt_var,
                           command=update_shortcut).grid(row=0, column=2, padx=5)
            ttk.Checkbutton(checkbox_frame, text="Cmd", variable=cmd_var,
                           command=update_shortcut).grid(row=0, column=3, padx=5)
            
            # Add clear all button with some spacing
            ttk.Button(modifier_frame, text="Clear All", command=lambda: [
                var.set(False) for var in [ctrl_var, shift_var, alt_var, cmd_var]
            ]).pack(side=tk.RIGHT, padx=10)
            
            # Preview
            shortcut_preview = tk.StringVar()
            ttk.Label(shortcut_frame, textvariable=shortcut_preview).pack(side=tk.LEFT, padx=20)
            
            # Voice Command
            ttk.Label(dialog, text="Voice Command:").grid(row=3, column=0, padx=5, pady=5)
            voice_var = tk.StringVar()
            voice_entry = ttk.Entry(dialog, textvariable=voice_var)
            voice_entry.grid(row=3, column=1, padx=5, pady=5)
            
            def save_command():
                try:
                    name = name_var.get().strip()
                    shortcut = shortcut_preview.get()
                    voice = voice_var.get().strip()
                    
                    if not name:
                        messagebox.showerror("Error", "Command name is required")
                        return
                        
                    # Check if command already exists
                    cursor = self.db.conn.cursor()
                    cursor.execute("SELECT 1 FROM commands WHERE command_name = ?", (name,))
                    if cursor.fetchone():
                        messagebox.showerror("Error", "Command already exists")
                        return
                        
                    # Add new command
                    cursor.execute("""
                        INSERT INTO commands (command_name, shortcut, voice_command)
                        VALUES (?, ?, ?)
                    """, (name, shortcut, voice))
                    self.db.conn.commit()
                    
                    dialog.destroy()
                    self.refresh_data()
                    self.show_status(f"Added command: {name}")
                    
                except Exception as e:
                    print(f"DEBUG: GUI - Error adding command: {e}")
                    messagebox.showerror("Error", f"Failed to add command: {e}")
            
            # Buttons
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=4, column=0, columnspan=2, pady=20)
            
            ttk.Button(button_frame, text="Save", command=save_command).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            # Focus first field
            name_entry.focus_set()
            
        except Exception as e:
            print(f"DEBUG: GUI - Error showing add dialog: {e}")
            messagebox.showerror("Error", "Failed to show add dialog")

    def sort_column(self, col):
        """Sort tree contents when a column header is clicked"""
        # Get all items
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        # Sort items
        items.sort(reverse=self.tree.heading(col).get('reverse', False))
        
        # Rearrange items in sorted positions
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
            
        # Reverse sort next time
        self.tree.heading(col, reverse=not self.tree.heading(col).get('reverse', False))

    def filter_records(self, *args):
        """Filter records based on search text"""
        search_text = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM commands 
                    WHERE LOWER(command_name) LIKE ? 
                    OR LOWER(shortcut) LIKE ? 
                    OR LOWER(voice_command) LIKE ?
                """, (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"))
                
                for row in cursor.fetchall():
                    self.tree.insert('', 'end', values=row)
                    
        except Exception as e:
            print(f"DEBUG: GUI - Error filtering records: {e}")

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            
    def edit_selected(self):
        """Edit selected command"""
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        values = self.tree.item(item)['values']
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Command")
        dialog.geometry("400x300")
        dialog.transient(self.root)  # Make dialog modal
        
        # Create and pack form fields with existing values
        ttk.Label(dialog, text="Command Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.insert(0, values[1])
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Shortcut:").pack(pady=5)
        shortcut_entry = ttk.Entry(dialog)
        shortcut_entry.insert(0, values[2] or '')
        shortcut_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Category:").pack(pady=5)
        category_entry = ttk.Entry(dialog)
        category_entry.insert(0, values[3] or '')
        category_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Voice Command:").pack(pady=5)
        voice_entry = ttk.Entry(dialog)
        voice_entry.insert(0, values[4] or '')
        voice_entry.pack(pady=5)
        
        def save_edit():
            # Add update_command method to Database class first
            db = Database()
            db.update_command(
                values[0],  # ID
                name_entry.get(),
                shortcut_entry.get() or None,
                category_entry.get() or None,
                voice_entry.get() or None
            )
            dialog.destroy()
            self.refresh_data()
            
        ttk.Button(dialog, text="Save", command=save_edit).pack(pady=20)
        
    def delete_selected(self):
        """Delete selected command"""
        selected = self.tree.selection()
        if not selected:
            return
            
        if messagebox.askyesno("Confirm Delete", 
                              "Are you sure you want to delete this command?"):
            try:
                item = selected[0]
                values = self.tree.item(item)['values']
                self.db.delete_command(values[0])  # Delete by ID
                self.refresh_data()
                self.show_status("Command deleted successfully")
            except Exception as e:
                print(f"DEBUG: GUI - Error deleting command: {e}")
                messagebox.showerror("Error", f"Failed to delete command: {e}")

    def focus_search(self):
        """Focus the search entry"""
        self.search_entry.focus_set()

    def validate_command(self, command_name, shortcut=None):
        """Validate command data before saving"""
        if not command_name:
            tk.messagebox.showerror("Error", "Command name is required")
            return False
            
        # Check for duplicate shortcuts
        if shortcut:
            db = Database()
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT command_name FROM commands WHERE shortcut = ?', (shortcut,))
                existing = cursor.fetchone()
                if existing:
                    return tk.messagebox.askyesno(
                        "Shortcut Conflict",
                        f"Shortcut '{shortcut}' is already used by '{existing[0]}'. Use anyway?"
                    )
        return True

    def show_status(self, message):
        """Update status bar message"""
        try:
            self.status_var.set(message)
            print(f"DEBUG: GUI - Status: {message}")
        except Exception as e:
            print(f"DEBUG: GUI - Error updating status: {e}")

    def highlight_matches(self, item, search_text):
        """Highlight matching text in tree view"""
        if not search_text:
            return
            
        # Get item values
        values = self.tree.item(item)['values']
        
        # If match found, apply a tag
        for idx, value in enumerate(values):
            if value and search_text.lower() in str(value).lower():
                self.tree.item(item, tags=('match',))  # Use item() instead of tag_add
                break
                
    def setup_tags(self):
        """Setup tags for tree items"""
        self.tree.tag_configure('match', background='yellow')

    def setup_bindings(self):
        """Setup additional keyboard bindings"""
        self.tree.bind('<Return>', lambda e: self.edit_selected())
        self.tree.bind('<Double-1>', lambda e: self.edit_selected())
        self.root.bind('<Control-f>', lambda e: self.focus_search())
        self.root.bind('<Escape>', lambda e: self.clear_search())

    def clear_search(self):
        """Clear the search entry"""
        self.search_var.set('')
        self.search_entry.focus_set()

    def refresh_view(self):
        """Refresh the treeview after import"""
        self.tree.delete(*self.tree.get_children())
        
        # Get all shortcuts from database
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT command_name, shortcut, category, program_name FROM commands')
            for row in cursor.fetchall():
                self.tree.insert('', 'end', values=row)

    def toggle_voice_control(self):
        """Toggle microphone on/off"""
        try:
            if not hasattr(self, 'last_toggle_time'):
                self.last_toggle_time = 0
            
            current_time = time.time()
            if current_time - self.last_toggle_time < 1.0:  # 1 second cooldown
                print("DEBUG: GUI - Toggle too fast, ignoring")
                return
            
            if self.voice_active:
                print("DEBUG: GUI - Turning microphone off...")
                self.voice_active = False
                self.voice_btn.configure(text="Turn Microphone On", state="disabled")
                if self.speech_recognizer:
                    self.speech_recognizer.microphone_off()
                self.show_status("Microphone off")
                self.voice_btn.configure(state="normal")
            else:
                print("DEBUG: GUI - Turning microphone on...")
                if not self.speech_recognizer:
                    raise Exception("Voice system not initialized")
                self.speech_recognizer.microphone_on()
                self.voice_btn.configure(text="Turn Microphone Off")
                self.show_status("Microphone on")
                self.voice_active = True
                self.check_voice_commands()
            
            self.last_toggle_time = current_time
            
        except Exception as e:
            print(f"DEBUG: GUI - Error toggling microphone: {e}")
            self.show_status(f"Microphone error: {e}")
            self.voice_active = False
            self.voice_btn.configure(text="Turn Microphone On", state="normal")

    def check_voice_commands(self):
        """Check for and process voice commands"""
        if self.root.winfo_exists():  # Only if window exists
            try:
                if not self.voice_active or self.training_in_progress:
                    if self.voice_active:  # Only schedule if still active
                        self.root.after(100, self.check_voice_commands)
                    return
                
                command = self.speech_recognizer.get_next_command()
                if command:
                    print(f"DEBUG: GUI - Processing command data: {command}")
                    self.process_voice_command(command)
                    
            except Exception as e:
                print(f"DEBUG: GUI - Error in command check: {e}")
            
            if self.voice_active:  # Only schedule next check if still active
                self.root.after(100, self.check_voice_commands)

    def process_voice_command(self, command_data):
        """Process a recognized voice command"""
        try:
            # Handle suggestion first
            if isinstance(command_data, dict) and 'suggested_match' in command_data:
                suggestion = command_data['suggested_match']
                response = messagebox.askyesno(
                    "Command Suggestion",
                    f"Did you mean '{suggestion}' when you said '{command_data['voice_text']}'?\n\n"
                    f"Yes - Use suggested command\n"
                    f"No - Train new command"
                )
                if response:
                    return self.process_voice_command({'voice_text': suggestion})
                else:
                    self.training_module.start_training(command_data['voice_text'])
                    return True

            # Get the text to process
            text = command_data.get('voice_text') if isinstance(command_data, dict) else command_data

            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT command_name 
                    FROM commands 
                    WHERE LOWER(voice_command) = LOWER(?)
                """, (text,))
                result = cursor.fetchone()
                
                if result:
                    command_name = result[0]
                    print(f"DEBUG: GUI - Executing command: {command_name}")
                    self.show_status(f"Executed: {command_name}")
                    self.highlight_command(command_name)
                    return True
                else:
                    print(f"DEBUG: GUI - Command not found: '{text}'")
                    self.show_status(f"Unknown command: {text}")
                    return False
                
        except Exception as e:
            print(f"DEBUG: GUI - Error processing command: {e}")
            return False

    def safe_offer_training(self, text):
        """Safely offer training dialog"""
        try:
            if self.voice_active:
                self.offer_training(text)
        except Exception as e:
            print(f"DEBUG: GUI - Error offering training: {e}")
            self.show_status(f"Training error: {e}")
        finally:
            self.training_in_progress = False

    def highlight_command(self, command_name):
        """Highlight a command in the tree"""
        for item in self.tree.get_children():
            if self.tree.item(item)['values'][1] == command_name:
                self.tree.selection_set(item)
                self.tree.see(item)
                break

    def offer_training(self, spoken_text):
        """Show enhanced training dialog"""
        if not self.root.winfo_exists():
            return
        
        try:
            # Stop listening while training
            self.speech_recognizer.stop()
            print("Starting training dialog...")
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Voice Command Training")
            dialog.geometry("400x300")
            
            # Ensure dialog gets cleaned up if closed
            dialog.protocol("WM_DELETE_WINDOW", 
                           lambda: self.cancel_training(dialog))
            
            # Style
            style = ttk.Style()
            style.configure("Training.TLabel", font=("Helvetica", 12))
            style.configure("Status.TLabel", foreground="blue")
            
            # Main message
            ttk.Label(dialog, 
                     text=f"New Command Detected: '{spoken_text}'",
                     style="Training.TLabel").pack(pady=10)
            
            # Status indicator
            status_var = tk.StringVar(value="Ready to start training...")
            status_label = ttk.Label(dialog, textvariable=status_var, 
                                   style="Status.TLabel")
            status_label.pack(pady=5)
            
            # Progress frame
            progress_frame = ttk.LabelFrame(dialog, text="Training Progress")
            progress_frame.pack(padx=10, pady=10, fill="x")
            
            # Progress indicators
            progress_vars = []
            progress_labels = []
            for i in range(3):
                var = tk.StringVar(value="⚪")  # Empty circle
                progress_vars.append(var)
                label = ttk.Label(progress_frame, textvariable=var)
                label.pack(side="left", padx=20, pady=5)
                progress_labels.append(label)
                
            def update_progress(step):
                progress_vars[step].set("🟢")  # Filled circle
                dialog.update()
                
            def start_training():
                try:
                    status_var.set("Training in progress... Please speak when prompted")
                    variations = []
                    
                    for i in range(3):
                        status_var.set(f"Please say '{spoken_text}' (Attempt {i+1}/3)")
                        dialog.update()
                        
                        variation = self.training_module.record_single_variation(spoken_text)
                        if variation:
                            variations.append(variation)
                            update_progress(i)
                            status_var.set(f"Recorded variation {i+1}")
                        else:
                            status_var.set("Failed to record. Please try again.")
                            continue
                    
                    if variations:
                        status_var.set("Training complete! Select a command to map to...")
                        self.select_command_mapping(spoken_text, variations, dialog)
                    else:
                        status_var.set("Training failed. Please try again.")
                    
                except Exception as e:
                    print(f"Error in training: {e}")
                    status_var.set("Error during training")
                    
            # Buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(side="bottom", pady=20)
            
            ttk.Button(button_frame, text="Start Training", 
                      command=start_training).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Cancel", 
                      command=lambda: self.cancel_training(dialog)).pack(side="left", padx=5)
            
        except Exception as e:
            print(f"Error in training dialog: {e}")
            self.training_in_progress = False
            self.speech_recognizer.start_listening()

    def select_command_mapping(self, spoken_text, variations, parent_dialog):
        """Enhanced command mapping dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Map Voice Command")
        dialog.geometry("500x400")
        
        # Instructions
        ttk.Label(dialog, 
                 text="Select the Studio One command that matches your voice command:",
                 wraplength=450).pack(pady=10)
                 
        # Command details
        details_frame = ttk.LabelFrame(dialog, text="Voice Command Details")
        details_frame.pack(padx=10, pady=5, fill="x")
        
        ttk.Label(details_frame, 
                 text=f"Voice Command: {spoken_text}").pack(pady=5)
        ttk.Label(details_frame,
                 text=f"Variations Recorded: {len(variations)}").pack(pady=5)
        
        # Search frame
        search_frame = ttk.Frame(dialog)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Command list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        commands_list = tk.Listbox(list_frame, height=10)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", 
                                 command=commands_list.yview)
        commands_list.configure(yscrollcommand=scrollbar.set)
        
        commands_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate and filter commands
        all_commands = self.get_available_commands()
        def filter_commands(*args):
            search_text = search_var.get().lower()
            commands_list.delete(0, tk.END)
            for cmd in all_commands:
                if search_text in cmd.lower():
                    commands_list.insert(tk.END, cmd)
                
        search_var.trace("w", filter_commands)
        filter_commands()  # Initial population
        
        def save_mapping():
            if commands_list.curselection():
                selected_command = commands_list.get(commands_list.curselection())
                self.training_module.store_command_variation(selected_command, spoken_text)
                self.show_status(f"Command '{spoken_text}' mapped to {selected_command}")
                dialog.destroy()
                parent_dialog.destroy()
                self.training_in_progress = False
                self.speech_recognizer.start_listening()
            
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side="bottom", pady=10)
        
        ttk.Button(button_frame, text="Save Mapping", 
                  command=save_mapping).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel",
                  command=dialog.destroy).pack(side="left", padx=5)

    def get_available_commands(self):
        """Get list of available commands for mapping"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT command_name FROM commands ORDER BY command_name")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"DEBUG: GUI - Error loading commands: {e}")
            self.show_status("Error loading commands")
            return []

    def on_closing(self):
        """Clean up before closing"""
        try:
            if self.voice_active:
                self.speech_recognizer.microphone_off()
            print("DEBUG: GUI - Shutting down")
            self.speech_recognizer.cleanup()
        except Exception as e:
            print(f"DEBUG: GUI - Error during cleanup: {e}")
        finally:
            self.root.destroy()

    def cancel_training(self, dialog):
        """Cancel training and cleanup"""
        try:
            dialog.destroy()
            self.training_in_progress = False
            print("DEBUG: GUI - Training cancelled")
        except Exception as e:
            print(f"DEBUG: GUI - Error cancelling training: {e}")
        finally:
            self.training_in_progress = False

    def cleanup(self):
        """Clean up GUI resources"""
        try:
            print("DEBUG: GUI - Cleaning up resources")
            if self.voice_active:
                self.speech_recognizer.microphone_off()
        except Exception as e:
            print(f"DEBUG: GUI - Error during cleanup: {e}")

    def import_kbs_file(self):
        """Handle KBS file import"""
        try:
            file_path = filedialog.askopenfilename(
                title="Select Studio One KBS File",
                filetypes=[("KBS Files", "*.kbs"), ("All Files", "*.*")]
            )
            
            if file_path:
                print(f"DEBUG: GUI - Importing KBS from: {file_path}")
                
                # Clear existing commands
                self.db.clear_commands()
                
                # Import new commands
                if self.db.import_kbs_commands(file_path):
                    print("DEBUG: GUI - KBS import successful")
                    self.refresh_view()
                    messagebox.showinfo("Success", "KBS file imported successfully!")
                else:
                    messagebox.showerror("Error", "Failed to import KBS file")
                    
        except Exception as e:
            print(f"DEBUG: GUI - Error importing KBS: {e}")
            messagebox.showerror("Error", f"Error importing KBS file: {e}")

    def apply_changes(self):
        """Apply any pending changes"""
        try:
            print("DEBUG: GUI - Applying changes...")
            self.refresh_data()  # Refresh view
            self.show_status("Changes applied successfully")
            
        except Exception as e:
            print(f"DEBUG: GUI - Error applying changes: {e}")
            self.show_status("Error applying changes")
            messagebox.showerror("Error", f"Failed to apply changes: {e}")

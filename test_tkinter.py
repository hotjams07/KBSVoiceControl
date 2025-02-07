import tkinter as tk
from tkinter import ttk

def test_tkinter():
    print("Starting Tkinter test...")
    
    root = tk.Tk()
    root.title("Simple Test")
    root.geometry("300x200")
    
    label = ttk.Label(root, text="Test Window")
    label.pack(pady=20)
    
    button = ttk.Button(root, text="Click Me", command=lambda: print("Button clicked!"))
    button.pack(pady=20)
    
    print("Window created, starting mainloop...")
    root.mainloop()
    print("Window closed")

if __name__ == "__main__":
    test_tkinter() 
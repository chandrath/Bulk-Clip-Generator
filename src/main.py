# main.py
import tkinter as tk
from ui import MainUI  # Import the class directly
from menu import create_menu

def main():
    root = tk.Tk()
    ui_instance = MainUI(root)  # Create the MainUI instance directly
    create_menu(root, ui_instance)  # Pass the instance to create_menu
    root.mainloop()

if __name__ == "__main__":
    main()
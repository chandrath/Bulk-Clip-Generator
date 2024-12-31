import tkinter as tk
from ui import create_ui
from menu import create_menu

def main():
    root = tk.Tk()
    ui_instance = create_ui(root)  # Create the UI and get the instance
    create_menu(root, ui_instance)  # Pass the UI instance to the menu
    root.mainloop()

if __name__ == "__main__":
    main()
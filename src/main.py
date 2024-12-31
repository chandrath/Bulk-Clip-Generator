# main.py
# main.py
import tkinter as tk
from ui import MainUI  # Import the class directly
from menu import create_menu

def main():
    root = tk.Tk()
    root.title("Bulk Clip Generator")  # Ensure title is set before geometry
    root.resizable(False, False)  # Disable resizing
    ui_instance = MainUI(root)  # Create the MainUI instance directly
    create_menu(root, ui_instance)  # Pass the instance to create_menu

    # Center the window on the screen
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = root.winfo_reqwidth()
    window_height = root.winfo_reqheight()
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    root.geometry(f"+{position_right}+{position_top}")

    root.mainloop()

if __name__ == "__main__":
    main()
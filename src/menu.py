# menu.py
import tkinter as tk
from tkinter import messagebox, filedialog
import webbrowser

def create_menu(root, ui_instance=None): # Make ui_instance optional
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # File Menu
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Open Source Video", command=ui_instance.browse_source_video if ui_instance else None)
    file_menu.add_command(label="Clear Fields", command=ui_instance.clear_fields if ui_instance else None)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=file_menu)

    # Settings Menu
    settings_menu = tk.Menu(menubar, tearoff=0)
    
    # Hardware Acceleration Submenu
    hw_accel_menu = tk.Menu(settings_menu, tearoff=0)
    if ui_instance and hasattr(ui_instance, 'gpu_detector'):
        encoders = ui_instance.gpu_detector.get_available_encoders()
        if encoders:
            for name, codec in encoders:
                hw_accel_menu.add_checkbutton(
                    label=name,
                    variable=ui_instance.hw_accel_vars[codec],
                    command=lambda c=codec: ui_instance.toggle_hw_acceleration(c)
                )
        else:
            hw_accel_menu.add_command(
                label="No GPU detected",
                state="disabled"
            )
    settings_menu.add_cascade(label="Hardware Acceleration", menu=hw_accel_menu)
    menubar.add_cascade(label="Settings", menu=settings_menu)


    # Help Menu
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="About", command=show_about)
    menubar.add_cascade(label="Help", menu=help_menu)

def show_about():
    messagebox.showinfo("About Bulk Clip Generator",
                        "Bulk Clip Generator\n"
                        "Version: 0.1 (Alpha)\n"
                        "Developed by: Shree\n"
                        "Repository: [https://github.com/chandrath/Bulk-Clip-Generator]")

if __name__ == '__main__':
    root = tk.Tk()
    create_menu(root) # Don't pass ui_instance for standalone test
    root.mainloop()
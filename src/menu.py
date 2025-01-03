# menu.py
import tkinter as tk
from tkinter import messagebox, filedialog, Toplevel
import webbrowser

class HyperlinkManager:
    def __init__(self, text):
        self.text = text
        self.text.tag_config("hyper", foreground="blue", underline=1)
        self.text.tag_bind("hyper", "<Enter>", self._enter)
        self.text.tag_bind("hyper", "<Leave>", self._leave)
        self.text.tag_bind("hyper", "<Button-1>", self._click)
        self.links = {}  # Store links with unique identifiers

    def add(self, link):
        # Generate a unique identifier for the link
        link_id = f"link-{len(self.links)}"
        self.links[link_id] = link
        # Apply the tag to the text
        return self._add_link(link_id)

    def _add_link(self, link_id):
        return 'hyper', link_id

    def _enter(self, event):
        self.text.config(cursor="hand2")

    def _leave(self, event):
        self.text.config(cursor="")

    def _click(self, event):
        for tag in self.text.tag_names(tk.CURRENT):
            if tag.startswith("link-"):
                webbrowser.open(self.links[tag])
                return

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
    help_menu.add_command(label="About", command=lambda: show_about(root)) # Pass root to show_about
    menubar.add_cascade(label="Help", menu=help_menu)

def show_about(parent):
    about_window = Toplevel(parent)
    about_window.title("About Bulk Clip Generator")

    text = tk.Text(about_window, wrap=tk.WORD, height=7, width=50)
    text.pack(padx=10, pady=10)
    text.insert(tk.END, "Bulk Clip Generator v0.1 (Alpha)\nA simple tool to cut multiple clips from a video.\n\nDeveloped By: Shree\n\n")

    text.config(state=tk.NORMAL)
    link_manager = HyperlinkManager(text)
    text.insert(tk.END, "Repository: ")
    text.insert(tk.END, "https://github.com/chandrath/Bulk-Clip-Generator", link_manager.add("https://github.com/chandrath/Bulk-Clip-Generator"))
    text.config(state=tk.DISABLED)

if __name__ == '__main__':
    root = tk.Tk()
    create_menu(root) # Don't pass ui_instance for standalone test
    root.mainloop()
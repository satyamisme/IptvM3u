import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading

from .filter_panel import FilterPanel
from .channel_tree import ChannelTree
from .status_bar import StatusBar

class MainWindow(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.title("IPTV Filter Pro")
        self.geometry("1024x768")
        self.minsize(800, 600)

        self._setup_ui()

    def _setup_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Load API Data", command=self.controller.load_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Load M3U File", command=self.controller.load_m3u_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Load URL", command=self.controller.load_m3u_url).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        ttk.Button(toolbar, text="Update Current Playlist", command=self.controller.update_current_playlist).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Export M3U", command=self.controller.export_data).pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="Toggle Theme", command=self.controller.toggle_theme).pack(side=tk.RIGHT, padx=2)

        # Main split container
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: Filters
        filter_container = ttk.Frame(self.paned_window, width=280)
        self.paned_window.add(filter_container, weight=0)

        self.filter_panel = FilterPanel(filter_container, self.controller)
        self.filter_panel.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Right panel: Results
        results_container = ttk.Frame(self.paned_window)
        self.paned_window.add(results_container, weight=1)

        self.count_label_var = tk.StringVar(value="0 channels loaded")
        ttk.Label(results_container, textvariable=self.count_label_var, font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))

        tree_frame = ttk.Frame(results_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.channel_tree = ChannelTree(
            tree_frame,
            on_toggle_favorite=self.controller.toggle_favorite,
            on_preview_stream=self.controller.preview_stream
        )

        # Status Bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_channel_count(self, count: int, total: int = None):
        if total is not None:
            self.count_label_var.set(f"Showing {count} of {total} channels")
        else:
            self.count_label_var.set(f"{count} channels found")

    def ask_open_filename(self) -> str:
        return filedialog.askopenfilename(
            filetypes=[("M3U Playlist", "*.m3u *.m3u8"), ("All Files", "*.*")]
        )

    def ask_string(self, title: str, prompt: str) -> str:
        return simpledialog.askstring(title, prompt, parent=self)

    def ask_save_filename(self) -> str:
        return filedialog.asksaveasfilename(
            defaultextension=".m3u",
            filetypes=[("M3U Playlist", "*.m3u"), ("All Files", "*.*")]
        )

    def ask_yes_no(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, parent=self)

    def show_error(self, title: str, message: str):
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str):
        messagebox.showinfo(title, message)

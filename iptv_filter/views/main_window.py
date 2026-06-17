import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading

from .filter_panel import FilterPanel
from .channel_tree import ChannelTree
from .status_bar import StatusBar
from .inspector_panel import InspectorPanel

class MainWindow(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.title("IPTV Filter Pro")
        self.geometry("1400x900")
        self.minsize(1200, 750)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._setup_ui()

    def _setup_ui(self):
        # Grid layout:
        # R0: Toolbar
        # R1: Content split (Filters, Main, Inspector)
        # R2: Status Bar
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Toolbar
        self.toolbar = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=("gray85", "#1a1c20"))
        self.toolbar.grid(row=0, column=0, sticky="ew")

        self.toolbar.grid_columnconfigure(1, weight=1)

        logo = ctk.CTkLabel(self.toolbar, text="StreamControl Pro", font=("Geist", 20, "bold"), text_color="#adc6ff")
        logo.grid(row=0, column=0, padx=15, pady=10)

        action_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        action_frame.grid(row=0, column=1, sticky="w", padx=10)

        btn_style = {"height": 32, "font": ("Inter", 12)}
        ctk.CTkButton(action_frame, text="📡 Fetch API", command=self.controller.load_data, width=110, **btn_style).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="📁 Load File", command=self.controller.load_m3u_file, width=110, fg_color="#333539", hover_color="#424754", **btn_style).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="🌐 Load URL", command=self.controller.load_m3u_url, width=110, fg_color="#333539", hover_color="#424754", **btn_style).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="💾 Export As...", command=self.controller.export_data, width=110, **btn_style).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="🔄 Update Local", command=self.controller.update_current_playlist, width=120, fg_color="#333539", hover_color="#424754", **btn_style).pack(side="left", padx=5)

        ctk.CTkButton(self.toolbar, text="🌙 Theme", command=self.controller.toggle_theme, width=90, fg_color="transparent", hover_color="#282a2e").grid(row=0, column=2, padx=15)

        # Content Split
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)

        # Left Panel: Filters
        self.filter_panel = FilterPanel(content_frame, self.controller)
        self.filter_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Center Panel: Treeview
        center_frame = ctk.CTkFrame(content_frame, fg_color=("gray90", "#1e2024"), corner_radius=12)
        center_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        center_top = ctk.CTkFrame(center_frame, fg_color="transparent")
        center_top.pack(fill="x", padx=15, pady=(15,5))
        self.count_label_var = ctk.StringVar(value="0 channels loaded")
        ctk.CTkLabel(center_top, textvariable=self.count_label_var, font=("Inter", 14, "bold")).pack(side="left")

        tree_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=15, pady=(5,15))

        self.channel_tree = ChannelTree(
            tree_frame,
            on_toggle_favorite=self.controller.toggle_favorite,
            on_preview_stream=self.controller.preview_stream,
            on_select_channel=self._on_channel_selected
        )

        # Right Panel: Inspector
        self.inspector_panel = InspectorPanel(content_frame, self.controller)
        self.inspector_panel.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        # Ensure it has a fixed width
        self.inspector_panel.grid_configure(ipadx=0, ipady=0)
        self.inspector_panel.configure(width=300)
        self.inspector_panel.grid_propagate(False)

        # Status Bar
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _on_channel_selected(self, channel):
        self.inspector_panel.set_channel(channel)

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
            filetypes=[("M3U Playlist", "*.m3u"), ("JSON File", "*.json"), ("CSV File", "*.csv"), ("All Files", "*.*")]
        )

    def ask_yes_no(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, parent=self)

    def show_error(self, title: str, message: str):
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str):
        messagebox.showinfo(title, message)

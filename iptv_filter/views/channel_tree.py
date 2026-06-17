import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Set
from iptv_filter.models.channel import Channel

class ChannelTree(ttk.Treeview):
    def __init__(self, parent, on_toggle_favorite: Callable, on_preview_stream: Callable, on_select_channel: Callable, **kwargs):
        columns = ("favorite", "status", "id", "name", "country", "categories", "languages")
        super().__init__(parent, columns=columns, show="headings", **kwargs)

        self.on_toggle_favorite = on_toggle_favorite
        self.on_preview_stream = on_preview_stream
        self.on_select_channel = on_select_channel

        # Apply modern style
        style = ttk.Style()
        style.theme_use("clam")

        # We will assume Dark mode base to start (matching HTML)
        style.configure("Treeview",
            background="#1e2024",
            foreground="#e2e2e8",
            fieldbackground="#1e2024",
            rowheight=35,
            font=('Inter', 11),
            borderwidth=0
        )
        style.map("Treeview",
            background=[('selected', '#282a2e')],
            foreground=[('selected', '#e2e2e8')]
        )
        style.configure("Treeview.Heading",
            background="#282a2e",
            foreground="#8c909f",
            font=('Inter', 11, 'bold'),
            padding=(8, 6),
            borderwidth=0
        )

        self.heading("favorite", text="⭐")
        self.heading("status", text="STAT")
        self.heading("id", text="ID")
        self.heading("name", text="NAME")
        self.heading("country", text="COUNTRY")
        self.heading("categories", text="CATEGORY")
        self.heading("languages", text="LANGUAGE")

        self.column("favorite", width=40, anchor=tk.CENTER)
        self.column("status", width=50, anchor=tk.CENTER)
        self.column("id", width=120)
        self.column("name", width=250)
        self.column("country", width=80, anchor=tk.CENTER)
        self.column("categories", width=150)
        self.column("languages", width=150)

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.xview)
        self.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        self.channels_data = {}

        self.context_menu = tk.Menu(self, tearoff=0, bg="#1e2024", fg="#e2e2e8", activebackground="#282a2e")
        self.context_menu.add_command(label="Toggle Favorite", command=self._toggle_fav_context)
        self.context_menu.add_command(label="Preview Stream (Browser)", command=self._preview_stream)
        self.context_menu.add_command(label="Copy Stream URL", command=self._copy_url)
        self.bind("<Button-3>", self._show_context_menu)
        self.bind("<Double-1>", lambda e: self._preview_stream())
        self.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, event):
        selected = self.selection()
        if selected:
            item_id = selected[0]
            channel_id = self.item(item_id, "values")[2]
            channel = self.channels_data.get(channel_id)
            if channel:
                self.on_select_channel(channel)

    def _show_context_menu(self, event):
        item = self.identify_row(event.y)
        if item:
            self.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _toggle_fav_context(self):
        selected = self.selection()
        if not selected: return
        item_id = selected[0]
        channel_id = self.item(item_id, "values")[2]
        new_state = self.on_toggle_favorite(channel_id)

        vals = list(self.item(item_id, "values"))
        vals[0] = "⭐" if new_state else ""
        self.item(item_id, values=vals)

    def _preview_stream(self):
        selected = self.selection()
        if not selected: return
        item_id = selected[0]
        channel_id = self.item(item_id, "values")[2]
        self.on_preview_stream(channel_id)

    def _copy_url(self):
        selected = self.selection()
        if not selected: return
        item_id = selected[0]
        channel_id = self.item(item_id, "values")[2]
        channel = self.channels_data.get(channel_id)
        if channel and channel.streams:
            url = channel.streams[0].get("url", "")
            if url:
                self.clipboard_clear()
                self.clipboard_append(url)

    def populate(self, channels: List[Channel], favorites: Set[str]):
        self.delete(*self.get_children())
        self.channels_data.clear()

        for i, ch in enumerate(channels):
            self.channels_data[ch.id] = ch
            if i > 5000: break

            cats = ", ".join(ch.categories)
            langs = ", ".join(ch.languages)
            is_fav = "⭐" if ch.id in favorites else ""
            status = ch.status_icon

            self.insert("", tk.END, values=(
                is_fav, status, ch.id, ch.name, ch.country, cats, langs
            ))

            if i % 500 == 0:
                self.update_idletasks()

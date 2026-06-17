import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Set
from iptv_filter.models.channel import Channel

class ChannelTree(ttk.Treeview):
    def __init__(self, parent, on_toggle_favorite: Callable, **kwargs):
        columns = ("favorite", "id", "name", "country", "categories", "languages", "streams")
        super().__init__(parent, columns=columns, show="headings", **kwargs)

        self.on_toggle_favorite = on_toggle_favorite

        self.heading("favorite", text="⭐")
        self.heading("id", text="ID")
        self.heading("name", text="Name")
        self.heading("country", text="Country")
        self.heading("categories", text="Categories")
        self.heading("languages", text="Languages")
        self.heading("streams", text="Streams")

        self.column("favorite", width=30, anchor=tk.CENTER)
        self.column("id", width=120)
        self.column("name", width=200)
        self.column("country", width=60, anchor=tk.CENTER)
        self.column("categories", width=150)
        self.column("languages", width=100)
        self.column("streams", width=60, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.xview)
        self.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        self.channels_data = {}

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Toggle Favorite", command=self._toggle_fav_context)
        self.context_menu.add_command(label="Copy Stream URL", command=self._copy_url)
        self.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        item = self.identify_row(event.y)
        if item:
            self.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _toggle_fav_context(self):
        selected = self.selection()
        if not selected: return
        item_id = selected[0]
        channel_id = self.item(item_id, "values")[1] # ID is index 1 now
        new_state = self.on_toggle_favorite(channel_id)

        vals = list(self.item(item_id, "values"))
        vals[0] = "⭐" if new_state else ""
        self.item(item_id, values=vals)

    def _copy_url(self):
        selected = self.selection()
        if not selected: return
        item_id = selected[0]
        channel_id = self.item(item_id, "values")[1]
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
            num_streams = len(ch.streams)
            is_fav = "⭐" if ch.id in favorites else ""

            self.insert("", tk.END, values=(
                is_fav, ch.id, ch.name, ch.country, cats, langs, num_streams
            ))

            if i % 500 == 0:
                self.update_idletasks()

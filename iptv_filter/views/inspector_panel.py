import customtkinter as ctk
from iptv_filter.models.channel import Channel

class InspectorPanel(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=12, fg_color=("gray90", "#1e2024"))
        self.controller = controller

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=15)

        ctk.CTkLabel(header, text="Inspector", font=("Inter", 16, "bold")).pack(side="left")

        # Details container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        # Video placeholder box
        self.preview_box = ctk.CTkFrame(self.scroll, height=150, corner_radius=8, fg_color="#111317")
        self.preview_box.pack(fill="x", pady=(0, 15))
        self.preview_box.pack_propagate(False)
        self.preview_status = ctk.CTkLabel(self.preview_box, text="Select a channel", text_color="#8c909f")
        self.preview_status.place(relx=0.5, rely=0.5, anchor="center")

        self.info_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.info_frame.pack(fill="both", expand=True)

        self.labels = {}

    def add_info_row(self, label: str, value: str, row_idx: int):
        f = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=label, text_color="#8c909f", font=("Inter", 12)).pack(side="left")

        val_label = ctk.CTkLabel(f, text=value, font=("Inter", 12, "bold"), wraplength=180, justify="right")
        val_label.pack(side="right")
        self.labels[label] = val_label

    def clear_info(self):
        for w in self.info_frame.winfo_children():
            w.destroy()
        self.labels.clear()

    def set_channel(self, channel: Channel):
        self.clear_info()
        if not channel:
            self.preview_status.configure(text="Select a channel")
            return

        self.preview_status.configure(text="Ready to Preview\n(Right-click in list)")

        self.add_info_row("ID", channel.id, 0)
        self.add_info_row("Name", channel.name, 1)
        self.add_info_row("Country", channel.country or "Unknown", 2)
        self.add_info_row("Status", channel.status_text, 3)
        self.add_info_row("Categories", ", ".join(channel.categories) if channel.categories else "None", 4)
        self.add_info_row("Languages", ", ".join(channel.languages) if channel.languages else "None", 5)
        self.add_info_row("Network", channel.network or "None", 6)

        # Streams
        stream_url = channel.streams[0].get("url", "None") if channel.streams else "None"
        # Truncate stream url for display
        if len(stream_url) > 25:
            stream_url = stream_url[:10] + "..." + stream_url[-10:]
        self.add_info_row("URL", stream_url, 7)

        # Action buttons
        btn_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)

        ctk.CTkButton(btn_frame, text="Preview Stream", fg_color="#adc6ff", text_color="#002e6a", hover_color="#8baaff",
                      command=lambda: self.controller.preview_stream(channel.id)).pack(fill="x", pady=5)

        is_fav = self.controller.prefs.is_favorite(channel.id)
        fav_text = "Remove Favorite" if is_fav else "Add Favorite"
        ctk.CTkButton(btn_frame, text=fav_text, fg_color="#333539", hover_color="#424754",
                      command=lambda: self._toggle_fav(channel.id)).pack(fill="x", pady=5)

    def _toggle_fav(self, channel_id):
        self.controller.toggle_favorite(channel_id)
        # re-select triggers redraw
        ch = next((c for c in self.controller.filter_engine.channels if c.id == channel_id), None)
        self.set_channel(ch)

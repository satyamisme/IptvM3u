import customtkinter as ctk

class StatisticsDashboard(ctk.CTkToplevel):
    def __init__(self, parent, stats: dict):
        super().__init__(parent)
        self.title("Channel Statistics")
        self.geometry("600x400")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        header = ctk.CTkLabel(self, text="Dashboard Overview", font=("Inter", 20, "bold"))
        header.grid(row=0, column=0, columnspan=2, pady=(20, 10))

        # Cards frame
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)

        cards_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.create_stat_card(cards_frame, "Total", stats.get('total', 0), "#adc6ff", 0, 0)
        self.create_stat_card(cards_frame, "Filtered", stats.get('filtered', 0), "#4edea3", 0, 1)
        self.create_stat_card(cards_frame, "Working", stats.get('working_count', 0), "#4edea3", 0, 2)
        self.create_stat_card(cards_frame, "Dead", stats.get('dead_count', 0), "#ffb4ab", 0, 3)

        # Details frame
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        details_frame.grid_columnconfigure((0,1), weight=1)

        # Top Langs
        lang_frame = ctk.CTkFrame(details_frame, corner_radius=12, fg_color=("gray90", "#1e2024"))
        lang_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        ctk.CTkLabel(lang_frame, text="Top Languages", font=("Inter", 14, "bold")).pack(pady=10)
        for l, c in stats.get('top_languages', []):
            f = ctk.CTkFrame(lang_frame, fg_color="transparent")
            f.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(f, text=l).pack(side="left")
            ctk.CTkLabel(f, text=str(c), font=("Inter", 12, "bold")).pack(side="right")

        # Top Cats
        cat_frame = ctk.CTkFrame(details_frame, corner_radius=12, fg_color=("gray90", "#1e2024"))
        cat_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        ctk.CTkLabel(cat_frame, text="Top Categories", font=("Inter", 14, "bold")).pack(pady=10)
        for c_name, count in stats.get('top_categories', []):
            f = ctk.CTkFrame(cat_frame, fg_color="transparent")
            f.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(f, text=c_name).pack(side="left")
            ctk.CTkLabel(f, text=str(count), font=("Inter", 12, "bold")).pack(side="right")

    def create_stat_card(self, parent, title, value, color, row, col):
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=("gray90", "#1e2024"), border_width=1, border_color=color)
        card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(card, text=title, text_color="#8c909f", font=("Inter", 12)).pack(pady=(15, 0))
        ctk.CTkLabel(card, text=str(value), text_color=color, font=("Geist", 24, "bold")).pack(pady=(5, 15))

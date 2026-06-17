import customtkinter as ctk

class StatusBar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, height=40, fg_color=("gray85", "#1a1c20"), corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.label = ctk.CTkLabel(self, text="Ready", font=("Inter", 12), text_color=("#333333", "#c2c6d6"))
        self.label.grid(row=0, column=0, sticky="w", padx=15, pady=10)

        self.progress = ctk.CTkProgressBar(self, width=200, height=8, progress_color=("#005ac2", "#adc6ff"))
        self.progress.grid(row=0, column=1, sticky="e", padx=15, pady=10)
        self.progress.set(0)

        self._indeterminate_active = False

    def set_status(self, text: str):
        self.label.configure(text=text)
        self.update_idletasks()

    def update_progress(self, current: int, total: int, text: str = None):
        if text:
            self.label.configure(text=text)
        if total > 0:
            self.progress.set(current / total)
        self.update_idletasks()

    def start_indeterminate(self, text: str = "Loading..."):
        self.label.configure(text=text)
        self._indeterminate_active = True
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.update_idletasks()

    def stop_progress(self, text: str = "Ready"):
        if self._indeterminate_active:
            self.progress.stop()
            self.progress.configure(mode="determinate")
            self._indeterminate_active = False

        self.progress.set(0)
        self.label.configure(text=text)
        self.update_idletasks()

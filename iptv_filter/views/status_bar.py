import tkinter as tk
from tkinter import ttk

class StatusBar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.label_var = tk.StringVar(value="Ready")
        self.label = ttk.Label(self, textvariable=self.label_var, anchor=tk.W)
        self.label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress.pack(side=tk.RIGHT, padx=5)

    def set_status(self, text: str):
        self.label_var.set(text)
        self.update_idletasks()

    def update_progress(self, current: int, total: int, text: str = None):
        if text:
            self.label_var.set(text)
        self.progress['maximum'] = total
        self.progress['value'] = current
        self.update_idletasks()

    def start_indeterminate(self, text: str = "Loading..."):
        self.label_var.set(text)
        self.progress.config(mode='indeterminate')
        self.progress.start(10)
        self.update_idletasks()

    def stop_progress(self, text: str = "Ready"):
        self.progress.stop()
        self.progress.config(mode='determinate')
        self.progress['value'] = 0
        self.label_var.set(text)
        self.update_idletasks()

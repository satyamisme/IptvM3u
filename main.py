import sys
import threading
from tkinter import messagebox
from iptv_filter.views.main_window import MainWindow
from iptv_filter.controllers.api_client import ApiClient
from iptv_filter.controllers.cache_manager import CacheManager
from iptv_filter.controllers.playlist_parser import DataProcessor
from iptv_filter.controllers.filter_engine import FilterEngine
from iptv_filter.controllers.export_manager import ExportManager

class AppController:
    def __init__(self):
        self.cache_manager = CacheManager()
        self.api_client = ApiClient(self.cache_manager)
        self.data_processor = DataProcessor()
        self.filter_engine = FilterEngine()

        self.window = MainWindow(self)

        # Load initial data on startup
        self.window.after(100, self.load_data)

    def run(self):
        self.window.mainloop()

    def load_data(self):
        def worker():
            try:
                self.window.status_bar.start_indeterminate("Fetching and processing API data...")

                api_data = self.api_client.fetch_all()
                playlist = self.data_processor.process_data(api_data)

                self.filter_engine.load_channels(playlist.channels)

                self.window.after(0, self._on_data_loaded)
            except Exception as e:
                self.window.after(0, self.window.show_error, "Error loading API data", str(e))
                self.window.after(0, self.window.status_bar.stop_progress, "Error")

        threading.Thread(target=worker, daemon=True).start()

    def load_m3u_file(self):
        filepath = self.window.ask_open_filename()
        if not filepath:
            return

        def worker():
            try:
                self.window.status_bar.start_indeterminate("Loading M3U file...")
                playlist = self.data_processor.load_m3u_file(filepath)
                self.filter_engine.load_channels(playlist.channels)
                self.window.after(0, self._on_data_loaded)
            except Exception as e:
                self.window.after(0, self.window.show_error, "Error loading M3U", str(e))
                self.window.after(0, self.window.status_bar.stop_progress, "Error")

        threading.Thread(target=worker, daemon=True).start()

    def load_m3u_url(self):
        url = self.window.ask_string("Load M3U URL", "Enter M3U Playlist URL:")
        if not url:
            return

        def worker():
            try:
                self.window.status_bar.start_indeterminate("Downloading M3U...")
                playlist = self.data_processor.load_m3u_url(url)
                self.filter_engine.load_channels(playlist.channels)
                self.window.after(0, self._on_data_loaded)
            except Exception as e:
                self.window.after(0, self.window.show_error, "Error loading M3U URL", str(e))
                self.window.after(0, self.window.status_bar.stop_progress, "Error")

        threading.Thread(target=worker, daemon=True).start()

    def _on_data_loaded(self):
        languages = list(self.filter_engine.channels_by_language.keys())
        categories = list(self.filter_engine.channels_by_category.keys())
        countries_counts = self.filter_engine.get_country_counts()

        self.window.filter_panel.populate_lists(languages, categories, countries_counts)

        # Trigger an initial filter to populate tree
        self.window.filter_panel._trigger_filter()
        self.window.status_bar.stop_progress("Data loaded successfully.")

    def apply_filters(self, filters: dict):
        def worker():
            self.window.status_bar.start_indeterminate("Applying filters...")
            filtered = self.filter_engine.apply_filters(**filters)

            # Update UI safely
            self.window.after(0, self._update_tree, filtered)

        threading.Thread(target=worker, daemon=True).start()

    def _update_tree(self, filtered_channels):
        self.window.channel_tree.populate(filtered_channels)
        self.window.update_channel_count(len(filtered_channels))
        self.window.status_bar.stop_progress("Ready")

    def export_data(self):
        if not self.filter_engine.filtered_channels:
            self.window.show_info("Export", "No channels to export.")
            return

        filepath = self.window.ask_save_filename()
        if filepath:
            try:
                self.window.status_bar.start_indeterminate("Exporting M3U...")
                ExportManager.export_m3u(filepath, self.filter_engine.filtered_channels)
                self.window.status_bar.stop_progress("Export successful.")
                self.window.show_info("Export Success", f"Playlist saved to {filepath}")
            except Exception as e:
                self.window.status_bar.stop_progress("Export failed.")
                self.window.show_error("Export Error", str(e))

if __name__ == "__main__":
    app = AppController()
    app.run()

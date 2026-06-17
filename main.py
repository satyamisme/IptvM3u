import sys
import threading
from tkinter import messagebox
import tkinter as tk

from iptv_filter.views.main_window import MainWindow
from iptv_filter.controllers.api_client import ApiClient
from iptv_filter.controllers.cache_manager import CacheManager
from iptv_filter.controllers.playlist_parser import DataProcessor
from iptv_filter.controllers.filter_engine import FilterEngine
from iptv_filter.controllers.export_manager import ExportManager
from iptv_filter.controllers.preferences_manager import PreferencesManager

class AppController:
    def __init__(self):
        self.prefs = PreferencesManager()
        self.cache_manager = CacheManager()
        self.api_client = ApiClient(self.cache_manager)
        self.data_processor = DataProcessor()
        self.filter_engine = FilterEngine()

        self.window = MainWindow(self)
        self.apply_theme(self.prefs.get_setting("theme", "light"))

        # Load initial data on startup
        self.window.after(100, self.load_data)

    def run(self):
        self.window.mainloop()

    def toggle_theme(self):
        current = self.prefs.get_setting("theme", "light")
        new_theme = "dark" if current == "light" else "light"
        self.prefs.set_setting("theme", new_theme)
        self.apply_theme(new_theme)

    def apply_theme(self, theme_name: str):
        # Very basic tk styling fallback if sv_ttk is not installed.
        bg = "#1E1E1E" if theme_name == "dark" else "#FFFFFF"
        fg = "#E0E0E0" if theme_name == "dark" else "#212121"
        try:
            self.window.tk.call("tk", "windowingsystem")
            # We can change standard tk background for main window
            self.window.configure(bg=bg)
        except:
            pass

    def toggle_favorite(self, channel_id: str) -> bool:
        return self.prefs.toggle_favorite(channel_id)

    def save_preset(self, name: str, filters: dict):
        self.prefs.save_preset(name, filters)
        self._update_presets_list()
        self.window.show_info("Preset Saved", f"Preset '{name}' saved successfully.")

    def get_preset(self, name: str) -> dict:
        return self.prefs.get_preset(name)

    def _update_presets_list(self):
        presets = list(self.prefs.presets.keys())
        self.window.filter_panel.populate_presets(presets)

    def remove_duplicates(self):
        count = self.filter_engine.remove_duplicates()
        if count > 0:
            self.window.show_info("Duplicates Removed", f"Removed {count} duplicate channels.")
            self._update_tree(self.filter_engine.filtered_channels)
        else:
            self.window.show_info("Duplicates", "No duplicates found in current view.")

    def show_statistics(self):
        stats = self.filter_engine.get_statistics()
        msg = f"Total Channels Loaded: {stats['total']}\n"
        msg += f"Currently Filtered: {stats['filtered']}\n"
        msg += f"Duplicates Detected (Filtered View): {stats['duplicates_in_filtered']}\n\n"

        msg += "Top Languages:\n"
        for l, c in stats['top_languages']:
            msg += f"  - {l}: {c}\n"

        msg += "\nTop Categories:\n"
        for c, count in stats['top_categories']:
            msg += f"  - {c}: {count}\n"

        self.window.show_info("Channel Statistics", msg)

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

        self.prefs.set_setting("last_loaded_file", filepath)

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
        self._update_presets_list()

        self.window.filter_panel._trigger_filter()
        self.window.status_bar.stop_progress("Data loaded successfully.")

    def apply_filters(self, filters: dict):
        # Inject favorites list
        filters["favorites_set"] = self.prefs.favorites

        def worker():
            self.window.status_bar.start_indeterminate("Applying filters...")
            filtered = self.filter_engine.apply_filters(**filters)

            self.window.after(0, self._update_tree, filtered)

        threading.Thread(target=worker, daemon=True).start()

    def _update_tree(self, filtered_channels):
        self.window.channel_tree.populate(filtered_channels, self.prefs.favorites)
        self.window.update_channel_count(len(filtered_channels), len(self.filter_engine.channels))
        self.window.status_bar.stop_progress("Ready")

    def export_data(self):
        if not self.filter_engine.filtered_channels:
            self.window.show_info("Export", "No channels to export.")
            return

        filepath = self.window.ask_save_filename()
        if filepath:
            self._do_export(filepath)

    def update_current_playlist(self):
        if not self.filter_engine.filtered_channels:
            self.window.show_info("Update", "No channels to export.")
            return

        last_file = self.prefs.get_setting("last_loaded_file", "")
        if not last_file:
            self.window.show_info("Update Playlist", "No local file was loaded recently. Use Export M3U instead.")
            return

        if self.window.ask_yes_no("Update Playlist", f"Overwrite {last_file} with current filtered list?"):
            self._do_export(last_file)

    def _do_export(self, filepath: str):
        try:
            self.window.status_bar.start_indeterminate(f"Exporting M3U to {filepath}...")
            ExportManager.export_m3u(filepath, self.filter_engine.filtered_channels)
            self.window.status_bar.stop_progress("Export successful.")
            self.window.show_info("Export Success", f"Playlist saved to {filepath}")
        except Exception as e:
            self.window.status_bar.stop_progress("Export failed.")
            self.window.show_error("Export Error", str(e))

if __name__ == "__main__":
    app = AppController()
    app.run()

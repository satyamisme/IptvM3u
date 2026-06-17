import os
import json
from typing import Set, Dict, List

class PreferencesManager:
    def __init__(self, data_dir: str = "."):
        self.data_dir = data_dir
        self.favorites_file = os.path.join(self.data_dir, "favorites.json")
        self.presets_file = os.path.join(self.data_dir, "presets.json")
        self.settings_file = os.path.join(self.data_dir, "settings.json")

        self.favorites: Set[str] = set()
        self.presets: Dict[str, dict] = self._default_presets()
        self.settings: dict = {"theme": "light", "last_loaded_file": ""}

        self.load_all()

    def _default_presets(self) -> Dict[str, dict]:
        return {
            "Indian Languages": {"languages": ["hin", "tel", "tam", "mal", "kan"]},
            "Kids Content": {"categories": ["kids", "education"]},
            "Family Friendly": {"nsfw": False},
            "News & Education": {"categories": ["news", "education"]}
        }

    def _load_json(self, filepath: str, default: any) -> any:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return default

    def _save_json(self, filepath: str, data: any):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving {filepath}: {e}")

    def load_all(self):
        fav_list = self._load_json(self.favorites_file, [])
        self.favorites = set(fav_list)

        loaded_presets = self._load_json(self.presets_file, {})
        # Merge with defaults
        self.presets = self._default_presets()
        self.presets.update(loaded_presets)

        loaded_settings = self._load_json(self.settings_file, {})
        self.settings.update(loaded_settings)

    def save_all(self):
        self._save_json(self.favorites_file, list(self.favorites))
        self._save_json(self.presets_file, self.presets)
        self._save_json(self.settings_file, self.settings)

    def toggle_favorite(self, channel_id: str) -> bool:
        """Returns True if added, False if removed"""
        if channel_id in self.favorites:
            self.favorites.remove(channel_id)
            self.save_all()
            return False
        else:
            self.favorites.add(channel_id)
            self.save_all()
            return True

    def is_favorite(self, channel_id: str) -> bool:
        return channel_id in self.favorites

    def save_preset(self, name: str, filters: dict):
        self.presets[name] = filters
        self.save_all()

    def get_preset(self, name: str) -> dict:
        return self.presets.get(name, {})

    def set_setting(self, key: str, value: any):
        self.settings[key] = value
        self.save_all()

    def get_setting(self, key: str, default: any = None) -> any:
        return self.settings.get(key, default)

from typing import List, Dict, Set
from iptv_filter.models.channel import Channel

class FilterEngine:
    def __init__(self):
        self.channels: List[Channel] = []
        self.filtered_channels: List[Channel] = []

        # Lookups
        self.channels_by_language: Dict[str, Set[str]] = {}
        self.channels_by_category: Dict[str, Set[str]] = {}
        self.channels_by_country: Dict[str, Set[str]] = {}

    def load_channels(self, channels: List[Channel]):
        self.channels = channels
        self._build_lookups()
        self.filtered_channels = self.channels.copy()

    def _build_lookups(self):
        self.channels_by_language.clear()
        self.channels_by_category.clear()
        self.channels_by_country.clear()

        for ch in self.channels:
            if ch.country:
                self.channels_by_country.setdefault(ch.country, set()).add(ch.id)
            for cat in ch.categories:
                self.channels_by_category.setdefault(cat, set()).add(ch.id)
            for lang in ch.languages:
                self.channels_by_language.setdefault(lang, set()).add(ch.id)

    def get_country_counts(self) -> Dict[str, int]:
        return {country: len(ids) for country, ids in self.channels_by_country.items()}

    def apply_filters(self,
                      search_term: str = "",
                      languages: List[str] = None,
                      categories: List[str] = None,
                      countries: List[str] = None,
                      nsfw: bool = False,
                      exclude_closed: bool = True) -> List[Channel]:

        result_ids = {ch.id for ch in self.channels}

        # If languages are selected, channel must have AT LEAST ONE of the selected languages
        if languages:
            lang_ids = set()
            for lang in languages:
                lang_ids.update(self.channels_by_language.get(lang, set()))
            result_ids.intersection_update(lang_ids)

        # Same for categories
        if categories:
            cat_ids = set()
            for cat in categories:
                cat_ids.update(self.channels_by_category.get(cat, set()))
            result_ids.intersection_update(cat_ids)

        # Same for countries
        if countries:
            country_ids = set()
            for country in countries:
                country_ids.update(self.channels_by_country.get(country, set()))
            result_ids.intersection_update(country_ids)

        # Apply search, nsfw, exclude_closed manually
        filtered = []
        search_term = search_term.lower() if search_term else ""

        for ch in self.channels:
            if ch.id not in result_ids:
                continue

            if exclude_closed and ch.closed:
                continue

            if not nsfw and ch.is_nsfw:
                continue

            if search_term:
                name_match = search_term in ch.name.lower()
                alt_match = any(search_term in alt.lower() for alt in ch.alt_names)
                network_match = ch.network and search_term in ch.network.lower()
                if not (name_match or alt_match or network_match):
                    continue

            filtered.append(ch)

        self.filtered_channels = filtered
        return self.filtered_channels

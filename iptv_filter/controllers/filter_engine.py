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

    def get_statistics(self) -> dict:
        total = len(self.channels)
        filtered = len(self.filtered_channels)

        lang_counts = [(l, len(ids)) for l, ids in self.channels_by_language.items()]
        lang_counts.sort(key=lambda x: x[1], reverse=True)
        top_langs = lang_counts[:5]

        cat_counts = [(c, len(ids)) for c, ids in self.channels_by_category.items()]
        cat_counts.sort(key=lambda x: x[1], reverse=True)
        top_cats = cat_counts[:5]

        seen_urls = set()
        duplicate_count = 0
        working_count = 0
        dead_count = 0
        geo_count = 0

        for ch in self.filtered_channels:
            if ch.status_text == "Working" or ch.status_text == "Slow":
                working_count += 1
            elif ch.status_text == "Dead":
                dead_count += 1
            elif ch.status_text == "Geo-blocked":
                geo_count += 1

            if ch.streams:
                url = ch.streams[0].get("url")
                if url in seen_urls:
                    duplicate_count += 1
                else:
                    seen_urls.add(url)

        return {
            "total": total,
            "filtered": filtered,
            "top_languages": top_langs,
            "top_categories": top_cats,
            "duplicates_in_filtered": duplicate_count,
            "working_count": working_count,
            "dead_count": dead_count,
            "geo_count": geo_count
        }

    def remove_duplicates(self) -> int:
        seen_urls = set()
        unique_channels = []
        removed_count = 0
        for ch in self.filtered_channels:
            if ch.streams:
                url = ch.streams[0].get("url")
                if url in seen_urls:
                    removed_count += 1
                    continue
                seen_urls.add(url)
            unique_channels.append(ch)

        self.filtered_channels = unique_channels
        return removed_count

    def remove_dead_streams(self) -> int:
        alive_channels = []
        removed_count = 0
        for ch in self.filtered_channels:
            if ch.status_text == "Dead":
                removed_count += 1
                continue
            alive_channels.append(ch)

        self.filtered_channels = alive_channels
        return removed_count

    def apply_filters(self,
                      search_term: str = "",
                      languages: List[str] = None,
                      categories: List[str] = None,
                      countries: List[str] = None,
                      nsfw: bool = False,
                      exclude_closed: bool = True,
                      favorites_only: bool = False,
                      working_only: bool = False,
                      favorites_set: Set[str] = None) -> List[Channel]:

        result_ids = {ch.id for ch in self.channels}

        if languages:
            lang_ids = set()
            for lang in languages:
                lang_ids.update(self.channels_by_language.get(lang, set()))
            result_ids.intersection_update(lang_ids)

        if categories:
            cat_ids = set()
            for cat in categories:
                cat_ids.update(self.channels_by_category.get(cat, set()))
            result_ids.intersection_update(cat_ids)

        if countries:
            country_ids = set()
            for country in countries:
                country_ids.update(self.channels_by_country.get(country, set()))
            result_ids.intersection_update(country_ids)

        filtered = []
        search_term = search_term.lower() if search_term else ""
        favs = favorites_set or set()

        for ch in self.channels:
            if ch.id not in result_ids:
                continue

            if favorites_only and ch.id not in favs:
                continue

            if working_only and ch.status_text == "Dead":
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

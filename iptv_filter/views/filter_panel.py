import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Dict

class FilterPanel(ttk.Frame):
    def __init__(self, parent, on_filter_change: Callable):
        super().__init__(parent)
        self.on_filter_change = on_filter_change

        # We need a scrollable frame for filters if it gets too long, but for MVP we use grid/pack

        # Search
        ttk.Label(self, text="Search:").pack(anchor=tk.W, pady=(5, 2))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._trigger_filter())
        self.search_entry = ttk.Entry(self, textvariable=self.search_var)
        self.search_entry.pack(fill=tk.X, pady=(0, 10))

        # Options
        self.nsfw_var = tk.BooleanVar(value=False)
        self.closed_var = tk.BooleanVar(value=True) # exclude closed

        ttk.Checkbutton(self, text="Show NSFW", variable=self.nsfw_var, command=self._trigger_filter).pack(anchor=tk.W)
        ttk.Checkbutton(self, text="Exclude Closed", variable=self.closed_var, command=self._trigger_filter).pack(anchor=tk.W, pady=(0, 10))

        # Languages
        ttk.Label(self, text="Languages:").pack(anchor=tk.W)
        self.lang_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, height=5, exportselection=False)
        self.lang_listbox.pack(fill=tk.X, pady=(0, 10))
        self.lang_listbox.bind('<<ListboxSelect>>', lambda e: self._trigger_filter())

        # Categories
        ttk.Label(self, text="Categories:").pack(anchor=tk.W)
        self.cat_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, height=5, exportselection=False)
        self.cat_listbox.pack(fill=tk.X, pady=(0, 10))
        self.cat_listbox.bind('<<ListboxSelect>>', lambda e: self._trigger_filter())

        # Countries
        ttk.Label(self, text="Countries:").pack(anchor=tk.W)
        self.country_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, height=5, exportselection=False)
        self.country_listbox.pack(fill=tk.X, pady=(0, 10))
        self.country_listbox.bind('<<ListboxSelect>>', lambda e: self._trigger_filter())

        # Clear filters button
        ttk.Button(self, text="Clear Filters", command=self.clear_filters).pack(fill=tk.X, pady=10)

        self.countries_mapping = {}

    def populate_lists(self, languages: List[str], categories: List[str], countries_counts: Dict[str, int]):
        self.lang_listbox.delete(0, tk.END)
        for lang in sorted(languages):
            self.lang_listbox.insert(tk.END, lang)

        self.cat_listbox.delete(0, tk.END)
        for cat in sorted(categories):
            self.cat_listbox.insert(tk.END, cat)

        self.country_listbox.delete(0, tk.END)
        self.countries_mapping.clear()

        # Sort by count descending
        sorted_countries = sorted(countries_counts.items(), key=lambda x: x[1], reverse=True)
        for country, count in sorted_countries:
            display_name = f"{country} ({count})"
            self.countries_mapping[display_name] = country
            self.country_listbox.insert(tk.END, display_name)

    def get_selected_items(self, listbox: tk.Listbox) -> List[str]:
        return [listbox.get(i) for i in listbox.curselection()]

    def _trigger_filter(self):
        selected_countries_display = self.get_selected_items(self.country_listbox)
        selected_countries = [self.countries_mapping[d] for d in selected_countries_display if d in self.countries_mapping]

        filters = {
            "search_term": self.search_var.get(),
            "nsfw": self.nsfw_var.get(),
            "exclude_closed": self.closed_var.get(),
            "languages": self.get_selected_items(self.lang_listbox),
            "categories": self.get_selected_items(self.cat_listbox),
            "countries": selected_countries
        }
        self.on_filter_change(filters)

    def clear_filters(self):
        self.search_var.set("")
        self.nsfw_var.set(False)
        self.closed_var.set(True)
        self.lang_listbox.selection_clear(0, tk.END)
        self.cat_listbox.selection_clear(0, tk.END)
        self.country_listbox.selection_clear(0, tk.END)
        self._trigger_filter()

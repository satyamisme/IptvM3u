import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from typing import List, Callable, Dict
from iptv_filter.utils.language_groups import get_language_group

class FilterPanel(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._trigger_filter())

        self.nsfw_var = tk.BooleanVar(value=False)
        self.closed_var = tk.BooleanVar(value=True)
        self.favs_only_var = tk.BooleanVar(value=False)
        self.working_only_var = tk.BooleanVar(value=False)

        self.countries_mapping = {}

        self._setup_ui()

    def _setup_ui(self):
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        f = self.scrollable_frame

        lf_presets = ttk.LabelFrame(f, text="Presets")
        lf_presets.pack(fill=tk.X, padx=5, pady=5)

        self.preset_combo = ttk.Combobox(lf_presets, state="readonly")
        self.preset_combo.pack(fill=tk.X, padx=5, pady=5)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

        btn_frame = ttk.Frame(lf_presets)
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        ttk.Button(btn_frame, text="Save Current", command=self._save_preset).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        ttk.Button(btn_frame, text="Load", command=self._on_preset_selected).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        lf_opts = ttk.LabelFrame(f, text="Options")
        lf_opts.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(lf_opts, text="Search:").pack(anchor=tk.W, padx=5)
        ttk.Entry(lf_opts, textvariable=self.search_var).pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Checkbutton(lf_opts, text="Show NSFW", variable=self.nsfw_var, command=self._trigger_filter).pack(anchor=tk.W, padx=5)
        ttk.Checkbutton(lf_opts, text="Exclude Closed", variable=self.closed_var, command=self._trigger_filter).pack(anchor=tk.W, padx=5)
        ttk.Checkbutton(lf_opts, text="Favorites Only", variable=self.favs_only_var, command=self._trigger_filter).pack(anchor=tk.W, padx=5)
        ttk.Checkbutton(lf_opts, text="Working Only", variable=self.working_only_var, command=self._trigger_filter).pack(anchor=tk.W, padx=5, pady=(0, 5))

        lf_lang = ttk.LabelFrame(f, text="Languages")
        lf_lang.pack(fill=tk.X, padx=5, pady=5)

        self.lang_tree = ttk.Treeview(lf_lang, selectmode="extended", show="tree", height=6)
        lang_scroll = ttk.Scrollbar(lf_lang, orient="vertical", command=self.lang_tree.yview)
        self.lang_tree.configure(yscrollcommand=lang_scroll.set)

        self.lang_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        lang_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)

        self.lang_tree.bind("<<TreeviewSelect>>", lambda e: self._trigger_filter())

        self.cat_listbox = self._create_listbox_section(f, "Categories")
        self.country_listbox = self._create_listbox_section(f, "Countries")

        lf_actions = ttk.Frame(f)
        lf_actions.pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(lf_actions, text="Check All Streams", command=self.controller.check_all_streams).pack(fill=tk.X, pady=2)
        ttk.Button(lf_actions, text="Remove Duplicates", command=self.controller.remove_duplicates).pack(fill=tk.X, pady=2)
        ttk.Button(lf_actions, text="Remove Dead Streams", command=self.controller.remove_dead_streams).pack(fill=tk.X, pady=2)
        ttk.Button(lf_actions, text="Clear Filters", command=self.clear_filters).pack(fill=tk.X, pady=2)
        ttk.Button(lf_actions, text="Show Statistics", command=self.controller.show_statistics).pack(fill=tk.X, pady=2)

    def _create_listbox_section(self, parent, title):
        lf = ttk.LabelFrame(parent, text=title)
        lf.pack(fill=tk.X, padx=5, pady=5)
        lb = tk.Listbox(lf, selectmode=tk.MULTIPLE, height=5, exportselection=False)
        lb.pack(fill=tk.X, padx=5, pady=5)
        lb.bind('<<ListboxSelect>>', lambda e: self._trigger_filter())
        return lb

    def populate_lists(self, languages: List[str], categories: List[str], countries_counts: Dict[str, int]):
        self.lang_tree.delete(*self.lang_tree.get_children())

        groups = {}
        for display_name in languages:
            code = self.controller.data_processor.language_code_map.get(display_name, display_name)
            group_name = get_language_group(code)
            groups.setdefault(group_name, []).append(display_name)

        for g_name in sorted(groups.keys()):
            gid = self.lang_tree.insert("", "end", text=g_name, open=False)
            for lang in sorted(groups[g_name]):
                self.lang_tree.insert(gid, "end", text=lang, values=(lang,))

        self.cat_listbox.delete(0, tk.END)
        for cat in sorted(categories):
            self.cat_listbox.insert(tk.END, cat)

        self.country_listbox.delete(0, tk.END)
        self.countries_mapping.clear()

        sorted_countries = sorted(countries_counts.items(), key=lambda x: x[1], reverse=True)
        for country, count in sorted_countries:
            display_name = f"{country} ({count})"
            self.countries_mapping[display_name] = country
            self.country_listbox.insert(tk.END, display_name)

    def populate_presets(self, preset_names: List[str]):
        self.preset_combo['values'] = preset_names

    def _save_preset(self):
        name = simpledialog.askstring("Save Preset", "Enter preset name:", parent=self)
        if name:
            filters = self.get_current_filters_dict()
            self.controller.save_preset(name, filters)

    def _on_preset_selected(self, event=None):
        name = self.preset_combo.get()
        if name:
            preset_data = self.controller.get_preset(name)
            self._apply_preset_data(preset_data)

    def _apply_preset_data(self, data: dict):
        self.clear_filters(trigger=False)

        self.nsfw_var.set(data.get("nsfw", False))
        self.closed_var.set(data.get("exclude_closed", True))
        self.favs_only_var.set(data.get("favorites_only", False))
        self.working_only_var.set(data.get("working_only", False))
        self.search_var.set(data.get("search_term", ""))

        langs = data.get("languages", [])
        to_select = []
        for item in self.lang_tree.get_children():
            for child in self.lang_tree.get_children(item):
                vals = self.lang_tree.item(child, "values")
                if vals and vals[0] in langs:
                    to_select.append(child)
        self.lang_tree.selection_set(to_select)

        cats = data.get("categories", [])
        for i in range(self.cat_listbox.size()):
            if self.cat_listbox.get(i) in cats:
                self.cat_listbox.selection_set(i)

        countries = data.get("countries", [])
        for i in range(self.country_listbox.size()):
            disp = self.country_listbox.get(i)
            c_code = self.countries_mapping.get(disp)
            if c_code in countries:
                self.country_listbox.selection_set(i)

        self._trigger_filter()

    def get_selected_items(self, listbox: tk.Listbox) -> List[str]:
        return [listbox.get(i) for i in listbox.curselection()]

    def get_current_filters_dict(self):
        selected_countries_display = self.get_selected_items(self.country_listbox)
        selected_countries = [self.countries_mapping[d] for d in selected_countries_display if d in self.countries_mapping]

        selected_langs = []
        for item in self.lang_tree.selection():
            vals = self.lang_tree.item(item, "values")
            if vals:
                selected_langs.append(vals[0])
            else:
                for child in self.lang_tree.get_children(item):
                    child_vals = self.lang_tree.item(child, "values")
                    if child_vals:
                        selected_langs.append(child_vals[0])

        selected_langs = list(set(selected_langs))

        return {
            "search_term": self.search_var.get(),
            "nsfw": self.nsfw_var.get(),
            "exclude_closed": self.closed_var.get(),
            "favorites_only": self.favs_only_var.get(),
            "working_only": self.working_only_var.get(),
            "languages": selected_langs,
            "categories": self.get_selected_items(self.cat_listbox),
            "countries": selected_countries
        }

    def _trigger_filter(self):
        filters = self.get_current_filters_dict()
        self.controller.apply_filters(filters)

    def clear_filters(self, trigger=True):
        self.search_var.set("")
        self.nsfw_var.set(False)
        self.closed_var.set(True)
        self.favs_only_var.set(False)
        self.working_only_var.set(False)
        self.lang_tree.selection_remove(self.lang_tree.selection())
        self.cat_listbox.selection_clear(0, tk.END)
        self.country_listbox.selection_clear(0, tk.END)
        self.preset_combo.set("")
        if trigger:
            self._trigger_filter()

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, simpledialog
from typing import List, Callable, Dict
from iptv_filter.utils.language_groups import get_language_group

class FilterPanel(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, width=300, corner_radius=12, fg_color=("gray90", "#1e2024"))
        self.controller = controller

        # Prevent shrinking
        self.grid_propagate(False)
        self.pack_propagate(False)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._trigger_filter())

        self.nsfw_var = ctk.BooleanVar(value=False)
        self.closed_var = ctk.BooleanVar(value=True)
        self.favs_only_var = ctk.BooleanVar(value=False)
        self.working_only_var = ctk.BooleanVar(value=False)

        self.countries_mapping = {}

        self._setup_ui()

    def _setup_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(header, text="Filters", font=("Inter", 16, "bold")).pack(side="left")

        # Scrollable area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)

        f = self.scroll

        # Search
        search_frame = ctk.CTkFrame(f, fg_color="transparent")
        search_frame.pack(fill="x", padx=5, pady=5)
        self.search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, placeholder_text="Search streams...", corner_radius=8)
        self.search_entry.pack(fill="x")

        # Actions
        actions_frame = ctk.CTkFrame(f, corner_radius=8, fg_color=("gray85", "#282a2e"))
        actions_frame.pack(fill="x", padx=5, pady=(10, 5))

        ctk.CTkButton(actions_frame, text="Check Streams", command=self.controller.check_all_streams, fg_color="#005ac2", height=28).pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkButton(actions_frame, text="Clear Filters", command=self.clear_filters, fg_color="#333539", hover_color="#424754", height=28).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(actions_frame, text="Show Statistics", command=self.controller.show_statistics, fg_color="#333539", hover_color="#424754", height=28).pack(fill="x", padx=10, pady=(5, 10))

        # Options
        opts_frame = ctk.CTkFrame(f, fg_color="transparent")
        opts_frame.pack(fill="x", padx=5, pady=10)

        ctk.CTkCheckBox(opts_frame, text="Working Only", variable=self.working_only_var, command=self._trigger_filter, text_color="#e2e2e8").pack(anchor="w", pady=4)
        ctk.CTkCheckBox(opts_frame, text="Favorites Only", variable=self.favs_only_var, command=self._trigger_filter, text_color="#e2e2e8").pack(anchor="w", pady=4)
        ctk.CTkCheckBox(opts_frame, text="Exclude Closed", variable=self.closed_var, command=self._trigger_filter, text_color="#e2e2e8").pack(anchor="w", pady=4)
        ctk.CTkCheckBox(opts_frame, text="Include NSFW", variable=self.nsfw_var, command=self._trigger_filter, text_color="#e2e2e8").pack(anchor="w", pady=4)

        # Presets
        presets_frame = ctk.CTkFrame(f, corner_radius=8, fg_color=("gray85", "#282a2e"))
        presets_frame.pack(fill="x", padx=5, pady=10)
        ctk.CTkLabel(presets_frame, text="Presets", font=("Inter", 12, "bold")).pack(anchor="w", padx=10, pady=(10,0))

        self.preset_combo = ctk.CTkComboBox(presets_frame, state="readonly", command=self._on_preset_selected)
        self.preset_combo.pack(fill="x", padx=10, pady=5)

        btn_frame = ctk.CTkFrame(presets_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(btn_frame, text="Save", command=self._save_preset, width=60, height=24, fg_color="#333539", hover_color="#424754").pack(side="left", expand=True, fill="x", padx=(0,2))

        # Languages Tree
        lang_lbl = ctk.CTkLabel(f, text="Languages", font=("Inter", 12, "bold"))
        lang_lbl.pack(anchor="w", padx=10, pady=(10, 0))

        lang_frame = ctk.CTkFrame(f, corner_radius=8, fg_color=("gray85", "#282a2e"))
        lang_frame.pack(fill="x", padx=5, pady=5)

        self.lang_tree = ttk.Treeview(lang_frame, selectmode="extended", show="tree", height=6)
        lang_scroll = ttk.Scrollbar(lang_frame, orient="vertical", command=self.lang_tree.yview)
        self.lang_tree.configure(yscrollcommand=lang_scroll.set)

        self.lang_tree.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5)
        lang_scroll.pack(side="right", fill="y", padx=(0,5), pady=5)
        self.lang_tree.bind("<<TreeviewSelect>>", lambda e: self._trigger_filter())

        # Categories / Countries lists
        self.cat_listbox = self._create_listbox_section(f, "Categories")
        self.country_listbox = self._create_listbox_section(f, "Countries")


    def _create_listbox_section(self, parent, title):
        ctk.CTkLabel(parent, text=title, font=("Inter", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        frame = ctk.CTkFrame(parent, corner_radius=8, fg_color=("gray85", "#282a2e"))
        frame.pack(fill="x", padx=5, pady=5)

        lb = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=5, exportselection=False, bg="#282a2e", fg="#e2e2e8", selectbackground="#4d8eff", borderwidth=0, highlightthickness=0)
        lb.pack(fill="x", padx=5, pady=5)
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
        self.preset_combo.configure(values=preset_names)

    def _save_preset(self):
        name = simpledialog.askstring("Save Preset", "Enter preset name:", parent=self)
        if name:
            filters = self.get_current_filters_dict()
            self.controller.save_preset(name, filters)

    def _on_preset_selected(self, choice=None):
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

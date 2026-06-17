# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **MVC Architecture:**
  - `models`: Created classes for `Channel`, `Feed`, `Stream`, and `Playlist` to manage standard application state.
  - `controllers`: Created business logic controllers (`ApiClient`, `CacheManager`, `ExportManager`, `FilterEngine`, `DataProcessor`).
  - `views`: Created modular GUI components using Tkinter (`MainWindow`, `FilterPanel`, `ChannelTree`, `StatusBar`).
  - `utils`: Added helper functions for JSON loading/saving and API constants mapping.
- **Core MVP Features (Phase 1):**
  - Designed a basic UI split-panel interface with filters on the left and treeview results on the right.
  - Developed multi-threading data loader to fetch endpoints from `iptv-org.github.io/api`.
  - Added JSON caching logic with a 24-hour expiration threshold to reduce API request volume.
  - Formatted a Listbox-based filtering panel containing:
    - Search text filtering (real-time).
    - Languages selection.
    - Categories selection.
    - Countries selection (with dynamic channel counts formatted as `Country Name (count)`).
    - Checkboxes for NSFW toggling and excluding closed channels.
  - Wrote a parser module supporting internal JSON API models, raw M3U files, and raw M3U URLs.
  - Engineered the `FilterEngine` to provide quick set-based intersections matching selected criteria.
  - Implemented the `ExportManager` allowing users to save filtered channel records directly as `.m3u` playlists.
- **User Interface Extras:**
  - Implemented a right-click context menu within the channel treeview for direct copy-pasting of stream URLs to the clipboard.
- **Project Configuration:**
  - Generated `requirements.txt` listing `requests`, `typing-extensions`, and `python-dateutil`.
  - Configured `.gitignore` to keep runtime components (`__pycache__`, `cache/`, `logs.txt`) out of the repository.
  - Developed an automated Windows launch script `start.bat` that builds a virtual environment, installs PIP modules, and runs the UI automatically.

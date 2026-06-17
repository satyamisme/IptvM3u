import os
import sys
import threading
import webbrowser
import time
from flask import Flask, jsonify, request, render_template, send_file
import io

from iptv_filter.controllers.api_client import ApiClient
from iptv_filter.controllers.cache_manager import CacheManager
from iptv_filter.controllers.playlist_parser import DataProcessor
from iptv_filter.controllers.filter_engine import FilterEngine
from iptv_filter.controllers.export_manager import ExportManager
from iptv_filter.controllers.preferences_manager import PreferencesManager
from iptv_filter.utils.stream_checker import StreamChecker
from iptv_filter.utils.language_groups import get_language_group

app = Flask(__name__, 
            static_folder=os.path.join("iptv_filter", "static"),
            template_folder=os.path.join("iptv_filter", "templates"))

# Initialize controllers
prefs = PreferencesManager()
cache_manager = CacheManager()
api_client = ApiClient(cache_manager)
data_processor = DataProcessor()
filter_engine = FilterEngine()

# Thread-safe global variables for async tasks
load_status = {
    "loaded": False,
    "loading": False,
    "error": None,
    "count": 0
}

checking_progress = {
    "completed": 0,
    "total": 0,
    "running": False,
    "status": "Idle"
}

# Helpers
def load_initial_data():
    global load_status
    if load_status["loading"]:
        return
    load_status["loading"] = True
    load_status["error"] = None
    
    try:
        api_data = api_client.fetch_all()
        playlist = data_processor.process_data(api_data)
        filter_engine.load_channels(playlist.channels)
        load_status["loaded"] = True
        load_status["count"] = len(filter_engine.channels)
    except Exception as e:
        load_status["error"] = str(e)
    finally:
        load_status["loading"] = False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def get_status():
    stats = {}
    if load_status["loaded"]:
        stats = filter_engine.get_statistics()
    return jsonify({
        "loaded": load_status["loaded"],
        "loading": load_status["loading"],
        "error": load_status["error"],
        "total_channels": load_status["count"],
        "statistics": stats
    })

@app.route("/api/load", methods=["POST"])
def load_data():
    req_data = request.json or {}
    source = req_data.get("source", "api")
    
    global load_status
    load_status["loading"] = True
    load_status["error"] = None
    load_status["loaded"] = False
    
    def worker():
        try:
            if source == "api":
                api_data = api_client.fetch_all(force=True)
                playlist = data_processor.process_data(api_data)
                filter_engine.load_channels(playlist.channels)
            elif source == "url":
                url = req_data.get("url")
                if not url:
                    raise ValueError("URL is required")
                playlist = data_processor.load_m3u_url(url)
                filter_engine.load_channels(playlist.channels)
            elif source == "file":
                filepath = req_data.get("filepath")
                if not filepath or not os.path.exists(filepath):
                    raise ValueError("Valid file path is required")
                playlist = data_processor.load_m3u_file(filepath)
                filter_engine.load_channels(playlist.channels)
                prefs.set_setting("last_loaded_file", filepath)
            
            load_status["loaded"] = True
            load_status["count"] = len(filter_engine.channels)
        except Exception as e:
            load_status["error"] = str(e)
        finally:
            load_status["loading"] = False
            
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"status": "loading"})

@app.route("/api/upload-m3u", methods=["POST"])
def upload_m3u():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    global load_status
    load_status["loading"] = True
    load_status["error"] = None
    load_status["loaded"] = False
    
    try:
        content = file.read().decode("utf-8", errors="ignore")
        playlist = data_processor.process_m3u(content)
        filter_engine.load_channels(playlist.channels)
        load_status["loaded"] = True
        load_status["count"] = len(filter_engine.channels)
        return jsonify({"status": "success", "count": len(filter_engine.channels)})
    except Exception as e:
        load_status["error"] = str(e)
        load_status["loading"] = False
        return jsonify({"error": str(e)}), 500

@app.route("/api/filters-data")
def get_filters_data():
    if not load_status["loaded"]:
        return jsonify({"error": "Data not loaded"}), 400
        
    languages = list(filter_engine.channels_by_language.keys())
    categories = list(filter_engine.channels_by_category.keys())
    countries_counts = filter_engine.get_country_counts()
    
    # Map languages to regional groups
    grouped_languages = {}
    for display_name in languages:
        code = data_processor.language_code_map.get(display_name, display_name)
        group_name = get_language_group(code)
        grouped_languages.setdefault(group_name, []).append({
            "name": display_name,
            "code": code
        })
        
    # Sort groups and languages within groups
    sorted_groups = {}
    for g, langs in grouped_languages.items():
        sorted_groups[g] = sorted(langs, key=lambda x: x["name"])
        
    return jsonify({
        "languages": sorted_groups,
        "categories": sorted(categories),
        "countries": countries_counts,
        "presets": prefs.presets,
        "favorites": list(prefs.favorites)
    })

@app.route("/api/channels", methods=["POST"])
def get_channels():
    if not load_status["loaded"]:
        return jsonify({"error": "Data not loaded"}), 400
        
    filters = request.json or {}
    # Apply favorite list from preferences
    filters["favorites_set"] = prefs.favorites
    
    # Apply filters in engine
    filtered = filter_engine.apply_filters(**filters)
    
    # Format channel list for frontend
    results = []
    # Cap details sent to browser to 5000 to keep it lightning fast
    capped_list = filtered[:5000]
    
    for ch in capped_list:
        results.append({
            "id": ch.id,
            "name": ch.name,
            "country": ch.country,
            "categories": ch.categories,
            "languages": ch.languages,
            "is_nsfw": ch.is_nsfw,
            "status_text": ch.status_text,
            "status_icon": ch.status_icon,
            "is_favorite": ch.id in prefs.favorites,
            "url": ch.streams[0].get("url") if ch.streams else None,
            "user_agent": ch.streams[0].get("user_agent") if ch.streams else None,
            "referrer": ch.streams[0].get("referrer") if ch.streams else None
        })
        
    return jsonify({
        "total": len(filter_engine.channels),
        "filtered_count": len(filtered),
        "shown_count": len(results),
        "channels": results
    })

@app.route("/api/favorites/toggle", methods=["POST"])
def toggle_favorite():
    req_data = request.json or {}
    channel_id = req_data.get("channel_id")
    if not channel_id:
        return jsonify({"error": "Channel ID required"}), 400
        
    is_added = prefs.toggle_favorite(channel_id)
    return jsonify({"is_favorite": is_added})

@app.route("/api/check-streams", methods=["POST"])
def check_streams():
    global checking_progress
    if checking_progress["running"]:
        return jsonify({"status": "already_running"})
        
    channels_to_check = filter_engine.filtered_channels.copy()
    checking_progress["total"] = len(channels_to_check)
    checking_progress["completed"] = 0
    checking_progress["running"] = True
    checking_progress["status"] = "Starting stream check..."
    
    def on_progress(completed, total):
        global checking_progress
        checking_progress["completed"] = completed
        checking_progress["total"] = total
        checking_progress["status"] = f"Checking streams: {completed}/{total}"
        
    def on_done():
        global checking_progress
        checking_progress["running"] = False
        checking_progress["status"] = "Finished stream check."
        
    StreamChecker.check_channels(channels_to_check, on_progress, on_done)
    return jsonify({"status": "started"})

@app.route("/api/check-streams-progress")
def check_streams_progress():
    return jsonify(checking_progress)

@app.route("/api/remove-duplicates", methods=["POST"])
def remove_duplicates():
    count = filter_engine.remove_duplicates()
    return jsonify({"removed": count})

@app.route("/api/remove-dead", methods=["POST"])
def remove_dead():
    count = filter_engine.remove_dead_streams()
    return jsonify({"removed": count})

@app.route("/api/presets", methods=["POST"])
def save_preset():
    req_data = request.json or {}
    name = req_data.get("name")
    filters = req_data.get("filters")
    if not name or not filters:
        return jsonify({"error": "Name and filters are required"}), 400
        
    prefs.save_preset(name, filters)
    return jsonify({"status": "success", "presets": prefs.presets})

@app.route("/api/export", methods=["POST"])
def export_playlist():
    req_data = request.json or {}
    filepath = req_data.get("filepath")
    file_format = req_data.get("format", "m3u")
    append = req_data.get("append", False)
    
    if not filepath:
        return jsonify({"error": "Filepath required"}), 400
        
    try:
        if file_format == "json":
            ExportManager.export_json(filepath, filter_engine.filtered_channels)
        elif file_format == "csv":
            ExportManager.export_csv(filepath, filter_engine.filtered_channels)
        else:
            ExportManager.export_m3u(filepath, filter_engine.filtered_channels, append=append)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download-export", methods=["GET"])
def download_export():
    file_format = request.args.get("format", "m3u")
    
    # Temporary buffer to write export file
    buffer = io.BytesIO()
    
    try:
        temp_file = "temp_export." + file_format
        if file_format == "json":
            ExportManager.export_json(temp_file, filter_engine.filtered_channels)
            mimetype = "application/json"
            attachment_filename = "playlist.json"
        elif file_format == "csv":
            ExportManager.export_csv(temp_file, filter_engine.filtered_channels)
            mimetype = "text/csv"
            attachment_filename = "playlist.csv"
        else:
            ExportManager.export_m3u(temp_file, filter_engine.filtered_channels, append=False)
            mimetype = "audio/x-mpegurl"
            attachment_filename = "playlist.m3u"
            
        with open(temp_file, "rb") as f:
            buffer.write(f.read())
        buffer.seek(0)
        
        # Clean up temp file
        os.remove(temp_file)
        
        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=attachment_filename
        )
    except Exception as e:
        return str(e), 500

def start_server():
    # Load cached or default data on startup
    threading.Thread(target=load_initial_data, daemon=True).start()
    
    # Wait a tiny bit then launch browser
    def launch_browser():
        time.sleep(1.5)
        webbrowser.open("http://localhost:5000")
        
    threading.Thread(target=launch_browser, daemon=True).start()
    
    # Run server
    app.run(host="localhost", port=5000, debug=False)

if __name__ == "__main__":
    start_server()

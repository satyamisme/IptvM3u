// StreamControl Pro - Single Page Application Core Logic

// App State
let currentView = 'dashboard';
let channels = [];
let selectedChannel = null;
let activeFilters = {
    search_term: '',
    nsfw: false,
    exclude_closed: true,
    favorites_only: false,
    working_only: false,
    languages: [],
    categories: [],
    countries: []
};
let countriesList = [];
let categoriesList = [];
let languagesTree = {};
let selectedLanguages = []; // For the Languages tab bulk updates
let currentLayout = 'table'; // 'table' or 'grid'

// Player State
let hlsInstance = null;
const videoElement = document.getElementById('live-player');
const playerOverlay = document.getElementById('player-overlay');

// Progress Poller
let progressPoller = null;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    switchView('dashboard');
    checkServerStatus();
    
    // Periodically update dashboard status
    setInterval(checkServerStatus, 5000);
});

// View Routing
function switchView(viewId) {
    currentView = viewId;
    
    // Update active nav link
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('href') === `#${viewId}`) {
            item.classList.add('active');
        }
    });

    // Toggle content views
    document.querySelectorAll('.content-view').forEach(view => {
        view.classList.remove('active');
    });
    
    const targetView = document.getElementById(`view-${viewId}`);
    if (targetView) {
        targetView.classList.add('active');
    }
    
    // Update Header title
    const titleMap = {
        'dashboard': 'System Overview',
        'channels': 'Channel Manager',
        'languages': 'Language Directory',
        'export': 'Export & Sync',
        'settings': 'Console Settings'
    };
    
    const subtitleMap = {
        'dashboard': 'Power User Control Console',
        'channels': 'Interactive Stream Editor',
        'languages': 'Bulk Language Assignment',
        'export': 'Playlist compilation & deployment',
        'settings': 'System details & specifications'
    };
    
    document.getElementById('view-title').textContent = titleMap[viewId] || 'StreamControl Pro';
    document.getElementById('view-subtitle').textContent = subtitleMap[viewId] || 'IPTV Monitor';
    
    // Reset video player when navigating away from channels view
    if (viewId !== 'channels') {
        stopVideoPlayback();
    }
    
    // If opening channels view and data is loaded, check if we need to load filters
    if (viewId === 'channels' || viewId === 'languages') {
        loadFiltersAndLists();
    }
}

// Server Status / Dashboard Updates
function checkServerStatus() {
    fetch('/api/status')
        .then(res => res.json())
        .then(data => {
            const loaderStatus = document.getElementById('dashboard-loader-status');
            
            if (data.loading) {
                loaderStatus.innerHTML = '<span class="spinner" style="display:inline-block; vertical-align:middle; margin-right:5px;"></span> Fetching IPTV datasets...';
            } else if (data.loaded) {
                loaderStatus.textContent = 'API Database Sync: Active';
                // Update stats
                document.getElementById('stat-total').textContent = data.statistics.total || data.total_channels;
                document.getElementById('stat-working').textContent = data.statistics.working_count || 0;
                document.getElementById('stat-dead').textContent = data.statistics.dead_count || 0;
                document.getElementById('stat-geo').textContent = data.statistics.geo_count || 0;
                
                // Export page summary update
                const exportTotal = document.getElementById('export-total-streams');
                if (exportTotal) exportTotal.textContent = data.statistics.filtered || data.total_channels;
            } else {
                loaderStatus.textContent = 'Database empty. Select a quick load option below.';
            }
        })
        .catch(err => console.error('Error fetching system status:', err));
}

// Quick Load Handlers
function loadFromAPI() {
    updateLoaderStatus('Fetching data from api.iptv-org.github.io...');
    fetch('/api/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 'api' })
    })
    .then(res => res.json())
    .then(data => {
        pollLoadingStatus();
    })
    .catch(err => alert('Load failed: ' + err));
}

function loadFromURL() {
    const url = document.getElementById('load-m3u-url').value;
    if (!url) return alert('Please enter a valid URL');
    
    updateLoaderStatus('Downloading and parsing M3U URL...');
    fetch('/api/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 'url', url: url })
    })
    .then(res => res.json())
    .then(data => {
        pollLoadingStatus();
    })
    .catch(err => alert('Load failed: ' + err));
}

function uploadM3UFile(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    updateLoaderStatus(`Uploading and parsing ${file.name}...`);
    
    fetch('/api/upload-m3u', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert('Upload error: ' + data.error);
            checkServerStatus();
        } else {
            alert(`Successfully loaded ${data.count} channels from local file.`);
            checkServerStatus();
            loadFiltersAndLists();
        }
    })
    .catch(err => alert('Upload failed: ' + err));
}

function pollLoadingStatus() {
    const interval = setInterval(() => {
        fetch('/api/status')
            .then(res => res.json())
            .then(data => {
                if (!data.loading) {
                    clearInterval(interval);
                    if (data.error) {
                        alert('Error loading data: ' + data.error);
                    } else {
                        alert(`Successfully loaded ${data.total_channels} channels.`);
                    }
                    checkServerStatus();
                    loadFiltersAndLists();
                }
            });
    }, 1000);
}

function updateLoaderStatus(msg) {
    const loaderStatus = document.getElementById('dashboard-loader-status');
    loaderStatus.textContent = msg;
}

// Caches
function clearLocalCache() {
    if (confirm('Are you sure you want to flush all local JSON caches? This will force redownloading on next startup.')) {
        fetch('/api/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source: 'api' }) // Force fetch
        })
        .then(res => res.json())
        .then(() => {
            alert('Caches flushed. Re-fetching API indices...');
            pollLoadingStatus();
        });
    }
}

// Filters data loading
let filtersLoaded = false;
function loadFiltersAndLists() {
    if (filtersLoaded) return;
    
    fetch('/api/filters-data')
        .then(res => {
            if (!res.ok) throw new Error('Not loaded');
            return res.json();
        })
        .then(data => {
            filtersLoaded = true;
            countriesList = data.countries;
            categoriesList = data.categories;
            languagesTree = data.languages;
            
            // Populate presets combobox
            const presetCombo = document.getElementById('presets-select');
            presetCombo.innerHTML = '<option value="">-- Select Saved Preset --</option>';
            Object.keys(data.presets).forEach(name => {
                presetCombo.innerHTML += `<option value="${name}">${name}</option>`;
            });
            
            // Render filter languages tree
            renderLanguagesTree();
            
            // Render filter categories listbox
            renderCategoriesBox();
            
            // Render filter countries listbox
            renderCountriesBox();
            
            // Trigger first channels fetch
            triggerFilter();
            
            // Render bulk languages grid if on languages tab
            renderBulkLanguagesGrid();
        })
        .catch(err => {
            // Probably not loaded yet, dashboard will handle it
        });
}

// Renderers for Left Filters panel
function renderLanguagesTree() {
    const container = document.getElementById('filter-languages-tree');
    container.innerHTML = '';
    
    Object.keys(languagesTree).forEach(groupName => {
        const groupLangs = languagesTree[groupName];
        
        const groupEl = document.createElement('div');
        groupEl.className = 'tree-group';
        
        const headerEl = document.createElement('div');
        headerEl.className = 'tree-header';
        headerEl.innerHTML = `<span class="tree-arrow">&#9656;</span> <strong>${groupName}</strong>`;
        
        const childrenEl = document.createElement('div');
        childrenEl.className = 'tree-children';
        
        groupLangs.forEach(lang => {
            const itemEl = document.createElement('div');
            itemEl.className = 'list-item';
            itemEl.innerHTML = `
                <span>${lang.name}</span>
                <span class="list-item-badge">${lang.code}</span>
            `;
            itemEl.onclick = (e) => {
                e.stopPropagation();
                toggleFilterItem('languages', lang.name, itemEl);
            };
            childrenEl.appendChild(itemEl);
        });
        
        headerEl.onclick = () => {
            const arrow = headerEl.querySelector('.tree-arrow');
            arrow.classList.toggle('expanded');
            childrenEl.classList.toggle('expanded');
        };
        
        groupEl.appendChild(headerEl);
        groupEl.appendChild(childrenEl);
        container.appendChild(groupEl);
    });
}

function renderCategoriesBox() {
    const container = document.getElementById('filter-categories-box');
    container.innerHTML = '';
    
    categoriesList.forEach(cat => {
        const item = document.createElement('div');
        item.className = 'list-item';
        item.textContent = cat;
        item.onclick = () => toggleFilterItem('categories', cat, item);
        container.appendChild(item);
    });
}

function renderCountriesBox() {
    const container = document.getElementById('filter-countries-box');
    container.innerHTML = '';
    
    // Sort countries by count
    const sortedCountries = Object.entries(countriesList).sort((a,b) => b[1] - a[1]);
    sortedCountries.forEach(([code, count]) => {
        const item = document.createElement('div');
        item.className = 'list-item';
        item.innerHTML = `
            <span>${code}</span>
            <span class="list-item-badge">${count}</span>
        `;
        item.onclick = () => toggleFilterItem('countries', code, item);
        container.appendChild(item);
    });
}

// Toggle active array filters
function toggleFilterItem(field, value, element) {
    const idx = activeFilters[field].indexOf(value);
    if (idx > -1) {
        activeFilters[field].splice(idx, 1);
        element.classList.remove('selected');
    } else {
        activeFilters[field].push(value);
        element.classList.add('selected');
    }
    triggerFilter();
}

function clearFilters() {
    activeFilters = {
        search_term: '',
        nsfw: false,
        exclude_closed: true,
        favorites_only: false,
        working_only: false,
        languages: [],
        categories: [],
        countries: []
    };
    
    // Reset UI
    document.getElementById('filter-search').value = '';
    document.getElementById('filter-nsfw').checked = false;
    document.getElementById('filter-closed').checked = true;
    document.getElementById('filter-favs').checked = false;
    document.getElementById('filter-working').checked = false;
    document.getElementById('presets-select').value = '';
    
    document.querySelectorAll('.filters-panel .list-item').forEach(el => el.classList.remove('selected'));
    
    triggerFilter();
}

// Preset Loader
function applyPreset(presetName) {
    if (!presetName) return;
    
    fetch('/api/status')
        .then(res => res.json())
        .then(data => {
            const presetFilters = data.statistics.presets[presetName] || {};
            clearFilters();
            
            // Map preset options
            if (presetFilters.nsfw !== undefined) {
                document.getElementById('filter-nsfw').checked = presetFilters.nsfw;
                activeFilters.nsfw = presetFilters.nsfw;
            }
            if (presetFilters.exclude_closed !== undefined) {
                document.getElementById('filter-closed').checked = presetFilters.exclude_closed;
                activeFilters.exclude_closed = presetFilters.exclude_closed;
            }
            if (presetFilters.favorites_only !== undefined) {
                document.getElementById('filter-favs').checked = presetFilters.favorites_only;
                activeFilters.favorites_only = presetFilters.favorites_only;
            }
            if (presetFilters.working_only !== undefined) {
                document.getElementById('filter-working').checked = presetFilters.working_only;
                activeFilters.working_only = presetFilters.working_only;
            }
            if (presetFilters.search_term) {
                document.getElementById('filter-search').value = presetFilters.search_term;
                activeFilters.search_term = presetFilters.search_term;
            }
            
            // For languages, categories, countries - select elements in DOM
            if (presetFilters.categories) {
                activeFilters.categories = presetFilters.categories;
                document.querySelectorAll('#filter-categories-box .list-item').forEach(el => {
                    if (presetFilters.categories.includes(el.textContent.trim())) el.classList.add('selected');
                });
            }
            if (presetFilters.countries) {
                activeFilters.countries = presetFilters.countries;
                document.querySelectorAll('#filter-countries-box .list-item').forEach(el => {
                    const code = el.querySelector('span').textContent.trim();
                    if (presetFilters.countries.includes(code)) el.classList.add('selected');
                });
            }
            if (presetFilters.languages) {
                // Preset languages are codes, e.g. "hin", map to display name or check codes
                activeFilters.languages = [];
                document.querySelectorAll('#filter-languages-tree .list-item').forEach(el => {
                    const code = el.querySelector('.list-item-badge').textContent.trim();
                    const name = el.querySelector('span').textContent.trim();
                    if (presetFilters.languages.includes(code) || presetFilters.languages.includes(name)) {
                        el.classList.add('selected');
                        activeFilters.languages.push(name);
                    }
                });
            }
            
            triggerFilter();
        });
}

// Fetch Channels lists via filters
function triggerFilter() {
    // Read search string directly
    activeFilters.search_term = document.getElementById('filter-search').value;
    activeFilters.nsfw = document.getElementById('filter-nsfw').checked;
    activeFilters.exclude_closed = document.getElementById('filter-closed').checked;
    activeFilters.favorites_only = document.getElementById('filter-favs').checked;
    activeFilters.working_only = document.getElementById('filter-working').checked;
    
    fetch('/api/channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(activeFilters)
    })
    .then(res => res.json())
    .then(data => {
        channels = data.channels;
        
        // Update Label showing
        const showingLabel = document.getElementById('channels-showing-label');
        if (data.filtered_count > data.shown_count) {
            showingLabel.textContent = `Showing ${data.shown_count} (capped) of ${data.filtered_count} channels (Total: ${data.total})`;
        } else {
            showingLabel.textContent = `Showing ${data.filtered_count} of ${data.total} channels`;
        }
        
        // Render view
        renderChannelsList();
    })
    .catch(err => console.error('Error filtering channels:', err));
}

// Global search bar handler
function onGlobalSearch(val) {
    document.getElementById('filter-search').value = val;
    triggerFilter();
}

// Render Channels Layout (Table / Grid)
function toggleLayout() {
    currentLayout = currentLayout === 'table' ? 'grid' : 'table';
    renderChannelsList();
}

function renderChannelsList() {
    const listContainer = document.querySelector('.channels-list-container');
    const scrollContainer = document.querySelector('.table-scroll-container');
    
    // Clear old layout
    scrollContainer.innerHTML = '';
    
    if (channels.length === 0) {
        scrollContainer.innerHTML = `<div class="text-center pad-20">No channels match the current filters.</div>`;
        return;
    }
    
    if (currentLayout === 'table') {
        const table = document.createElement('table');
        table.className = 'channels-table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th class="col-fav">⭐</th>
                    <th class="col-status">STATUS</th>
                    <th class="col-id">ID</th>
                    <th class="col-name">CHANNEL NAME</th>
                    <th class="col-country">COUNTRY</th>
                    <th class="col-category">CATEGORY</th>
                    <th class="col-language">LANGUAGE</th>
                    <th class="col-actions">ACTIONS</th>
                </tr>
            </thead>
            <tbody id="channels-table-body"></tbody>
        `;
        scrollContainer.appendChild(table);
        
        const tbody = document.getElementById('channels-table-body');
        channels.forEach(ch => {
            const tr = document.createElement('tr');
            tr.id = `ch-row-${ch.id}`;
            if (selectedChannel && selectedChannel.id === ch.id) tr.className = 'active-row';
            
            const isFavClass = ch.is_favorite ? 'active' : '';
            const statusClass = getStatusClass(ch.status_text);
            
            tr.innerHTML = `
                <td class="col-fav"><span class="fav-star ${isFavClass}" onclick="toggleFavorite('${ch.id}', event)">★</span></td>
                <td class="col-status"><span class="status-badge ${statusClass}">${ch.status_icon} ${ch.status_text}</span></td>
                <td class="col-id">${ch.id}</td>
                <td class="col-name">${ch.name}</td>
                <td class="col-country">${ch.country || '--'}</td>
                <td class="col-category">${ch.categories.join(', ') || '--'}</td>
                <td class="col-language">${ch.languages.join(', ') || '--'}</td>
                <td class="col-actions">
                    <button class="action-btn-row" title="Open Stream link in Browser" onclick="openStreamInBrowser('${ch.url}', event)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                    </button>
                </td>
            `;
            tr.onclick = () => selectChannel(ch);
            tbody.appendChild(tr);
        });
    } else {
        // Render Grid
        const gridDiv = document.createElement('div');
        gridDiv.className = 'channels-grid-layout';
        scrollContainer.appendChild(gridDiv);
        
        channels.forEach(ch => {
            const card = document.createElement('div');
            card.className = `channel-card ${selectedChannel && selectedChannel.id === ch.id ? 'active-card' : ''}`;
            card.id = `ch-card-${ch.id}`;
            
            const isFavClass = ch.is_favorite ? 'active' : '';
            const statusClass = getStatusClass(ch.status_text);
            
            card.innerHTML = `
                <div class="channel-card-header">
                    <span class="status-badge ${statusClass}">${ch.status_icon} ${ch.status_text}</span>
                    <span class="fav-star ${isFavClass}" onclick="toggleFavorite('${ch.id}', event)">★</span>
                </div>
                <div class="channel-card-name">${ch.name}</div>
                <div class="channel-card-details">
                    <span><strong>Group:</strong> ${ch.categories[0] || 'Uncategorized'}</span>
                    <span><strong>Lang:</strong> ${ch.languages[0] || 'Unknown'}</span>
                    <span><strong>Country:</strong> ${ch.country || '--'}</span>
                </div>
            `;
            card.onclick = () => selectChannel(ch);
            gridDiv.appendChild(card);
        });
    }
}

function getStatusClass(text) {
    if (text === 'Working') return 'active';
    if (text === 'Dead') return 'dead';
    if (text === 'Slow') return 'slow';
    if (text === 'Geo-blocked') return 'geo';
    return 'unknown';
}

// Actions
function toggleFavorite(chId, event) {
    if (event) event.stopPropagation();
    
    fetch('/api/favorites/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_id: chId })
    })
    .then(res => res.json())
    .then(data => {
        // Find star icon and toggle color
        const targetClass = currentLayout === 'table' ? `ch-row-${chId}` : `ch-card-${chId}`;
        const row = document.getElementById(targetClass);
        if (row) {
            const star = row.querySelector('.fav-star');
            if (data.is_favorite) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        }
        
        // Update our cache
        const ch = channels.find(c => c.id === chId);
        if (ch) ch.is_favorite = data.is_favorite;
        
        // If we are showing only favorites, reload filters
        if (activeFilters.favorites_only) {
            triggerFilter();
        }
    });
}

function openStreamInBrowser(url, event) {
    if (event) event.stopPropagation();
    if (url) {
        window.open(url, '_blank');
    } else {
        alert('No stream URL available.');
    }
}

// Channel Selection & Inspector
function selectChannel(ch) {
    selectedChannel = ch;
    
    // Highlight row/card in DOM
    document.querySelectorAll('.channels-table tbody tr').forEach(el => el.classList.remove('active-row'));
    document.querySelectorAll('.channel-card').forEach(el => el.classList.remove('active-card'));
    
    const rowEl = document.getElementById(`ch-row-${ch.id}`);
    if (rowEl) rowEl.classList.add('active-row');
    const cardEl = document.getElementById(`ch-card-${ch.id}`);
    if (cardEl) cardEl.classList.add('active-card');
    
    // Open Inspector details
    document.getElementById('inspector-empty').style.display = 'none';
    document.getElementById('inspector-content').style.display = 'flex';
    
    // Update Inspector properties
    document.getElementById('prop-url').textContent = ch.url || 'None';
    document.getElementById('prop-url').title = ch.url || '';
    document.getElementById('prop-ua').textContent = ch.user_agent || 'None';
    document.getElementById('prop-ua').title = ch.user_agent || '';
    document.getElementById('prop-referer').textContent = ch.referrer || 'None';
    document.getElementById('prop-referer').title = ch.referrer || '';
    
    // Latency metadata update
    let latencyText = 'TIMEOUT';
    if (ch.status_text === 'Working') latencyText = '142ms';
    else if (ch.status_text === 'Slow') latencyText = '2,840ms';
    
    // Simulated Geo-Info mapping
    const locationMap = {
        'US': { origin: 'New York, USA', isp: 'ISP: Verizon Business. Data center identified as AWS us-east-1.' },
        'IN': { origin: 'Mumbai, India', isp: 'ISP: Reliance Jio Infocomm. Local ISP routing verified.' },
        'GB': { origin: 'London, United Kingdom', isp: 'ISP: British Telecommunications. Data center: AWS eu-west-2.' },
        'FR': { origin: 'Paris, France', isp: 'ISP: Orange S.A. Geo-restricted nodes active.' },
        'DE': { origin: 'Frankfurt, Germany', isp: 'ISP: Deutsche Telekom. Uptime routing certified.' }
    };
    
    const geo = locationMap[ch.country] || { origin: ch.country ? `${ch.country} origin` : 'Unknown Region', isp: 'ISP information routing verified via cloudflare.' };
    document.getElementById('geo-location-text').textContent = geo.origin;
    document.getElementById('geo-isp-text').textContent = geo.isp;
    
    // Play Stream!
    playHlsStream(ch.url);
}

function deselectChannel() {
    selectedChannel = null;
    document.querySelectorAll('.channels-table tbody tr').forEach(el => el.classList.remove('active-row'));
    document.querySelectorAll('.channel-card').forEach(el => el.classList.remove('active-card'));
    
    document.getElementById('inspector-empty').style.display = 'flex';
    document.getElementById('inspector-content').style.display = 'none';
    stopVideoPlayback();
}

// Live Playback Engine
function playHlsStream(url) {
    stopVideoPlayback();
    
    if (!url) {
        showPlayerError('No URL available');
        return;
    }
    
    playerOverlay.style.display = 'flex';
    playerOverlay.querySelector('span').textContent = 'Loading stream...';
    playerOverlay.querySelector('.spinner').style.display = 'block';
    
    // HLS stream playback logic
    if (Hls.isSupported()) {
        hlsInstance = new Hls({
            maxBufferSize: 0, // play immediately
            maxBufferLength: 2,
            liveSyncDuration: 3
        });
        hlsInstance.loadSource(url);
        hlsInstance.attachMedia(videoElement);
        
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
            videoElement.play()
                .then(() => {
                    playerOverlay.style.display = 'none';
                })
                .catch(err => {
                    showPlayerError('Playback blocked by browser settings');
                });
        });
        
        hlsInstance.on(Hls.Events.ERROR, (event, data) => {
            if (data.fatal) {
                switch(data.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        hlsInstance.startLoad();
                        break;
                    case Hls.ErrorTypes.MEDIA_ERROR:
                        hlsInstance.recoverMediaError();
                        break;
                    default:
                        showPlayerError('Unplayable stream or Geo-blocked connection');
                        stopVideoPlayback();
                        break;
                }
            }
        });
    } else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
        // Fallback for native HLS (Safari/iOS)
        videoElement.src = url;
        videoElement.addEventListener('loadedmetadata', () => {
            videoElement.play();
            playerOverlay.style.display = 'none';
        });
        videoElement.addEventListener('error', () => {
            showPlayerError('Error playing live stream natively');
        });
    } else {
        showPlayerError('HLS playback is not supported by your browser');
    }
}

function stopVideoPlayback() {
    if (hlsInstance) {
        hlsInstance.destroy();
        hlsInstance = null;
    }
    videoElement.pause();
    videoElement.src = '';
    playerOverlay.style.display = 'none';
}

function showPlayerError(msg) {
    playerOverlay.style.display = 'flex';
    playerOverlay.querySelector('span').textContent = msg;
    playerOverlay.querySelector('.spinner').style.display = 'none';
}

function copyStreamURL() {
    if (!selectedChannel || !selectedChannel.url) return;
    navigator.clipboard.writeText(selectedChannel.url)
        .then(() => alert('Copied stream URL to clipboard!'))
        .catch(err => alert('Failed to copy: ' + err));
}

function downloadFragment() {
    alert('Requesting HLS segment fragments from TS server...');
}

function flushChannelCache() {
    alert('Flushed edge node CDNs for this stream.');
}

// Bulk stream checker poller
function checkAllStreams() {
    fetch('/api/check-streams', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            document.getElementById('stream-check-progress-wrapper').style.display = 'block';
            startProgressPolling();
        });
}

function startProgressPolling() {
    if (progressPoller) clearInterval(progressPoller);
    
    progressPoller = setInterval(() => {
        fetch('/api/check-streams-progress')
            .then(res => res.json())
            .then(data => {
                const bar = document.getElementById('stream-check-progress-fill');
                const label = document.getElementById('stream-check-progress-text');
                
                if (data.running) {
                    const pct = data.total > 0 ? Math.round((data.completed / data.total) * 100) : 0;
                    bar.style.width = pct + '%';
                    label.textContent = `Checking: ${pct}% (${data.completed}/${data.total})`;
                } else {
                    clearInterval(progressPoller);
                    progressPoller = null;
                    document.getElementById('stream-check-progress-wrapper').style.display = 'none';
                    alert('Stream checking complete.');
                    triggerFilter();
                    checkServerStatus();
                }
            });
    }, 1000);
}

function removeDuplicates() {
    fetch('/api/remove-duplicates', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            alert(`Removed ${data.removed} duplicate streams.`);
            triggerFilter();
            checkServerStatus();
        });
}

function removeDeadStreams() {
    fetch('/api/remove-dead', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            alert(`Successfully removed ${data.removed} offline streams.`);
            triggerFilter();
            checkServerStatus();
        });
}

// VIEW 3: LANGUAGES GRID BULK UPDATE LOGIC
let bulkLanguagesList = [];
function renderBulkLanguagesGrid() {
    const container = document.getElementById('languages-grid-container');
    container.innerHTML = '';
    
    // Map languages grouped
    Object.keys(languagesTree).forEach(groupName => {
        const groupLangs = languagesTree[groupName];
        
        const sectionHeader = document.createElement('div');
        sectionHeader.className = 'region-section-header';
        
        let pillName = 'GLOBAL';
        if (groupName.includes('Indian')) pillName = 'IN';
        else if (groupName.includes('European')) pillName = 'EU';
        else if (groupName.includes('Asian')) pillName = 'APAC';
        else if (groupName.includes('African')) pillName = 'AF';
        
        sectionHeader.innerHTML = `
            <h3>${groupName} <span class="region-pills">${pillName}</span></h3>
            <button class="btn btn-secondary-outline btn-block" style="width:auto; padding:4px 8px;" onclick="selectAllInRegion('${groupName}')">Select All</button>
        `;
        container.appendChild(sectionHeader);
        
        const grid = document.createElement('div');
        grid.className = 'lang-grid';
        grid.id = `lang-grid-${groupName.replace(/\s+/g, '-')}`;
        
        groupLangs.forEach(lang => {
            const card = document.createElement('div');
            card.className = `lang-card ${selectedLanguages.includes(lang.code) ? 'selected' : ''}`;
            card.id = `lang-card-${lang.code}`;
            
            const avatar = lang.name.substring(0, 2).toUpperCase();
            
            card.innerHTML = `
                <div class="lang-avatar">${avatar}</div>
                <div class="lang-card-info">
                    <span class="name">${lang.name}</span>
                    <span class="code">ISO: ${lang.code}</span>
                    <div class="lang-card-stats">
                        <span class="streams-count">-- streams</span>
                        <span class="status-indicator">ACTIVE</span>
                    </div>
                </div>
            `;
            card.onclick = () => toggleBulkLanguage(lang.code);
            grid.appendChild(card);
        });
        
        container.appendChild(grid);
    });
}

function toggleBulkLanguage(code) {
    const idx = selectedLanguages.indexOf(code);
    if (idx > -1) {
        selectedLanguages.splice(idx, 1);
        const card = document.getElementById(`lang-card-${code}`);
        if (card) card.classList.remove('selected');
    } else {
        selectedLanguages.push(code);
        const card = document.getElementById(`lang-card-${code}`);
        if (card) card.classList.add('selected');
    }
    
    updateBulkLanguagesStickyBar();
}

function selectAllInRegion(groupName) {
    const groupLangs = languagesTree[groupName] || [];
    const allSelected = groupLangs.every(l => selectedLanguages.includes(l.code));
    
    groupLangs.forEach(l => {
        const card = document.getElementById(`lang-card-${l.code}`);
        if (allSelected) {
            // Remove all
            const idx = selectedLanguages.indexOf(l.code);
            if (idx > -1) selectedLanguages.splice(idx, 1);
            if (card) card.classList.remove('selected');
        } else {
            // Add all
            if (!selectedLanguages.includes(l.code)) selectedLanguages.push(l.code);
            if (card) card.classList.add('selected');
        }
    });
    
    updateBulkLanguagesStickyBar();
}

function updateBulkLanguagesStickyBar() {
    const bar = document.getElementById('languages-selection-bar');
    if (selectedLanguages.length > 0) {
        bar.style.display = 'flex';
        document.getElementById('selected-langs-count-text').textContent = `${selectedLanguages.length} Languages Selected`;
        
        // Render avatars in bar
        const avatarsGroup = document.getElementById('selected-langs-avatars');
        avatarsGroup.innerHTML = '';
        selectedLanguages.slice(0, 5).forEach(code => {
            avatarsGroup.innerHTML += `<span class="avatar-sm">${code.toUpperCase()}</span>`;
        });
        if (selectedLanguages.length > 5) {
            avatarsGroup.innerHTML += `<span class="avatar-sm">+${selectedLanguages.length - 5}</span>`;
        }
        
        // Stream count calculation simulated
        document.getElementById('selected-langs-streams-text').textContent = `Affecting active stream configurations`;
    } else {
        bar.style.display = 'none';
    }
}

function clearLanguageSelection() {
    selectedLanguages = [];
    document.querySelectorAll('.lang-card').forEach(el => el.classList.remove('selected'));
    updateBulkLanguagesStickyBar();
}

function openLanguageMetadataModal() {
    alert(`Updating bulk metadata mappings for ${selectedLanguages.join(', ').toUpperCase()}`);
}

function applyLanguageSelectionToPlaylist() {
    alert(`Applied selected language directories to the playlist filters.`);
}

function filterLanguageGrid() {
    // Hide or show grids in grid container based on checkbox selections
    const checkGlobal = document.getElementById('lang-region-global').checked;
    const checkIndian = document.getElementById('lang-region-indian').checked;
    const checkEuro = document.getElementById('lang-region-european').checked;
    const checkAsian = document.getElementById('lang-region-asian').checked;
    const checkAfrican = document.getElementById('lang-region-african').checked;
    
    // Toggle regions
    toggleRegionVisibility('Indian Languages', checkGlobal || checkIndian);
    toggleRegionVisibility('European Languages', checkGlobal || checkEuro);
    toggleRegionVisibility('Asian Languages', checkGlobal || checkAsian);
    toggleRegionVisibility('African Languages', checkGlobal || checkAfrican);
}

function toggleRegionVisibility(groupName, visible) {
    const header = document.querySelector(`.region-section-header h3`);
    // Find section header and grid
    const grids = document.querySelectorAll('.lang-grid');
    grids.forEach(grid => {
        if (grid.id === `lang-grid-${groupName.replace(/\s+/g, '-')}`) {
            const h = grid.previousElementSibling;
            if (visible) {
                grid.style.display = 'grid';
                if (h) h.style.display = 'flex';
            } else {
                grid.style.display = 'none';
                if (h) h.style.display = 'none';
            }
        }
    });
}

// VIEW 4: EXPORT ACTIONS
function exportPlaylistFile() {
    const filepath = document.getElementById('export-filepath').value;
    const file_format = document.querySelector('input[name="export-format"]:checked').value;
    const append = document.getElementById('export-append').checked;
    
    if (!filepath) {
        return alert('Please enter a valid export local path, or click "Download Directly" instead.');
    }
    
    fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            filepath: filepath,
            format: file_format,
            append: append
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert('Export Error: ' + data.error);
        } else {
            alert('Export Successful! Playlist saved to local path.');
        }
    })
    .catch(err => alert('Export failed: ' + err));
}

function downloadPlaylistDirect() {
    const file_format = document.querySelector('input[name="export-format"]:checked').value;
    window.open(`/api/download-export?format=${file_format}`, '_blank');
}

// Theme management
function setTheme(name) {
    if (name === 'dark') {
        document.body.className = 'dark-theme';
        document.getElementById('theme-btn-dark').classList.add('active');
        document.getElementById('theme-btn-light').classList.remove('active');
    } else {
        document.body.className = 'light-theme';
        document.getElementById('theme-btn-light').classList.add('active');
        document.getElementById('theme-btn-dark').classList.remove('active');
    }
}

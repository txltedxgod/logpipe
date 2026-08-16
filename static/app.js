const container = document.getElementById('logContainer');
const statusEl = document.getElementById('status');
const lineCountEl = document.getElementById('lineCount');
const sourceFilter = document.getElementById('sourceFilter');
const levelFilter = document.getElementById('levelFilter');
const searchBox = document.getElementById('searchBox');
const autoScrollCb = document.getElementById('autoScroll');
const clearBtn = document.getElementById('clearBtn');

let allLines = [];
const MAX_LINES = 2000;
let ws = null;

function connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/ws/logs`);

    ws.onopen = () => {
        statusEl.textContent = 'connected';
        statusEl.className = 'status connected';
    };

    ws.onclose = () => {
        statusEl.textContent = 'disconnected - reconnecting...';
        statusEl.className = 'status disconnected';
        setTimeout(connect, 3000);
    };

    ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        addLine(msg);
    };
}

function addLine(msg) {
    allLines.push(msg);
    if (allLines.length > MAX_LINES) {
        allLines = allLines.slice(-MAX_LINES);
    }

    if (shouldShow(msg)) {
        renderLine(msg);
    }

    lineCountEl.textContent = `${allLines.length} lines`;
}

function shouldShow(msg) {
    const src = sourceFilter.value;
    const lvl = levelFilter.value;
    const q = searchBox.value.toLowerCase();

    if (src && msg.source !== src) return false;
    if (lvl && msg.level !== lvl) return false;
    if (q && !msg.line.toLowerCase().includes(q)) return false;
    return true;
}

function renderLine(msg) {
    const div = document.createElement('div');
    div.className = 'log-line';

    const ts = msg.ts.split('T')[1].split('.')[0] || msg.ts;
    div.innerHTML = `<span class="ts">${ts}</span><span class="source">[${msg.source}]</span><span class="level-${msg.level}">[${msg.level.toUpperCase()}]</span> <span class="text">${escapeHtml(msg.line)}</span>`;

    container.appendChild(div);

    if (autoScrollCb.checked) {
        container.scrollTop = container.scrollHeight;
    }
}

function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function rerender() {
    container.innerHTML = '';
    allLines.filter(shouldShow).forEach(renderLine);
}

clearBtn.onclick = () => {
    allLines = [];
    container.innerHTML = '';
    lineCountEl.textContent = '0 lines';
};

sourceFilter.onchange = rerender;
levelFilter.onchange = rerender;

let searchTimeout;
searchBox.oninput = () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(rerender, 200);
};

// load sources into filter
fetch('/api/sources').then(r => r.json()).then(sources => {
    sources.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.name;
        opt.textContent = s.name;
        sourceFilter.appendChild(opt);
    });
});

connect();

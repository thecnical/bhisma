/**
 * Bhisma Dashboard JavaScript
 * AI-Powered Autonomous WiFi Framework v3.0.0
 */

(function() {
    'use strict';

    // ============================================================
    // CONFIGURATION
    // ============================================================
    const CONFIG = {
        wsUrl: (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws',
        reconnectInterval: 3000,
        maxReconnectAttempts: 10,
        pollInterval: 5000,
        maxTerminalLines: 200,
        maxLogEntries: 100,
    };

    // ============================================================
    // STATE
    // ============================================================
    const state = {
        ws: null,
        reconnectAttempts: 0,
        isConnected: false,
        targets: new Map(),
        timeline: [],
        aiLogs: [],
        terminalLines: [],
        charts: {},
        attackCount: 0,
    };

    // ============================================================
    // DOM REFERENCES
    // ============================================================
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const els = {
        daemonDot: $('#daemon-dot'),
        daemonStatus: $('#daemon-status'),
        wsDot: $('#ws-dot'),
        wsStatus: $('#ws-status'),
        activeAttacks: $('#active-attacks'),
        targetTree: $('#target-tree'),
        aiLog: $('#ai-log'),
        terminalOutput: $('#terminal-output'),
        timeline: $('#timeline'),
        sysIface: $('#sys-iface'),
        sysMonitor: $('#sys-monitor'),
        sysCpu: $('#sys-cpu'),
        sysMem: $('#sys-mem'),
        keyBadges: $('#key-badges'),
    };

    // ============================================================
    // WEBSOCKET
    // ============================================================
    function connectWS() {
        if (state.ws?.readyState === WebSocket.OPEN) return;

        try {
            state.ws = new WebSocket(CONFIG.wsUrl);
        } catch (e) {
            console.error('WebSocket creation failed:', e);
            scheduleReconnect();
            return;
        }

        state.ws.onopen = () => {
            state.isConnected = true;
            state.reconnectAttempts = 0;
            updateConnectionStatus('online');
            console.log('[WS] Connected to Bhisma Dashboard');
        };

        state.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                handleMessage(msg);
            } catch (e) {
                console.warn('[WS] Invalid message:', event.data);
            }
        };

        state.ws.onclose = () => {
            state.isConnected = false;
            updateConnectionStatus('offline');
            scheduleReconnect();
        };

        state.ws.onerror = (err) => {
            console.error('[WS] Error:', err);
            state.ws?.close();
        };
    }

    function scheduleReconnect() {
        if (state.reconnectAttempts >= CONFIG.maxReconnectAttempts) {
            updateConnectionStatus('offline');
            return;
        }
        state.reconnectAttempts++;
        updateConnectionStatus('standby');
        setTimeout(connectWS, CONFIG.reconnectInterval);
    }

    function updateConnectionStatus(status) {
        if (!els.wsDot || !els.wsStatus) return;
        els.wsDot.className = 'status-dot ' + status;
        const labels = { online: 'Connected', offline: 'Disconnected', standby: 'Reconnecting...' };
        els.wsStatus.textContent = 'WebSocket: ' + labels[status];
    }

    // ============================================================
    // MESSAGE HANDLERS
    // ============================================================
    function handleMessage(msg) {
        switch (msg.type) {
            case 'target':
                handleTarget(msg.data);
                break;
            case 'ai_decision':
                handleAIDecision(msg.data);
                break;
            case 'timeline':
                handleTimeline(msg.data);
                break;
            case 'tool_output':
                handleToolOutput(msg.data);
                break;
            case 'system_status':
                handleSystemStatus(msg.data);
                break;
            case 'daemon_status':
                handleDaemonStatus(msg.data);
                break;
            case 'attack_count':
                handleAttackCount(msg.data);
                break;
            default:
                console.log('[WS] Unknown type:', msg.type, msg);
        }
    }

    // ============================================================
    // TARGET TREE
    // ============================================================
    function handleTarget(data) {
        if (!data?.bssid) return;
        state.targets.set(data.bssid, {
            ...data,
            timestamp: Date.now(),
        });
        renderTargets();
    }

    function renderTargets() {
        if (!els.targetTree) return;
        const sorted = Array.from(state.targets.values())
            .sort((a, b) => (b.score || 0) - (a.score || 0));

        els.targetTree.innerHTML = sorted.map(t => {
            const scoreClass = t.score >= 70 ? 'score-high' : t.score >= 40 ? 'score-medium' : 'score-low';
            const scoreLabel = t.score >= 70 ? 'HIGH' : t.score >= 40 ? 'MED' : 'LOW';
            return `
                <div class="target-item" data-bssid="${t.bssid}">
                    <div class="ssid">
                        <span>${escapeHtml(t.ssid || '<Hidden>')}</span>
                        <span class="score ${scoreClass}">${scoreLabel} ${t.score || 0}</span>
                    </div>
                    <div class="meta">
                        <span>${t.bssid}</span>
                        <span>Ch ${t.channel || '?'}</span>
                        <span>${t.band || '2.4GHz'}</span>
                        <span>${t.security || 'Unknown'}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ============================================================
    // AI LOG
    // ============================================================
    function handleAIDecision(data) {
        const entry = {
            provider: data.provider || 'AI',
            message: data.message || data.decision || '',
            timestamp: new Date().toLocaleTimeString(),
        };
        state.aiLogs.unshift(entry);
        if (state.aiLogs.length > CONFIG.maxLogEntries) state.aiLogs.pop();
        renderAILog();
    }

    function renderAILog() {
        if (!els.aiLog) return;
        els.aiLog.innerHTML = state.aiLogs.map(log => `
            <div class="ai-entry">
                <div class="provider">${escapeHtml(log.provider)}</div>
                <div class="msg">${escapeHtml(log.message)}</div>
                <div class="timestamp">${log.timestamp}</div>
            </div>
        `).join('');
        if (els.aiLog.scrollTop === 0) els.aiLog.scrollTop = 0;
    }

    // ============================================================
    // TERMINAL OUTPUT
    // ============================================================
    function handleToolOutput(data) {
        if (!data?.line) return;
        const line = {
            tool: data.tool || 'system',
            stream: data.stream || 'stdout',
            text: data.line,
            time: new Date().toLocaleTimeString(),
        };
        state.terminalLines.push(line);
        if (state.terminalLines.length > CONFIG.maxTerminalLines) {
            state.terminalLines.shift();
        }
        renderTerminal();
    }

    function renderTerminal() {
        if (!els.terminalOutput) return;
        els.terminalOutput.innerHTML = state.terminalLines.map(l => `
            <div class="terminal-line ${escapeHtml(l.stream)}">
                <span class="tool-name">[${escapeHtml(l.tool)}]</span>
                <span>${escapeHtml(l.text)}</span>
            </div>
        `).join('');
        els.terminalOutput.scrollTop = els.terminalOutput.scrollHeight;
    }

    // ============================================================
    // TIMELINE
    // ============================================================
    function handleTimeline(data) {
        if (!data?.phase) return;
        state.timeline.unshift({
            phase: data.phase,
            status: data.status,
            result: data.result || '',
            time: new Date().toLocaleTimeString(),
        });
        if (state.timeline.length > CONFIG.maxLogEntries) state.timeline.pop();
        renderTimeline();
    }

    function renderTimeline() {
        if (!els.timeline) return;
        els.timeline.innerHTML = state.timeline.map(t => {
            const dotClass = t.status === 'success' ? 'success' :
                             t.status === 'failed' ? 'failed' :
                             t.status === 'started' ? 'started' : 'running';
            return `
                <div class="timeline-item">
                    <div class="timeline-dot ${dotClass}"></div>
                    <div class="timeline-content">
                        <div class="timeline-phase">${escapeHtml(t.phase)}</div>
                        <div class="timeline-result">${escapeHtml(t.result)} <span style="color:var(--bhisma-text-dim)">${t.time}</span></div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ============================================================
    // SYSTEM STATUS
    // ============================================================
    function handleSystemStatus(data) {
        if (data.iface && els.sysIface) els.sysIface.textContent = data.iface;
        if (data.monitor !== undefined && els.sysMonitor) {
            els.sysMonitor.textContent = data.monitor ? 'ON' : 'OFF';
            els.sysMonitor.className = 'value ' + (data.monitor ? 'ok' : '');
        }
        if (data.cpu !== undefined && els.sysCpu) {
            els.sysCpu.textContent = data.cpu + '%';
            els.sysCpu.className = 'value ' + (data.cpu > 80 ? 'alert' : data.cpu > 50 ? 'warn' : 'ok');
        }
        if (data.mem && els.sysMem) els.sysMem.textContent = data.mem;
        if (data.providers && els.keyBadges) renderKeyBadges(data.providers);
    }

    function renderKeyBadges(providers) {
        if (!els.keyBadges) return;
        els.keyBadges.innerHTML = Object.entries(providers).map(([name, status]) => {
            const cls = status === 'ok' ? 'key-ok' : status === 'quota' ? 'key-quota' : 'key-missing';
            const txt = status === 'ok' ? 'OK' : status === 'quota' ? 'QUOTA' : 'MISS';
            return `<span class="key-badge ${cls}">${escapeHtml(name)}: ${txt}</span>`;
        }).join('');
    }

    // ============================================================
    // DAEMON & ATTACKS
    // ============================================================
    function handleDaemonStatus(data) {
        if (!els.daemonDot || !els.daemonStatus) return;
        const status = data.active ? 'online' : 'offline';
        els.daemonDot.className = 'status-dot ' + status;
        els.daemonStatus.textContent = 'Daemon: ' + (data.active ? 'Active' : 'Standby');
    }

    function handleAttackCount(data) {
        state.attackCount = data.count || 0;
        if (els.activeAttacks) els.activeAttacks.textContent = 'Attacks: ' + state.attackCount;
    }

    // ============================================================
    // UTILITIES
    // ============================================================
    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function pollStatus() {
        if (state.ws?.readyState === WebSocket.OPEN) {
            state.ws.send(JSON.stringify({ type: 'status_request' }));
        }
    }

    // ============================================================
    // CHARTS (Chart.js integration)
    // ============================================================
    function initCharts() {
        // Placeholder for chart initialization
        // Will be expanded when chart containers are added to HTML
    }

    // ============================================================
    // MAP (Leaflet integration)
    // ============================================================
    function initMap() {
        const mapEl = document.getElementById('map');
        if (!mapEl || typeof L === 'undefined') return;

        const map = L.map('map', {
            center: [20, 0],
            zoom: 2,
            zoomControl: false,
            attributionControl: false,
        });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy;OpenStreetMap, &copy;CartoDB',
            subdomains: 'abcd',
            maxZoom: 19,
        }).addTo(map);

        state.map = map;
    }

    // ============================================================
    // INITIALIZATION
    // ============================================================
    function init() {
        connectWS();
        initMap();
        initCharts();

        // Poll system status
        setInterval(pollStatus, CONFIG.pollInterval);

        // ASCII logo animation is inline in HTML
        console.log('%c BHISMA v3.0.0 ', 'background:#e94560;color:#fff;padding:4px 8px;border-radius:4px;font-weight:bold;');
        console.log('%c AI-Powered Autonomous WiFi Framework ', 'color:#e94560;');
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

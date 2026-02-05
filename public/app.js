// Global state
let currentUid = '';
let isReading = false;
let isReadingLite = false;
let apduLogEntries = [];

// DOM Elements
const statusIndicator = document.getElementById('statusIndicator');
const nfcList = document.getElementById('nfcList');
const uidDisplay = document.getElementById('uidDisplay');
const uidActions = document.getElementById('uidActions');
const readBtn = document.getElementById('readBtn');
const historyList = document.getElementById('historyList');
const toast = document.getElementById('toast');
const liteVersion = document.getElementById('liteVersion');
const liteInfo = document.getElementById('liteInfo');
const readLiteBtn = document.getElementById('readLiteBtn');
const apduInput = document.getElementById('apduInput');
const apduOutput = document.getElementById('apduOutput');
const stopServerBtn = document.getElementById('stopServerBtn');
const apduLogList = document.getElementById('apduLogList');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    refreshReaders();
    loadHistory();
});

// Set status
function setStatus(status, message) {
    statusIndicator.className = 'status-indicator ' + status;
    statusIndicator.querySelector('.status-text').textContent = message;
}

// Show toast notification
function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = 'toast ' + type + ' show';
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

// APDU Log functions
function addApduLogEntries(logs, operation) {
    if (!logs || logs.length === 0) return;

    const timestamp = new Date().toLocaleTimeString();
    logs.forEach((log, index) => {
        apduLogEntries.unshift({
            timestamp,
            operation,
            index: index + 1,
            total: logs.length,
            tx: log.tx,
            rx: log.rx,
            sw: log.sw
        });
    });

    // Keep only last 100 entries
    if (apduLogEntries.length > 100) {
        apduLogEntries = apduLogEntries.slice(0, 100);
    }

    renderApduLog();
}

function renderApduLog() {
    if (apduLogEntries.length === 0) {
        apduLogList.innerHTML = '<div class="log-empty">No APDU transactions yet</div>';
        return;
    }

    apduLogList.innerHTML = apduLogEntries.map(entry => {
        const swClass = entry.sw === '9000' ? 'sw-ok' : 'sw-err';
        const itemClass = entry.sw === '9000' ? 'success' : 'error';
        return `
            <div class="log-item ${itemClass}">
                <div class="log-timestamp">${entry.timestamp} - ${entry.operation} (${entry.index}/${entry.total})</div>
                <div class="log-tx"><span class="log-label">TX:</span><span class="log-value">${entry.tx}</span></div>
                <div class="log-rx"><span class="log-label">RX:</span><span class="log-value">${entry.rx || '(empty)'}</span></div>
                <div class="log-sw ${swClass}"><span class="log-label">SW:</span><span class="log-value">${entry.sw}</span></div>
            </div>
        `;
    }).join('');
}

function clearApduLog() {
    apduLogEntries = [];
    renderApduLog();
    showToast('APDU log cleared', 'success');
}

function disableControls() {
    document.querySelectorAll('button').forEach((btn) => {
        if (btn.id !== 'stopServerBtn') {
            btn.disabled = true;
        }
    });
}

// Refresh readers
async function refreshReaders() {
    nfcList.innerHTML = '<div class="nfc-list-loading">Scanning...</div>';
    try {
        const response = await fetch('/api/readers');
        const data = await response.json();

        if (data.success && data.readers.length > 0) {
            const targetIndex = data.readers.length > 1 ? 1 : 0;
            nfcList.innerHTML = data.readers.map((reader, index) => {
                const isActive = index === targetIndex;
                return `
                    <div class="nfc-reader-item ${isActive ? 'active' : ''}">
                        <div class="reader-status-dot ${isActive ? 'active' : ''}"></div>
                        <div class="reader-details">
                            <div class="reader-name">${reader}</div>
                            <div class="reader-index">${isActive ? 'Active' : `Index ${index}`}</div>
                        </div>
                    </div>
                `;
            }).join('');
            setStatus('', 'Ready');
        } else if (data.readers && data.readers.length === 0) {
            nfcList.innerHTML = '<div class="nfc-list-empty">No readers found</div>';
            setStatus('error', 'No Reader');
        } else {
            nfcList.innerHTML = `<div class="nfc-list-error">${data.error || 'Error'}</div>`;
            setStatus('error', 'Error');
        }
    } catch (error) {
        nfcList.innerHTML = '<div class="nfc-list-error">Connection error</div>';
        setStatus('error', 'Offline');
    }
}

// Read NFC UID
async function readUid() {
    if (isReading) return;

    isReading = true;
    readBtn.disabled = true;
    readBtn.classList.add('loading');
    setStatus('reading', 'Reading...');

    uidDisplay.innerHTML = '<div class="uid-placeholder">Reading card...</div>';
    uidActions.style.display = 'none';

    try {
        const response = await fetch('/api/uid');
        const data = await response.json();

        // Log APDU transactions
        if (data.apdu_log) {
            addApduLogEntries(data.apdu_log, 'Read UID');
        }

        if (data.success) {
            currentUid = data.uid;
            uidDisplay.innerHTML = `<div class="uid-value">${data.uid}</div>`;
            uidActions.style.display = 'block';
            setStatus('', 'Success');
            showToast('UID read successfully!', 'success');
            loadHistory();
        } else {
            uidDisplay.innerHTML = `<div class="uid-error">❌ ${data.error}</div>`;
            uidActions.style.display = 'none';
            setStatus('error', 'Failed');
            showToast(data.error, 'error');
        }
    } catch (error) {
        uidDisplay.innerHTML = '<div class="uid-error">❌ Connection error</div>';
        uidActions.style.display = 'none';
        setStatus('error', 'Error');
        showToast('Failed to connect to server', 'error');
    } finally {
        isReading = false;
        readBtn.disabled = false;
        readBtn.classList.remove('loading');
    }
}

// Copy UID to clipboard
async function copyUid() {
    if (!currentUid) return;

    try {
        // Copy without spaces
        const uidNoSpace = currentUid.replace(/\s/g, '');
        await navigator.clipboard.writeText(uidNoSpace);
        showToast('UID copied to clipboard!', 'success');
    } catch (error) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = currentUid.replace(/\s/g, '');
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showToast('UID copied to clipboard!', 'success');
    }
}

// Copy specific UID from history
async function copyHistoryUid(uid) {
    try {
        const uidNoSpace = uid.replace(/\s/g, '');
        await navigator.clipboard.writeText(uidNoSpace);
        showToast('UID copied!', 'success');
    } catch (error) {
        showToast('Failed to copy', 'error');
    }
}

// Load history
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const history = await response.json();

        if (history.length === 0) {
            historyList.innerHTML = '<div class="history-empty">No records yet</div>';
            return;
        }

        historyList.innerHTML = history.map(item => {
            const time = new Date(item.timestamp);
            const timeStr = time.toLocaleTimeString();
            const dateStr = time.toLocaleDateString();
            return `
                <div class="history-item">
                    <div>
                        <div class="history-uid" onclick="copyHistoryUid('${item.uid}')" title="Click to copy">
                            ${item.uid}
                        </div>
                        <div class="history-time">${dateStr} ${timeStr}</div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        historyList.innerHTML = '<div class="history-empty">Failed to load history</div>';
    }
}

// Clear history
async function clearHistory() {
    if (!confirm('Clear all history?')) return;

    try {
        await fetch('/api/history', { method: 'DELETE' });
        loadHistory();
        showToast('History cleared', 'success');
    } catch (error) {
        showToast('Failed to clear history', 'error');
    }
}

// Stop server
async function stopServer() {
    if (!confirm('Stop the NFC Reader server?')) return;

    stopServerBtn.disabled = true;
    setStatus('reading', 'Stopping...');

    try {
        const response = await fetch('/api/stop', { method: 'POST' });
        const data = await response.json();
        showToast(data.message || 'Server stopping...', 'success');
    } catch (error) {
        showToast('Server stopped or unreachable', 'success');
    } finally {
        setStatus('error', 'Stopped');
        disableControls();
    }
}

// Read OneKey Lite info
async function readLiteInfo() {
    if (isReadingLite) return;

    isReadingLite = true;
    readLiteBtn.disabled = true;
    readLiteBtn.classList.add('loading');
    setStatus('reading', 'Reading Lite...');

    liteInfo.innerHTML = '<div class="lite-placeholder">Reading card info...</div>';

    try {
        const version = liteVersion.value;
        const response = await fetch(`/api/lite/info?version=${version}`);
        const data = await response.json();

        // Log APDU transactions
        if (data.apdu_log) {
            addApduLogEntries(data.apdu_log, 'Lite Info');
        }

        if (data.success) {
            const pinStatusClass = data.pin_status === 'set' ? 'status-set' : 'status-not-set';
            const backupStatusClass = data.backup_status === 'has_backup' ? 'status-set' : 'status-not-set';

            liteInfo.innerHTML = `
                <div class="lite-info-grid">
                    <div class="info-item">
                        <span class="info-label">Serial Number</span>
                        <span class="info-value">${data.serial_number || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">PIN Status</span>
                        <span class="info-value ${pinStatusClass}">${formatStatus(data.pin_status)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Backup Status</span>
                        <span class="info-value ${backupStatusClass}">${formatStatus(data.backup_status)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">PIN Retry Count</span>
                        <span class="info-value">${data.pin_retry_count !== null ? data.pin_retry_count : 'N/A'}</span>
                    </div>
                </div>
                ${data.errors && data.errors.length > 0 ? `<div class="lite-errors">Warnings: ${data.errors.join(', ')}</div>` : ''}
            `;
            setStatus('', 'Success');
            showToast('Lite info read successfully!', 'success');
        } else {
            liteInfo.innerHTML = `<div class="lite-error">❌ ${data.error}</div>`;
            setStatus('error', 'Failed');
            showToast(data.error, 'error');
        }
    } catch (error) {
        liteInfo.innerHTML = '<div class="lite-error">❌ Connection error</div>';
        setStatus('error', 'Error');
        showToast('Failed to connect to server', 'error');
    } finally {
        isReadingLite = false;
        readLiteBtn.disabled = false;
        readLiteBtn.classList.remove('loading');
    }
}

// Format status for display
function formatStatus(status) {
    const statusMap = {
        'set': 'Set',
        'not_set': 'Not Set',
        'has_backup': 'Has Backup',
        'no_backup': 'No Backup',
        'unknown': 'Unknown'
    };
    return statusMap[status] || status || 'N/A';
}

// Send raw APDU command
async function sendApdu() {
    const apdu = apduInput.value.replace(/\s/g, '');
    if (!apdu) {
        showToast('Please enter APDU hex string', 'error');
        return;
    }

    apduOutput.innerHTML = '<div class="debug-placeholder">Sending...</div>';

    try {
        const response = await fetch('/api/lite/apdu', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ apdu })
        });
        const data = await response.json();

        // Log APDU transactions
        if (data.apdu_log) {
            addApduLogEntries(data.apdu_log, 'Raw APDU');
        }

        if (data.success) {
            apduOutput.innerHTML = `
                <div class="apdu-result">
                    <div class="apdu-row"><span class="apdu-label">APDU:</span> <span class="apdu-value">${data.apdu}</span></div>
                    <div class="apdu-row"><span class="apdu-label">Response:</span> <span class="apdu-value">${data.response || '(empty)'}</span></div>
                    <div class="apdu-row"><span class="apdu-label">SW:</span> <span class="apdu-value sw-${data.sw === '9000' ? 'ok' : 'err'}">${data.sw}</span></div>
                </div>
            `;
        } else {
            apduOutput.innerHTML = `<div class="debug-error">❌ ${data.error}</div>`;
        }
    } catch (error) {
        apduOutput.innerHTML = '<div class="debug-error">❌ Connection error</div>';
    }
}

// Type 4 Card Functions
let isReadingType4 = false;
const type4Aid = document.getElementById('type4Aid');
const type4Info = document.getElementById('type4Info');
const type4Operations = document.getElementById('type4Operations');

async function readType4Info() {
    if (isReadingType4) return;

    isReadingType4 = true;
    const btn = document.getElementById('readType4Btn');
    btn.disabled = true;
    btn.classList.add('loading');
    setStatus('reading', 'Connecting...');

    type4Info.innerHTML = '<div class="type4-placeholder">Connecting to card...</div>';
    type4Operations.style.display = 'none';

    try {
        const aid = type4Aid.value.replace(/\s/g, '');
        const response = await fetch(`/api/type4/info?aid=${aid}`);
        const data = await response.json();

        // Log APDU transactions
        if (data.apdu_log) {
            addApduLogEntries(data.apdu_log, 'Type4 Connect');
        }

        if (data.success) {
            const selectedClass = data.selected ? 'status-set' : 'status-not-set';
            const usedAid = data.aid || 'N/A';
            const requestedAid = data.aid_requested || '';
            const aidHtml = requestedAid && requestedAid !== usedAid
                ? `
                    <div class="info-item">
                        <span class="info-label">AID (Used)</span>
                        <span class="info-value">${usedAid}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">AID (Requested)</span>
                        <span class="info-value">${requestedAid}</span>
                    </div>
                `
                : `
                    <div class="info-item">
                        <span class="info-label">AID</span>
                        <span class="info-value">${usedAid}</span>
                    </div>
                `;
            type4Info.innerHTML = `
                <div class="type4-info-grid">
                    <div class="info-item">
                        <span class="info-label">UID</span>
                        <span class="info-value">${data.uid || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">ATR</span>
                        <span class="info-value atr-value">${data.atr || 'N/A'}</span>
                    </div>
                    ${aidHtml}
                    <div class="info-item">
                        <span class="info-label">Select Status</span>
                        <span class="info-value ${selectedClass}">${data.selected ? 'OK' : 'Failed'} (${data.select_sw})</span>
                    </div>
                </div>
            `;

            if (data.selected) {
                type4Operations.style.display = 'block';
                showToast('Card connected!', 'success');
            } else {
                showToast(`Select failed: ${data.select_sw}`, 'error');
            }
            setStatus('', 'Connected');
        } else {
            type4Info.innerHTML = `<div class="type4-error">${data.error}</div>`;
            type4Operations.style.display = 'none';
            setStatus('error', 'Failed');
            showToast(data.error, 'error');
        }
    } catch (error) {
        type4Info.innerHTML = '<div class="type4-error">Connection error</div>';
        type4Operations.style.display = 'none';
        setStatus('error', 'Error');
        showToast('Failed to connect to server', 'error');
    } finally {
        isReadingType4 = false;
        btn.disabled = false;
        btn.classList.remove('loading');
    }
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.style.display = 'none');

    if (tab === 'read') {
        document.querySelector('.tab-btn:first-child').classList.add('active');
        document.getElementById('tabRead').style.display = 'block';
    } else {
        document.querySelector('.tab-btn:last-child').classList.add('active');
        document.getElementById('tabWrite').style.display = 'block';
    }
}

async function type4Read() {
    const aid = type4Aid.value.replace(/\s/g, '');
    const offset = parseInt(document.getElementById('readOffset').value) || 0;
    const length = parseInt(document.getElementById('readLength').value) || 16;
    const resultDiv = document.getElementById('readResult');

    resultDiv.innerHTML = '<div class="result-placeholder">Reading...</div>';

    try {
        const response = await fetch('/api/type4/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ aid, offset, length })
        });
        const data = await response.json();

        // Log APDU transactions
        if (data.apdu_log) {
            addApduLogEntries(data.apdu_log, 'Type4 Read');
        }

        if (data.success && data.operation_ok) {
            resultDiv.innerHTML = `
                <div class="result-success">
                    <div class="result-row"><span class="result-label">SW:</span> <span class="sw-ok">${data.operation_sw}</span></div>
                    <div class="result-row"><span class="result-label">Data:</span></div>
                    <div class="result-data">${data.data || '(empty)'}</div>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `<div class="result-error">Read failed: ${data.error || data.operation_sw}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = '<div class="result-error">Connection error</div>';
    }
}

async function type4Write() {
    const aid = type4Aid.value.replace(/\s/g, '');
    const offset = parseInt(document.getElementById('writeOffset').value) || 0;
    const dataHex = document.getElementById('writeData').value.replace(/\s/g, '');
    const resultDiv = document.getElementById('writeResult');

    if (!dataHex) {
        showToast('Please enter data to write', 'error');
        return;
    }

    resultDiv.innerHTML = '<div class="result-placeholder">Writing...</div>';

    try {
        const response = await fetch('/api/type4/write', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ aid, offset, data: dataHex })
        });
        const data = await response.json();

        // Log APDU transactions
        if (data.apdu_log) {
            addApduLogEntries(data.apdu_log, 'Type4 Write');
        }

        if (data.success && data.operation_ok) {
            resultDiv.innerHTML = `
                <div class="result-success">
                    <div class="result-row"><span class="result-label">SW:</span> <span class="sw-ok">${data.operation_sw}</span></div>
                    <div class="result-row">Write successful!</div>
                </div>
            `;
            showToast('Write successful!', 'success');
        } else {
            resultDiv.innerHTML = `<div class="result-error">Write failed: ${data.error || data.operation_sw}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = '<div class="result-error">Connection error</div>';
    }
}

// Keyboard shortcut: Space to read
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !isReading && !isReadingLite && !isReadingType4 && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        readUid();
    }
});

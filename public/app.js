// Global state
let currentUid = '';
let isReading = false;
let isReadingLite = false;

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

// Keyboard shortcut: Space to read
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !isReading && !isReadingLite && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        readUid();
    }
});

// Global state
let currentUid = '';
let isReading = false;

// DOM Elements
const statusIndicator = document.getElementById('statusIndicator');
const readerName = document.getElementById('readerName');
const uidDisplay = document.getElementById('uidDisplay');
const uidActions = document.getElementById('uidActions');
const readBtn = document.getElementById('readBtn');
const historyList = document.getElementById('historyList');
const toast = document.getElementById('toast');

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
    readerName.textContent = 'Checking...';
    try {
        const response = await fetch('/api/readers');
        const data = await response.json();

        if (data.success && data.readers.length > 0) {
            // Show the target reader (index 1 or 0 if only one)
            const targetIndex = data.readers.length > 1 ? 1 : 0;
            readerName.textContent = data.readers[targetIndex];
            setStatus('', 'Ready');
        } else if (data.readers && data.readers.length === 0) {
            readerName.textContent = 'No readers found';
            setStatus('error', 'No Reader');
        } else {
            readerName.textContent = data.error || 'Error';
            setStatus('error', 'Error');
        }
    } catch (error) {
        readerName.textContent = 'Connection error';
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

// Keyboard shortcut: Space to read
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !isReading && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        readUid();
    }
});

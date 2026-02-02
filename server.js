const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Store history in memory
let uidHistory = [];

// Python virtual environment path
const VENV_PYTHON = path.join(__dirname, 'venv_nfc', 'bin', 'python');
const READ_UID_SCRIPT = path.join(__dirname, 'scripts', 'read_uid.py');

// API: Get NFC UID
app.get('/api/uid', async (req, res) => {
    try {
        const result = await readNfcUid();
        if (result.success) {
            // Add to history
            const record = {
                uid: result.uid,
                timestamp: new Date().toISOString(),
                reader: result.reader
            };
            uidHistory.unshift(record);
            // Keep only last 50 records
            if (uidHistory.length > 50) {
                uidHistory = uidHistory.slice(0, 50);
            }
        }
        res.json(result);
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// API: Get history
app.get('/api/history', (req, res) => {
    res.json(uidHistory);
});

// API: Clear history
app.delete('/api/history', (req, res) => {
    uidHistory = [];
    res.json({ success: true, message: 'History cleared' });
});

// API: Get available readers
app.get('/api/readers', async (req, res) => {
    try {
        const result = await getReaders();
        res.json(result);
    } catch (error) {
        res.json({ success: false, error: error.message, readers: [] });
    }
});

// Function to read NFC UID
function readNfcUid() {
    return new Promise((resolve, reject) => {
        const process = spawn(VENV_PYTHON, [READ_UID_SCRIPT, 'read']);
        let stdout = '';
        let stderr = '';

        process.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        process.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        process.on('close', (code) => {
            try {
                const result = JSON.parse(stdout);
                resolve(result);
            } catch (e) {
                resolve({
                    success: false,
                    error: stderr || stdout || 'Failed to parse response'
                });
            }
        });

        process.on('error', (err) => {
            resolve({ success: false, error: `Failed to execute script: ${err.message}` });
        });
    });
}

// Function to get available readers
function getReaders() {
    return new Promise((resolve, reject) => {
        const process = spawn(VENV_PYTHON, [READ_UID_SCRIPT, 'list']);
        let stdout = '';
        let stderr = '';

        process.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        process.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        process.on('close', (code) => {
            try {
                const result = JSON.parse(stdout);
                resolve(result);
            } catch (e) {
                resolve({
                    success: false,
                    error: stderr || stdout || 'Failed to parse response',
                    readers: []
                });
            }
        });

        process.on('error', (err) => {
            resolve({ success: false, error: `Failed to execute script: ${err.message}`, readers: [] });
        });
    });
}

app.listen(PORT, () => {
    console.log(`\n🚀 NFC Reader Server running at http://localhost:${PORT}`);
    console.log(`📖 Open this URL in your browser to use the NFC Reader\n`);
});

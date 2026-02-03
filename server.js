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

// API: Get OneKey Lite card info
app.get('/api/lite/info', async (req, res) => {
    try {
        const version = req.query.version || 'v2';
        const result = await getLiteInfo(version);
        res.json(result);
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// API: Send raw APDU command
app.post('/api/lite/apdu', async (req, res) => {
    try {
        const { apdu } = req.body;
        if (!apdu) {
            return res.json({ success: false, error: 'APDU hex string required' });
        }
        const result = await sendRawApdu(apdu);
        res.json(result);
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// API: Get Type 4 card info
app.get('/api/type4/info', async (req, res) => {
    try {
        const aid = req.query.aid || 'F00102030405';
        const result = await getType4Info(aid);
        res.json(result);
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// API: Type 4 read operation
app.post('/api/type4/read', async (req, res) => {
    try {
        const { aid, offset, length } = req.body;
        const result = await type4Read(aid || 'F00102030405', offset || 0, length || 16);
        res.json(result);
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// API: Type 4 write operation
app.post('/api/type4/write', async (req, res) => {
    try {
        const { aid, offset, data } = req.body;
        if (!data) {
            return res.json({ success: false, error: 'Data hex string required' });
        }
        const result = await type4Write(aid || 'F00102030405', offset || 0, data);
        res.json(result);
    } catch (error) {
        res.json({ success: false, error: error.message });
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

// Function to get OneKey Lite info
function getLiteInfo(version) {
    return new Promise((resolve, reject) => {
        const process = spawn(VENV_PYTHON, [READ_UID_SCRIPT, 'lite', '1', version]);
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

// Function to send raw APDU
function sendRawApdu(apduHex) {
    return new Promise((resolve, reject) => {
        const process = spawn(VENV_PYTHON, [READ_UID_SCRIPT, 'apdu', '1', apduHex]);
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

// Function to get Type 4 card info
function getType4Info(aid) {
    return new Promise((resolve, reject) => {
        const process = spawn(VENV_PYTHON, [READ_UID_SCRIPT, 'type4', '1', aid]);
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

// Function to read from Type 4 card
function type4Read(aid, offset, length) {
    return new Promise((resolve, reject) => {
        const process = spawn(VENV_PYTHON, [READ_UID_SCRIPT, 'type4_read', '1', aid, String(offset), String(length)]);
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

// Function to write to Type 4 card
function type4Write(aid, offset, dataHex) {
    return new Promise((resolve, reject) => {
        const process = spawn(VENV_PYTHON, [READ_UID_SCRIPT, 'type4_write', '1', aid, String(offset), dataHex]);
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

app.listen(PORT, () => {
    console.log(`\n🚀 NFC Reader Server running at http://localhost:${PORT}`);
    console.log(`📖 Open this URL in your browser to use the NFC Reader\n`);
});

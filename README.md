# NFC UID Reader Web Interface

A web-based interface for reading NFC card UIDs.

## Features

- 🔖 One-click NFC UID reading
- 📋 Copy UID to clipboard
- 📜 Reading history with timestamps
- ⌨️ Keyboard shortcut (Space to read)
- 🎨 Modern dark theme UI

## Requirements

- Node.js v14+
- Python 3
- pyscard library
- NFC reader hardware (PC/SC compatible)

## Quick Start

```bash
cd nfc-reader
./start.sh
```

Then open http://localhost:3001 in your browser.

## Manual Setup

1. Install Python dependencies:
```bash
python3 -m venv venv_nfc
./venv_nfc/bin/pip install pyscard
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the server:
```bash
npm start
```

## Usage

1. Connect your NFC reader
2. Open http://localhost:3001
3. Place NFC card on reader
4. Click "Read UID" button (or press Space)
5. UID will be displayed and can be copied

## API Endpoints

- `GET /api/uid` - Read NFC card UID
- `GET /api/readers` - List available readers
- `GET /api/history` - Get reading history
- `DELETE /api/history` - Clear history

## Scripts

- `./start.sh` - Start server (background)
- `./stop.sh` - Stop server

## Project Structure

```
nfc-reader/
├── server.js          # Express backend
├── package.json       # Node.js dependencies
├── start.sh          # Start script
├── stop.sh           # Stop script
├── scripts/
│   └── read_uid.py   # Python NFC reader
└── public/
    ├── index.html    # Web interface
    ├── style.css     # Styles
    └── app.js        # Frontend logic
```

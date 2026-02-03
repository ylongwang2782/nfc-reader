# NFC Card Reader

A web-based interface and CLI tool for reading NFC cards, supporting generic Type 4 cards and OneKey Lite cards.

## Features

- Read NFC card UID
- OneKey Lite card info (V1/V2)
- Type 4 card operations (Select/Read/Write)
- Web UI with dark theme
- CLI with human-readable and JSON output
- Raw APDU command support

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

## CLI Usage

The CLI tool is located at `scripts/read_uid.py`.

### List Readers

```bash
./venv_nfc/bin/python scripts/read_uid.py list
```

### Read Card UID

```bash
./venv_nfc/bin/python scripts/read_uid.py uid
./venv_nfc/bin/python scripts/read_uid.py uid -r 0    # Use reader index 0
```

### OneKey Lite Card

```bash
./venv_nfc/bin/python scripts/read_uid.py lite           # V2 card (default)
./venv_nfc/bin/python scripts/read_uid.py lite -v v1     # V1 card
```

### Type 4 Card Operations

```bash
# Connect to card with AID
./venv_nfc/bin/python scripts/read_uid.py type4 -a F00102030405

# Read data (offset=0, length=16)
./venv_nfc/bin/python scripts/read_uid.py type4 -a F00102030405 read -o 0 -l 16

# Write data at offset 0
./venv_nfc/bin/python scripts/read_uid.py type4 -a F00102030405 write -o 0 -d 48454C4C4F
```

### Send Raw APDU

```bash
./venv_nfc/bin/python scripts/read_uid.py apdu 00A4040000
```

### Output Formats

```bash
# JSON output (default when piped)
./venv_nfc/bin/python scripts/read_uid.py --json list

# Human-readable output
./venv_nfc/bin/python scripts/read_uid.py --pretty list
```

### Help

```bash
./venv_nfc/bin/python scripts/read_uid.py --help
./venv_nfc/bin/python scripts/read_uid.py type4 --help
```

## API Endpoints

### Basic

- `GET /api/uid` - Read NFC card UID
- `GET /api/readers` - List available readers
- `GET /api/history` - Get reading history
- `DELETE /api/history` - Clear history

### OneKey Lite

- `GET /api/lite/info?version=v1|v2` - Get Lite card info
- `POST /api/lite/apdu` - Send raw APDU

### Type 4 Card

- `GET /api/type4/info?aid=HEX` - Connect and get card info
- `POST /api/type4/read` - Read data `{aid, offset, length}`
- `POST /api/type4/write` - Write data `{aid, offset, data}`

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

## Scripts

- `./start.sh` - Start server (background)
- `./stop.sh` - Stop server

## Project Structure

```
nfc-reader/
├── server.js          # Express backend
├── package.json       # Node.js dependencies
├── start.sh           # Start script
├── stop.sh            # Stop script
├── scripts/
│   └── read_uid.py    # Python NFC reader CLI
└── public/
    ├── index.html     # Web interface
    ├── style.css      # Styles
    └── app.js         # Frontend logic
```

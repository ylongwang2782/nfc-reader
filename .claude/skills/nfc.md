# NFC Card Reader Skill

Read NFC cards using pyscard library. Supports generic Type 4 cards and OneKey Lite cards.

## Usage

All commands are executed from the `nfc-reader` directory using the Python virtual environment.

### List Available Readers

```bash
./venv_nfc/bin/python scripts/read_uid.py --json list
```

Returns: `{"success": true, "readers": ["Reader1", "Reader2"], "count": 2}`

### Read Card UID

```bash
./venv_nfc/bin/python scripts/read_uid.py --json uid
```

Returns: `{"success": true, "uid": "XX XX XX XX", "uid_hex": "XXXXXXXX", "reader": "...", "sw": "90 00"}`

### OneKey Lite Card Info

```bash
# V2 card (default)
./venv_nfc/bin/python scripts/read_uid.py --json lite

# V1 card
./venv_nfc/bin/python scripts/read_uid.py --json lite -v v1
```

Returns: `{"success": true, "serial_number": "...", "pin_status": "set|not_set", "backup_status": "has_backup|no_backup", "pin_retry_count": N}`

### Type 4 Card Operations

```bash
# Connect to card with AID
./venv_nfc/bin/python scripts/read_uid.py --json type4 -a <AID_HEX>

# Read data
./venv_nfc/bin/python scripts/read_uid.py --json type4 -a <AID_HEX> read -o <OFFSET> -l <LENGTH>

# Write data
./venv_nfc/bin/python scripts/read_uid.py --json type4 -a <AID_HEX> write -o <OFFSET> -d <DATA_HEX>
```

### Send Raw APDU

```bash
./venv_nfc/bin/python scripts/read_uid.py --json apdu <APDU_HEX>
```

Returns: `{"success": true, "apdu": "...", "response": "...", "sw": "9000"}`

## Common Status Words (SW)

- `9000` - Success
- `6385` - Conditions not satisfied (e.g., wrong AID)
- `6700` - Wrong length
- `6982` - Security not satisfied
- `6983` - Authentication blocked
- `6985` - Conditions of use not satisfied
- `63CX` - PIN wrong, X retries remaining

## Notes

- Always use `--json` flag for machine-readable output
- Default reader index is 1 (use `-r 0` for index 0)
- Card must be placed on reader before executing commands
- If "No card present" error, ensure card is properly positioned

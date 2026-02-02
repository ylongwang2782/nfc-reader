#!/usr/bin/env python3
"""
NFC UID Reader Script
Reads NFC card UID using pyscard library
"""

import sys
import json

try:
    from smartcard.System import readers
    from smartcard.util import toHexString
    from smartcard.Exceptions import NoCardException, CardConnectionException
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "pyscard not installed. Run: pip install pyscard"
    }))
    sys.exit(1)


def get_readers():
    """Get list of available readers"""
    try:
        r_list = readers()
        reader_names = [str(r) for r in r_list]
        return {
            "success": True,
            "readers": reader_names,
            "count": len(reader_names)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "readers": []
        }


def read_uid(reader_index=1):
    """Read UID from NFC card"""
    try:
        r_list = readers()

        if len(r_list) == 0:
            return {
                "success": False,
                "error": "No NFC readers found"
            }

        # Select reader (default to index 1 as per original script)
        if reader_index >= len(r_list):
            reader_index = 0

        target_reader = r_list[reader_index]
        reader_name = str(target_reader)

        try:
            # Create connection
            connection = target_reader.createConnection()
            connection.connect()

            # Send GET UID command
            cmd = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            data, sw1, sw2 = connection.transmit(cmd)

            if sw1 == 0x90:
                uid = toHexString(data)
                uid_no_space = ''.join(data_byte.to_bytes(1, 'big').hex().upper() for data_byte in data)
                return {
                    "success": True,
                    "uid": uid,
                    "uid_hex": uid_no_space,
                    "uid_bytes": data,
                    "reader": reader_name,
                    "sw": f"{sw1:02X} {sw2:02X}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Read failed with status: {sw1:02X} {sw2:02X}",
                    "reader": reader_name
                }

        except NoCardException:
            return {
                "success": False,
                "error": "No card present - please place card on reader",
                "reader": reader_name
            }
        except CardConnectionException as e:
            return {
                "success": False,
                "error": f"Card connection error: {str(e)}",
                "reader": reader_name
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No command specified"}))
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        result = get_readers()
    elif command == "read":
        reader_index = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        result = read_uid(reader_index)
    else:
        result = {"success": False, "error": f"Unknown command: {command}"}

    print(json.dumps(result))


if __name__ == "__main__":
    main()

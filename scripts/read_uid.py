#!/usr/bin/env python3
"""
NFC UID Reader Script
Reads NFC card UID using pyscard library
Supports OneKey Lite card info reading
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

# OneKey Lite APDU Constants
APDU_SELECT = [0x00, 0xA4, 0x04, 0x00]
AID_PRIMARY_SAFETY = []  # Select with no data for primary safety
AID_BACKUP_V1 = [0xD1, 0x56, 0x00, 0x01, 0x32, 0x83, 0x40, 0x01]
AID_BACKUP_V2 = [0x6F, 0x6E, 0x65, 0x6B, 0x65, 0x79, 0x2E, 0x62, 0x61, 0x63, 0x6B, 0x75, 0x70, 0x01]  # "onekey.backup" + 0x01
NDEF_APP_AID = "D2760000850101"
NDEF_CC_FILE_ID = 0xE103


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
    clear_apdu_log()
    try:
        r_list = readers()

        if len(r_list) == 0:
            return {
                "success": False,
                "error": "No NFC readers found",
                "apdu_log": get_apdu_log()
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
            data, sw1, sw2 = send_apdu(connection, cmd)

            if sw1 == 0x90:
                uid = toHexString(data)
                uid_no_space = ''.join(data_byte.to_bytes(1, 'big').hex().upper() for data_byte in data)
                return {
                    "success": True,
                    "uid": uid,
                    "uid_hex": uid_no_space,
                    "uid_bytes": data,
                    "reader": reader_name,
                    "sw": f"{sw1:02X} {sw2:02X}",
                    "apdu_log": get_apdu_log()
                }
            else:
                return {
                    "success": False,
                    "error": f"Read failed with status: {sw1:02X} {sw2:02X}",
                    "reader": reader_name,
                    "apdu_log": get_apdu_log()
                }

        except NoCardException:
            return {
                "success": False,
                "error": "No card present - please place card on reader",
                "reader": reader_name,
                "apdu_log": get_apdu_log()
            }
        except CardConnectionException as e:
            return {
                "success": False,
                "error": f"Card connection error: {str(e)}",
                "reader": reader_name,
                "apdu_log": get_apdu_log()
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "apdu_log": get_apdu_log()
        }


# Global APDU log for current session
apdu_log = []


def send_apdu(connection, apdu):
    """Send APDU and return response, logging the exchange"""
    apdu_hex = ''.join(f'{b:02X}' for b in apdu)
    data, sw1, sw2 = connection.transmit(apdu)
    response_hex = ''.join(f'{b:02X}' for b in data) if data else ''
    sw_hex = f'{sw1:02X}{sw2:02X}'

    # Log the APDU exchange
    apdu_log.append({
        'tx': apdu_hex,
        'rx': response_hex,
        'sw': sw_hex
    })

    return data, sw1, sw2


def clear_apdu_log():
    """Clear the APDU log"""
    global apdu_log
    apdu_log = []


def get_apdu_log():
    """Get current APDU log"""
    return apdu_log.copy()


def format_sw(sw1, sw2):
    """Format status word as hex string"""
    return f"{sw1:02X}{sw2:02X}"


def normalize_hex_string(hex_str):
    """Normalize hex string (remove spaces, optional 0x, upper-case)"""
    if not hex_str:
        return ""
    hex_str = "".join(hex_str.split()).upper()
    if hex_str.startswith("0X"):
        hex_str = hex_str[2:]
    return hex_str


def select_primary_safety(connection):
    """Select primary safety domain"""
    apdu = APDU_SELECT + [0x00]  # Lc = 0
    data, sw1, sw2 = send_apdu(connection, apdu)
    return sw1 == 0x90, format_sw(sw1, sw2), data


def select_backup_applet(connection, version):
    """Select backup applet (V1 or V2)"""
    aid = AID_BACKUP_V1 if version == "v1" else AID_BACKUP_V2
    apdu = APDU_SELECT + [len(aid)] + aid
    data, sw1, sw2 = send_apdu(connection, apdu)
    return sw1 == 0x90, format_sw(sw1, sw2), data


def get_device_certificate(connection):
    """Get device certificate"""
    apdu = [0x80, 0xCA, 0xBF, 0x21, 0x06, 0xA6, 0x04, 0x83, 0x02, 0x15, 0x18, 0x00]
    data, sw1, sw2 = send_apdu(connection, apdu)
    if sw1 == 0x90:
        return True, format_sw(sw1, sw2), toHexString(data)
    return False, format_sw(sw1, sw2), None


def get_backup_status(connection):
    """Get backup status"""
    apdu = [0x80, 0x6A, 0x00, 0x00, 0x00]
    data, sw1, sw2 = send_apdu(connection, apdu)
    if sw1 == 0x90 and len(data) > 0:
        return True, format_sw(sw1, sw2), data[0]
    return sw1 == 0x90, format_sw(sw1, sw2), None


def get_pin_status(connection):
    """Get PIN status"""
    apdu = [0x80, 0xCB, 0x80, 0x00, 0x05, 0xDF, 0xFF, 0x02, 0x81, 0x05, 0x00]
    data, sw1, sw2 = send_apdu(connection, apdu)
    if sw1 == 0x90 and len(data) > 0:
        return True, format_sw(sw1, sw2), data[0]
    return sw1 == 0x90, format_sw(sw1, sw2), None


def get_serial_number(connection):
    """Get serial number"""
    apdu = [0x80, 0xCB, 0x80, 0x00, 0x05, 0xDF, 0xFF, 0x02, 0x81, 0x01, 0x00]
    data, sw1, sw2 = send_apdu(connection, apdu)
    if sw1 == 0x90 and len(data) > 0:
        return True, format_sw(sw1, sw2), toHexString(data)
    return sw1 == 0x90, format_sw(sw1, sw2), None


def get_pin_retry_count(connection):
    """Get PIN retry count"""
    apdu = [0x80, 0xCB, 0x80, 0x00, 0x05, 0xDF, 0xFF, 0x02, 0x81, 0x02, 0x00]
    data, sw1, sw2 = send_apdu(connection, apdu)
    if sw1 == 0x90 and len(data) > 0:
        return True, format_sw(sw1, sw2), data[0]
    return sw1 == 0x90, format_sw(sw1, sw2), None


def interpret_backup_status(status_byte, version):
    """Interpret backup status byte based on version"""
    if status_byte is None:
        return "unknown"
    if version == "v1":
        return "no_backup" if status_byte == 0x02 else "has_backup"
    else:  # v2
        return "no_backup" if status_byte == 0x00 else "has_backup" if status_byte == 0x02 else "unknown"


def interpret_pin_status(status_byte, version):
    """Interpret PIN status byte based on version"""
    if status_byte is None:
        return "unknown"
    if version == "v1":
        return "not_set" if status_byte == 0x02 else "set" if status_byte == 0x00 else "unknown"
    else:  # v2
        return "not_set" if status_byte == 0x02 else "set" if status_byte == 0x01 else "unknown"


def get_lite_info(reader_index=1, version="v2"):
    """Get all OneKey Lite card info"""
    clear_apdu_log()
    try:
        r_list = readers()
        if len(r_list) == 0:
            return {"success": False, "error": "No NFC readers found", "apdu_log": get_apdu_log()}

        if reader_index >= len(r_list):
            reader_index = 0

        target_reader = r_list[reader_index]
        reader_name = str(target_reader)

        try:
            connection = target_reader.createConnection()
            connection.connect()

            result = {
                "success": True,
                "reader": reader_name,
                "version": version,
                "serial_number": None,
                "pin_status": None,
                "pin_status_raw": None,
                "backup_status": None,
                "backup_status_raw": None,
                "pin_retry_count": None,
                "certificate": None,
                "errors": []
            }

            # Get certificate first (card starts in primary safety context)
            ok, sw, cert = get_device_certificate(connection)
            if ok:
                result["certificate"] = cert
            else:
                result["errors"].append(f"get_certificate failed: {sw}")

            # For V1: select primary safety then get pin_status, serial_number, pin_retry
            if version == "v1":
                ok, sw, _ = select_primary_safety(connection)
                if not ok:
                    result["errors"].append(f"select_primary_safety failed: {sw}")
                else:
                    ok, sw, val = get_pin_status(connection)
                    if ok:
                        result["pin_status_raw"] = val
                        result["pin_status"] = interpret_pin_status(val, version)
                    else:
                        result["errors"].append(f"get_pin_status failed: {sw}")

                    ok, sw, val = get_serial_number(connection)
                    if ok:
                        result["serial_number"] = val
                    else:
                        result["errors"].append(f"get_serial_number failed: {sw}")

                    ok, sw, val = get_pin_retry_count(connection)
                    if ok:
                        result["pin_retry_count"] = val
                    elif sw != "6985":  # 6985 = PIN not set, retry count N/A
                        result["errors"].append(f"get_pin_retry_count failed: {sw}")

            # Select backup applet
            ok, sw, _ = select_backup_applet(connection, version)
            if not ok:
                result["errors"].append(f"select_backup_applet failed: {sw}")
            else:
                # Get backup status (always from backup applet context)
                ok, sw, val = get_backup_status(connection)
                if ok:
                    result["backup_status_raw"] = val
                    result["backup_status"] = interpret_backup_status(val, version)
                else:
                    result["errors"].append(f"get_backup_status failed: {sw}")

                # For V2: get pin_status, serial_number, pin_retry from backup applet
                if version == "v2":
                    ok, sw, val = get_pin_status(connection)
                    if ok:
                        result["pin_status_raw"] = val
                        result["pin_status"] = interpret_pin_status(val, version)
                    else:
                        result["errors"].append(f"get_pin_status failed: {sw}")

                    ok, sw, val = get_serial_number(connection)
                    if ok:
                        result["serial_number"] = val
                    else:
                        result["errors"].append(f"get_serial_number failed: {sw}")

                    ok, sw, val = get_pin_retry_count(connection)
                    if ok:
                        result["pin_retry_count"] = val
                    elif sw != "6985":  # 6985 = PIN not set, retry count N/A
                        result["errors"].append(f"get_pin_retry_count failed: {sw}")

            result["apdu_log"] = get_apdu_log()
            return result

        except NoCardException:
            return {"success": False, "error": "No card present - please place card on reader", "reader": reader_name, "apdu_log": get_apdu_log()}
        except CardConnectionException as e:
            return {"success": False, "error": f"Card connection error: {str(e)}", "reader": reader_name, "apdu_log": get_apdu_log()}

    except Exception as e:
        return {"success": False, "error": str(e), "apdu_log": get_apdu_log()}


def send_raw_apdu(reader_index=1, apdu_hex=""):
    """Send raw APDU command"""
    clear_apdu_log()
    try:
        r_list = readers()
        if len(r_list) == 0:
            return {"success": False, "error": "No NFC readers found", "apdu_log": get_apdu_log()}

        if reader_index >= len(r_list):
            reader_index = 0

        target_reader = r_list[reader_index]
        reader_name = str(target_reader)

        try:
            apdu = [int(apdu_hex[i:i+2], 16) for i in range(0, len(apdu_hex), 2)]
        except ValueError:
            return {"success": False, "error": "Invalid APDU hex string", "apdu_log": get_apdu_log()}

        try:
            connection = target_reader.createConnection()
            connection.connect()

            data, sw1, sw2 = send_apdu(connection, apdu)
            return {
                "success": True,
                "reader": reader_name,
                "apdu": apdu_hex.upper(),
                "response": toHexString(data) if data else "",
                "sw": format_sw(sw1, sw2),
                "apdu_log": get_apdu_log()
            }

        except NoCardException:
            return {"success": False, "error": "No card present - please place card on reader", "reader": reader_name, "apdu_log": get_apdu_log()}
        except CardConnectionException as e:
            return {"success": False, "error": f"Card connection error: {str(e)}", "reader": reader_name, "apdu_log": get_apdu_log()}

    except Exception as e:
        return {"success": False, "error": str(e), "apdu_log": get_apdu_log()}


# Type 4 Card Functions
def type4_select(connection, aid_hex):
    """Select application by AID"""
    try:
        aid_hex = normalize_hex_string(aid_hex)
        if not aid_hex:
            return False, "0000", "Empty AID"
        if len(aid_hex) % 2 != 0:
            return False, "0000", "Invalid AID length"
        aid = [int(aid_hex[i:i+2], 16) for i in range(0, len(aid_hex), 2)]
    except ValueError:
        return False, "0000", "Invalid AID hex"
    apdu = [0x00, 0xA4, 0x04, 0x00, len(aid)] + aid + [0x00]
    data, sw1, sw2 = send_apdu(connection, apdu)
    response = toHexString(data) if data else ""
    return sw1 == 0x90, format_sw(sw1, sw2), response


def type4_select_with_fallback(connection, aid_hex):
    """Select AID, fallback to NDEF AID if needed"""
    aid_hex = normalize_hex_string(aid_hex)
    if not aid_hex:
        aid_hex = NDEF_APP_AID
    ok, sw, response = type4_select(connection, aid_hex)
    if ok or aid_hex == NDEF_APP_AID:
        return ok, sw, response, aid_hex, False
    ok2, sw2, response2 = type4_select(connection, NDEF_APP_AID)
    if ok2:
        return ok2, sw2, response2, NDEF_APP_AID, True
    return ok, sw, response, aid_hex, False


def type4_read(connection, offset, length):
    """Read data from card"""
    offset_hi = (offset >> 8) & 0xFF
    offset_lo = offset & 0xFF
    apdu = [0x00, 0xB0, offset_hi, offset_lo, length]
    data, sw1, sw2 = send_apdu(connection, apdu)
    response = toHexString(data) if data else ""
    return sw1 == 0x90, format_sw(sw1, sw2), response


def type4_read_bytes(connection, offset, length):
    """Read data from card (raw bytes)"""
    offset_hi = (offset >> 8) & 0xFF
    offset_lo = offset & 0xFF
    apdu = [0x00, 0xB0, offset_hi, offset_lo, length]
    data, sw1, sw2 = send_apdu(connection, apdu)
    return sw1 == 0x90, format_sw(sw1, sw2), data


def type4_write(connection, offset, data_hex):
    """Write data to card"""
    try:
        write_data = [int(data_hex[i:i+2], 16) for i in range(0, len(data_hex), 2)]
    except ValueError:
        return False, "0000", "Invalid data hex"
    offset_hi = (offset >> 8) & 0xFF
    offset_lo = offset & 0xFF
    apdu = [0x00, 0xD0, offset_hi, offset_lo, len(write_data)] + write_data
    data, sw1, sw2 = send_apdu(connection, apdu)
    response = toHexString(data) if data else ""
    return sw1 == 0x90, format_sw(sw1, sw2), response


def type4_update_binary(connection, offset, data_hex):
    """Update binary (ISO 7816-4)"""
    try:
        write_data = [int(data_hex[i:i+2], 16) for i in range(0, len(data_hex), 2)]
    except ValueError:
        return False, "0000", "Invalid data hex"
    offset_hi = (offset >> 8) & 0xFF
    offset_lo = offset & 0xFF
    apdu = [0x00, 0xD6, offset_hi, offset_lo, len(write_data)] + write_data
    data, sw1, sw2 = send_apdu(connection, apdu)
    response = toHexString(data) if data else ""
    return sw1 == 0x90, format_sw(sw1, sw2), response


def type4_select_file(connection, file_id):
    """Select file by File ID"""
    fid = file_id & 0xFFFF
    apdu = [0x00, 0xA4, 0x00, 0x0C, 0x02, (fid >> 8) & 0xFF, fid & 0xFF]
    data, sw1, sw2 = send_apdu(connection, apdu)
    response = toHexString(data) if data else ""
    return sw1 == 0x90, format_sw(sw1, sw2), response


def type4_get_ndef_file_id(connection):
    """Read CC file to get NDEF File ID"""
    ok, sw, _ = type4_select_file(connection, NDEF_CC_FILE_ID)
    if not ok:
        return False, sw, None
    ok, sw, cc = type4_read_bytes(connection, 0, 15)
    if not ok:
        return False, sw, None
    if cc is None or len(cc) < 11:
        return False, sw, None
    fid = (cc[9] << 8) | cc[10]
    return True, "9000", fid


def get_type4_info(reader_index=1, aid_hex=NDEF_APP_AID):
    """Get Type 4 card info - select app and read basic info"""
    clear_apdu_log()
    try:
        r_list = readers()
        if len(r_list) == 0:
            return {"success": False, "error": "No NFC readers found", "apdu_log": get_apdu_log()}

        if reader_index >= len(r_list):
            reader_index = 0

        target_reader = r_list[reader_index]
        reader_name = str(target_reader)

        try:
            connection = target_reader.createConnection()
            connection.connect()

            # Get ATR
            atr = connection.getATR()
            atr_hex = toHexString(atr) if atr else ""

            # Get UID
            cmd = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            data, sw1, sw2 = send_apdu(connection, cmd)
            uid = toHexString(data) if sw1 == 0x90 and data else ""

            result = {
                "success": True,
                "reader": reader_name,
                "atr": atr_hex,
                "uid": uid,
                "aid": aid_hex.upper() if aid_hex else "",
                "selected": False,
                "select_sw": "",
                "select_response": ""
            }

            # Select application
            ok, sw, response, used_aid, fallback_used = type4_select_with_fallback(connection, aid_hex)
            result["selected"] = ok
            result["select_sw"] = sw
            result["select_response"] = response
            result["aid"] = used_aid
            result["aid_requested"] = normalize_hex_string(aid_hex)
            result["aid_fallback"] = fallback_used
            result["apdu_log"] = get_apdu_log()

            return result

        except NoCardException:
            return {"success": False, "error": "No card present - please place card on reader", "reader": reader_name, "apdu_log": get_apdu_log()}
        except CardConnectionException as e:
            return {"success": False, "error": f"Card connection error: {str(e)}", "reader": reader_name, "apdu_log": get_apdu_log()}

    except Exception as e:
        return {"success": False, "error": str(e), "apdu_log": get_apdu_log()}


def type4_operation(reader_index=1, operation="read", aid_hex=NDEF_APP_AID, offset=0, length=16, data_hex=""):
    """Perform Type 4 card operation"""
    clear_apdu_log()
    try:
        r_list = readers()
        if len(r_list) == 0:
            return {"success": False, "error": "No NFC readers found", "apdu_log": get_apdu_log()}

        if reader_index >= len(r_list):
            reader_index = 0

        target_reader = r_list[reader_index]
        reader_name = str(target_reader)

        try:
            connection = target_reader.createConnection()
            connection.connect()

            result = {
                "success": True,
                "reader": reader_name,
                "operation": operation,
                "select_ok": False,
                "select_sw": "",
                "aid": "",
                "operation_ok": False,
                "operation_sw": "",
                "data": ""
            }

            # Select application first
            ok, sw, _, used_aid, fallback_used = type4_select_with_fallback(connection, aid_hex)
            result["select_ok"] = ok
            result["select_sw"] = sw
            result["aid"] = used_aid
            result["aid_requested"] = normalize_hex_string(aid_hex)
            result["aid_fallback"] = fallback_used

            if not ok:
                result["success"] = False
                result["error"] = f"Select failed: SW={sw}"
                result["apdu_log"] = get_apdu_log()
                return result

            # Perform operation
            if operation == "read":
                if used_aid == NDEF_APP_AID:
                    ok, sw, ndef_fid = type4_get_ndef_file_id(connection)
                    if not ok:
                        result["success"] = False
                        result["error"] = f"Select CC failed: SW={sw}"
                        result["apdu_log"] = get_apdu_log()
                        return result
                    ok, sw, _ = type4_select_file(connection, ndef_fid)
                    if not ok:
                        result["success"] = False
                        result["error"] = f"Select NDEF file failed: SW={sw}"
                        result["apdu_log"] = get_apdu_log()
                        return result
                ok, sw, data = type4_read(connection, offset, length)
                result["operation_ok"] = ok
                result["operation_sw"] = sw
                result["data"] = data
            elif operation == "write":
                if used_aid == NDEF_APP_AID:
                    ok, sw, ndef_fid = type4_get_ndef_file_id(connection)
                    if not ok:
                        result["success"] = False
                        result["error"] = f"Select CC failed: SW={sw}"
                        result["apdu_log"] = get_apdu_log()
                        return result
                    ok, sw, _ = type4_select_file(connection, ndef_fid)
                    if not ok:
                        result["success"] = False
                        result["error"] = f"Select NDEF file failed: SW={sw}"
                        result["apdu_log"] = get_apdu_log()
                        return result
                    ok, sw, _ = type4_update_binary(connection, offset, data_hex)
                else:
                    ok, sw, _ = type4_write(connection, offset, data_hex)
                result["operation_ok"] = ok
                result["operation_sw"] = sw
            else:
                result["success"] = False
                result["error"] = f"Unknown operation: {operation}"

            result["apdu_log"] = get_apdu_log()
            return result

        except NoCardException:
            return {"success": False, "error": "No card present - please place card on reader", "reader": reader_name, "apdu_log": get_apdu_log()}
        except CardConnectionException as e:
            return {"success": False, "error": f"Card connection error: {str(e)}", "reader": reader_name, "apdu_log": get_apdu_log()}

    except Exception as e:
        return {"success": False, "error": str(e), "apdu_log": get_apdu_log()}


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='NFC Card Reader CLI - Read NFC cards and communicate with Type 4 / OneKey Lite cards',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s list                          List available NFC readers
  %(prog)s uid                           Read card UID
  %(prog)s uid -r 0                      Read UID using reader index 0
  %(prog)s apdu 00A4040000               Send raw APDU command
  %(prog)s lite                          Read OneKey Lite card info (V2)
  %(prog)s lite -v v1                    Read OneKey Lite V1 card info
  %(prog)s type4                         Connect to Type 4 card
  %(prog)s type4 -a D276000085010100     Connect with custom AID
  %(prog)s type4 read -o 0 -l 32         Read 32 bytes from offset 0
  %(prog)s type4 write -o 0 -d 48454C4C4F  Write "HELLO" at offset 0
'''
    )
    parser.add_argument('-r', '--reader', type=int, default=1, help='Reader index (default: 1)')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    parser.add_argument('--pretty', action='store_true', help='Force human-readable output')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # list command
    list_parser = subparsers.add_parser('list', help='List available NFC readers')

    # uid command
    uid_parser = subparsers.add_parser('uid', help='Read card UID')

    # apdu command
    apdu_parser = subparsers.add_parser('apdu', help='Send raw APDU command')
    apdu_parser.add_argument('apdu_hex', help='APDU command in hex (e.g., 00A4040000)')

    # lite command
    lite_parser = subparsers.add_parser('lite', help='Read OneKey Lite card info')
    lite_parser.add_argument('-v', '--version', choices=['v1', 'v2'], default='v2', help='Card version (default: v2)')

    # type4 command
    type4_parser = subparsers.add_parser('type4', help='Type 4 card operations')
    type4_parser.add_argument('-a', '--aid', default=NDEF_APP_AID, help='Application ID in hex (default: NDEF AID)')
    type4_sub = type4_parser.add_subparsers(dest='type4_cmd', help='Type 4 operations')

    # type4 read
    type4_read = type4_sub.add_parser('read', help='Read data from card')
    type4_read.add_argument('-o', '--offset', type=int, default=0, help='Read offset (default: 0)')
    type4_read.add_argument('-l', '--length', type=int, default=16, help='Read length (default: 16)')

    # type4 write
    type4_write = type4_sub.add_parser('write', help='Write data to card')
    type4_write.add_argument('-o', '--offset', type=int, default=0, help='Write offset (default: 0)')
    type4_write.add_argument('-d', '--data', required=True, help='Data to write in hex')

    args = parser.parse_args()

    # Check if output is piped
    is_tty = sys.stdout.isatty()
    use_json = args.json or (not is_tty and not args.pretty)

    # Execute command
    result = None
    if args.command == 'list':
        result = get_readers()
    elif args.command == 'uid':
        result = read_uid(args.reader)
    elif args.command == 'apdu':
        result = send_raw_apdu(args.reader, args.apdu_hex)
    elif args.command == 'lite':
        result = get_lite_info(args.reader, args.version)
    elif args.command == 'type4':
        if args.type4_cmd == 'read':
            result = type4_operation(args.reader, 'read', args.aid, args.offset, args.length)
        elif args.type4_cmd == 'write':
            result = type4_operation(args.reader, 'write', args.aid, args.offset, 0, args.data)
        else:
            result = get_type4_info(args.reader, args.aid)
    else:
        parser.print_help()
        sys.exit(0)

    # Output result
    if result:
        if use_json:
            print(json.dumps(result))
        else:
            print_formatted(result, args.command)


def print_formatted(result, command):
    """Print result in human-readable format"""
    if not result.get('success', False):
        print(f"\033[91mError:\033[0m {result.get('error', 'Unknown error')}")
        return

    if command == 'list':
        print(f"\033[96mNFC Readers ({result.get('count', 0)}):\033[0m")
        for i, reader in enumerate(result.get('readers', [])):
            marker = '\033[92m*\033[0m' if i == 1 else ' '
            print(f"  {marker} [{i}] {reader}")
        if result.get('count', 0) > 1:
            print(f"\n  \033[92m*\033[0m = default reader")

    elif command == 'uid':
        print(f"\033[96mCard UID:\033[0m {result.get('uid', 'N/A')}")
        print(f"\033[90mReader: {result.get('reader', 'N/A')}\033[0m")

    elif command == 'apdu':
        sw = result.get('sw', '')
        sw_color = '\033[92m' if sw == '9000' else '\033[91m'
        print(f"\033[96mAPDU:\033[0m {result.get('apdu', '')}")
        print(f"\033[96mSW:\033[0m {sw_color}{sw}\033[0m")
        if result.get('response'):
            print(f"\033[96mResponse:\033[0m {result.get('response')}")

    elif command == 'lite':
        print(f"\033[96mOneKey Lite ({result.get('version', 'v2').upper()}):\033[0m")
        print(f"  Serial:      {result.get('serial_number', 'N/A')}")
        pin = result.get('pin_status', 'unknown')
        pin_color = '\033[92m' if pin == 'set' else '\033[93m'
        print(f"  PIN Status:  {pin_color}{pin}\033[0m")
        backup = result.get('backup_status', 'unknown')
        backup_color = '\033[92m' if backup == 'has_backup' else '\033[93m'
        print(f"  Backup:      {backup_color}{backup}\033[0m")
        retry = result.get('pin_retry_count')
        print(f"  PIN Retry:   {retry if retry is not None else 'N/A'}")
        if result.get('errors'):
            print(f"\033[93mWarnings:\033[0m {', '.join(result['errors'])}")

    elif command == 'type4':
        print(f"\033[96mType 4 Card:\033[0m")
        print(f"  UID:    {result.get('uid', 'N/A')}")
        print(f"  ATR:    {result.get('atr', 'N/A')}")
        if 'aid' in result:
            print(f"  AID:    {result.get('aid', 'N/A')}")
            selected = result.get('selected', False)
            sel_color = '\033[92m' if selected else '\033[91m'
            sel_text = 'OK' if selected else 'Failed'
            print(f"  Select: {sel_color}{sel_text} ({result.get('select_sw', '')})\033[0m")
        if 'operation' in result:
            op = result.get('operation', '')
            op_ok = result.get('operation_ok', False)
            op_color = '\033[92m' if op_ok else '\033[91m'
            print(f"  {op.capitalize()}: {op_color}{result.get('operation_sw', '')}\033[0m")
            if op == 'read' and result.get('data'):
                print(f"  Data:   {result.get('data')}")


if __name__ == "__main__":
    main()

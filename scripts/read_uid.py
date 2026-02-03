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


def send_apdu(connection, apdu):
    """Send APDU and return response"""
    data, sw1, sw2 = connection.transmit(apdu)
    return data, sw1, sw2


def format_sw(sw1, sw2):
    """Format status word as hex string"""
    return f"{sw1:02X}{sw2:02X}"


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
    try:
        r_list = readers()
        if len(r_list) == 0:
            return {"success": False, "error": "No NFC readers found"}

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

            return result

        except NoCardException:
            return {"success": False, "error": "No card present - please place card on reader", "reader": reader_name}
        except CardConnectionException as e:
            return {"success": False, "error": f"Card connection error: {str(e)}", "reader": reader_name}

    except Exception as e:
        return {"success": False, "error": str(e)}


def send_raw_apdu(reader_index=1, apdu_hex=""):
    """Send raw APDU command"""
    try:
        r_list = readers()
        if len(r_list) == 0:
            return {"success": False, "error": "No NFC readers found"}

        if reader_index >= len(r_list):
            reader_index = 0

        target_reader = r_list[reader_index]
        reader_name = str(target_reader)

        try:
            apdu = [int(apdu_hex[i:i+2], 16) for i in range(0, len(apdu_hex), 2)]
        except ValueError:
            return {"success": False, "error": "Invalid APDU hex string"}

        try:
            connection = target_reader.createConnection()
            connection.connect()

            data, sw1, sw2 = send_apdu(connection, apdu)
            return {
                "success": True,
                "reader": reader_name,
                "apdu": apdu_hex.upper(),
                "response": toHexString(data) if data else "",
                "sw": format_sw(sw1, sw2)
            }

        except NoCardException:
            return {"success": False, "error": "No card present - please place card on reader", "reader": reader_name}
        except CardConnectionException as e:
            return {"success": False, "error": f"Card connection error: {str(e)}", "reader": reader_name}

    except Exception as e:
        return {"success": False, "error": str(e)}


# Type 4 Card Functions
def type4_select(connection, aid_hex):
    """Select application by AID"""
    try:
        aid = [int(aid_hex[i:i+2], 16) for i in range(0, len(aid_hex), 2)]
    except ValueError:
        return False, "0000", "Invalid AID hex"
    apdu = [0x00, 0xA4, 0x04, 0x00, len(aid)] + aid + [0x00]
    data, sw1, sw2 = send_apdu(connection, apdu)
    response = toHexString(data) if data else ""
    return sw1 == 0x90, format_sw(sw1, sw2), response


def type4_read(connection, offset, length):
    """Read data from card"""
    offset_hi = (offset >> 8) & 0xFF
    offset_lo = offset & 0xFF
    apdu = [0x00, 0xB0, offset_hi, offset_lo, length]
    data, sw1, sw2 = send_apdu(connection, apdu)
    response = toHexString(data) if data else ""
    return sw1 == 0x90, format_sw(sw1, sw2), response


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


def get_type4_info(reader_index=1, aid_hex="F00102030405"):
    """Get Type 4 card info - select app and read basic info"""
    try:
        r_list = readers()
        if len(r_list) == 0:
            return {"success": False, "error": "No NFC readers found"}

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
                "aid": aid_hex.upper(),
                "selected": False,
                "select_sw": "",
                "select_response": ""
            }

            # Select application
            ok, sw, response = type4_select(connection, aid_hex)
            result["selected"] = ok
            result["select_sw"] = sw
            result["select_response"] = response

            return result

        except NoCardException:
            return {"success": False, "error": "No card present - please place card on reader", "reader": reader_name}
        except CardConnectionException as e:
            return {"success": False, "error": f"Card connection error: {str(e)}", "reader": reader_name}

    except Exception as e:
        return {"success": False, "error": str(e)}


def type4_operation(reader_index=1, operation="read", aid_hex="F00102030405", offset=0, length=16, data_hex=""):
    """Perform Type 4 card operation"""
    try:
        r_list = readers()
        if len(r_list) == 0:
            return {"success": False, "error": "No NFC readers found"}

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
                "operation_ok": False,
                "operation_sw": "",
                "data": ""
            }

            # Select application first
            ok, sw, _ = type4_select(connection, aid_hex)
            result["select_ok"] = ok
            result["select_sw"] = sw

            if not ok:
                result["success"] = False
                result["error"] = f"Select failed: SW={sw}"
                return result

            # Perform operation
            if operation == "read":
                ok, sw, data = type4_read(connection, offset, length)
                result["operation_ok"] = ok
                result["operation_sw"] = sw
                result["data"] = data
            elif operation == "write":
                ok, sw, _ = type4_write(connection, offset, data_hex)
                result["operation_ok"] = ok
                result["operation_sw"] = sw
            else:
                result["success"] = False
                result["error"] = f"Unknown operation: {operation}"

            return result

        except NoCardException:
            return {"success": False, "error": "No card present - please place card on reader", "reader": reader_name}
        except CardConnectionException as e:
            return {"success": False, "error": f"Card connection error: {str(e)}", "reader": reader_name}

    except Exception as e:
        return {"success": False, "error": str(e)}


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
    elif command == "lite":
        reader_index = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        version = sys.argv[3] if len(sys.argv) > 3 else "v2"
        result = get_lite_info(reader_index, version)
    elif command == "apdu":
        reader_index = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        apdu_hex = sys.argv[3] if len(sys.argv) > 3 else ""
        result = send_raw_apdu(reader_index, apdu_hex)
    elif command == "type4":
        reader_index = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        aid_hex = sys.argv[3] if len(sys.argv) > 3 else "F00102030405"
        result = get_type4_info(reader_index, aid_hex)
    elif command == "type4_read":
        reader_index = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        aid_hex = sys.argv[3] if len(sys.argv) > 3 else "F00102030405"
        offset = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        length = int(sys.argv[5]) if len(sys.argv) > 5 else 16
        result = type4_operation(reader_index, "read", aid_hex, offset, length)
    elif command == "type4_write":
        reader_index = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        aid_hex = sys.argv[3] if len(sys.argv) > 3 else "F00102030405"
        offset = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        data_hex = sys.argv[5] if len(sys.argv) > 5 else ""
        result = type4_operation(reader_index, "write", aid_hex, offset, 0, data_hex)
    else:
        result = {"success": False, "error": f"Unknown command: {command}"}

    print(json.dumps(result))


if __name__ == "__main__":
    main()

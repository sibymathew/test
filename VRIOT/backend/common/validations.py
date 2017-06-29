import re


def device_mac_address_validator(value):
    try:
        mac_address_pattern = "^([0-9A-Fa-f]{2}[:]){7}[0-9A-Fa-f]{2}$"
        if re.fullmatch(mac_address_pattern, value):
            return True
        return False
    except Exception:
        return False


def gateway_mac_address_validator(value):
    try:
        mac_address_pattern = "^([0-9A-Fa-f]{2}[:]){5}[0-9A-Fa-f]{2}$"
        if re.fullmatch(mac_address_pattern, value):
            return True
        return False
    except Exception:
        return False


def name_basic_validator(value):
    try:
        name_basic_pattern = "^[a-zA-Z0-9 .:!_-]+$"
        if re.fullmatch(name_basic_pattern, value):
            return True
        return False
    except Exception:
        return False


def tags_validator(value):
    try:
        name_basic_pattern = "^[a-zA-Z0-9 !_-]+$"
        for tag in value:
            if not re.fullmatch(name_basic_pattern, tag):
                return False
        return True
    except Exception:
        return False

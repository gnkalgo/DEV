import re
from datetime import datetime, timezone


def parse_user_agent(user_agent: str | None) -> tuple[str, str, str]:
    """Return (device_type, browser, os)."""
    if not user_agent:
        return "Unknown device", "Unknown browser", "Unknown OS"

    ua = user_agent.lower()
    device = "Desktop"
    if "mobile" in ua or "iphone" in ua or "android" in ua:
        device = "Mobile"
    if "ipad" in ua or "tablet" in ua:
        device = "Tablet"

    browser = "Unknown browser"
    if "edg/" in ua or "edge" in ua:
        browser = "Edge"
    elif "chrome" in ua and "chromium" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "opr/" in ua or "opera" in ua:
        browser = "Opera"

    os = "Unknown OS"
    if "windows" in ua:
        os = "Windows"
        if "windows nt 10" in ua:
            os = "Windows 10/11"
    elif "mac os" in ua or "macintosh" in ua:
        os = "macOS"
    elif "iphone" in ua:
        os = "iOS"
    elif "android" in ua:
        os = "Android"
    elif "linux" in ua:
        os = "Linux"

    return device, browser, os


def approximate_location(ip: str | None) -> str:
    if not ip:
        return "Unknown location"
    if ip.startswith("127.") or ip == "::1":
        return "Local network"
    return "India"


def client_id_for_user(user_id) -> str:
    return f"GNK{str(user_id).replace('-', '').upper()[:6]}"


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    cleaned = phone.replace(" ", "")
    if not re.match(r"^\+?[6-9]\d{9}$", cleaned):
        raise ValueError("Invalid Indian phone number")
    return cleaned

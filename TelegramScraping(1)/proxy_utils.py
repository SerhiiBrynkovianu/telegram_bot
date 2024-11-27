# import socks
import sys
from python_socks import ProxyType
def parse_proxy(proxy_str):
    try:
        parts = proxy_str.split(':')
        if sys.version_info.minor >= 6:
            socket = ProxyType.SOCKS5
        # else:
        #     socket = socks.SOCKS5
        if len(parts) == 2:
            ip, port = parts
            return (socket, ip, int(port), False, None, None)  # No authentication
        elif len(parts) == 4:
            ip, port, username, password = parts
            return (socket, ip, int(port), True, username, password)  # With authentication
        else:
            raise ValueError(f"Invalid proxy format: {proxy_str}. Expected format: IP:PORT or IP:PORT:USERNAME:PASSWORD")
    except Exception as e:
        raise ValueError(f"Error parsing proxy: {e}")

def validate_proxies(proxies):
    for proxy in proxies:
        try:
            parse_proxy(proxy)
        except ValueError as e:
            print(f"Proxy validation error: {e}")

def validate_proxy(proxy):
    try:
        parse_proxy(proxy)
        return True
    except ValueError as e:
        print(f"Proxy validation error: {e}")
        return False
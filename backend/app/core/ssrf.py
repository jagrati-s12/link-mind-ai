import ipaddress
import socket
from urllib.parse import urlparse

# Prohibited IP ranges (IPv4 and IPv6)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / cloud metadata (AWS, GCP, Azure)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),   # Shared address space
    ipaddress.ip_network("198.18.0.0/15"),   # Benchmark testing
    ipaddress.ip_network("224.0.0.0/4"),     # Multicast
    ipaddress.ip_network("240.0.0.0/4"),     # Reserved
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),        # Unique local address
    ipaddress.ip_network("fe80::/10"),       # Link-local
    ipaddress.ip_network("ff00::/8"),        # Multicast
]

def is_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    for network in BLOCKED_NETWORKS:
        if ip in network:
            return True
    return False

def validate_safe_url(url: str) -> tuple[bool, str]:
    """
    Validates a URL against SSRF vulnerabilities:
    - Only http and https schemes allowed
    - Hostname must resolve to a public IP
    - Blocks localhost, link-local, private, cloud metadata (169.254.169.254), etc.
    Returns (is_safe, error_reason).
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."

    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return False, f"Invalid scheme '{scheme}'. Only http and https URLs are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL does not contain a valid hostname."

    hostname_lower = hostname.lower()
    if hostname_lower in ("localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal", "instance-data"):
        return False, f"Access to restricted hostname '{hostname}' is blocked."

    # Resolve hostname to IP addresses
    try:
        # Check if the hostname itself is an IP literal
        try:
            ip_obj = ipaddress.ip_address(hostname_lower)
            if is_ip_blocked(ip_obj):
                return False, f"Access to private/restricted IP '{hostname}' is blocked."
            return True, ""
        except ValueError:
            pass

        # Perform DNS resolution
        addr_info = socket.getaddrinfo(hostname, None)
        if not addr_info:
            return False, f"Could not resolve hostname '{hostname}'."

        for item in addr_info:
            ip_str = item[4][0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                if is_ip_blocked(ip_obj):
                    return False, f"Hostname '{hostname}' resolves to blocked IP address '{ip_str}'."
            except ValueError:
                return False, f"Invalid IP address resolved for host '{hostname}'."

    except socket.gaierror:
        return False, f"Could not resolve hostname '{hostname}'."
    except Exception as e:
        return False, f"Failed URL verification: {str(e)}"

    return True, ""

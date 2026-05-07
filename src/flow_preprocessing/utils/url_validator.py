"""
Utility function for URL validation.
"""

import ipaddress
from urllib.parse import urlparse


def _is_private_or_reserved_host(hostname: str) -> bool:
    """Return True if hostname is a private/loopback/link-local/reserved IP address."""
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        return False  # Hostname string, not an IP literal


def validate_url(url: str) -> None:
    """
    Validate URL to prevent SSRF (Server-Side Request Forgery) attacks.

    :param url: URL to validate.
    :raises ValueError: If URL is invalid or targets forbidden destinations.
    """
    try:
        parsed = urlparse(url)

        # Allow only HTTP/HTTPS
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Only HTTP/HTTPS URLs allowed, got: {parsed.scheme}")

        hostname = parsed.hostname or ""

        # Block localhost by name
        if hostname == "localhost":
            raise ValueError("Access to localhost not allowed")

        # Block private/loopback/link-local/reserved IPs (IPv4 and IPv6)
        if _is_private_or_reserved_host(hostname):
            raise ValueError(f"Access to private/reserved IP addresses not allowed: {hostname}")

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Invalid URL: {url}") from e

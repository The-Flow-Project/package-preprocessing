"""
Utility function for URL validation.
"""


def validate_url(url: str) -> None:
    """
    Validate URL to prevent SSRF (Server-Side Request Forgery) attacks.

    :param url: URL to validate.
    :raises ValueError: If URL is invalid or targets forbidden destinations.
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # Allow only HTTP/HTTPS
        if parsed.scheme not in ('http', 'https'):
            raise ValueError(f"Only HTTP/HTTPS URLs allowed, got: {parsed.scheme}")

        # Block localhost and private IPs
        if parsed.hostname in ('localhost', '127.0.0.1', '0.0.0.0'):
            raise ValueError("Access to localhost/private IPs not allowed")

        # Block private IP ranges (optional but recommended)
        # This is a basic check; consider using ipaddress module for production
        if parsed.hostname and parsed.hostname.startswith(('192.168.', '10.', '172.')):
            raise ValueError(f"Access to private IP ranges not allowed: {parsed.hostname}")

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Invalid URL: {url}") from e

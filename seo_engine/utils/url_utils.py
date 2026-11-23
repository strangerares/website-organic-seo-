from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit


def validate_url(value: str) -> str:
    """Validate and normalize an absolute HTTP(S) URL."""
    if not isinstance(value, str):
        raise ValueError("URL must be a string")
    value = value.strip()
    parts = urlsplit(value)
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        raise ValueError("URL must be an absolute HTTP or HTTPS URL")
    if parts.username or parts.password:
        raise ValueError("URLs with embedded credentials are not supported")
    return normalize_url(value)


def normalize_url(value: str) -> str:
    """Remove fragments and a trailing slash from URL paths when appropriate."""
    value, _ = urldefrag(value.strip())
    parts = urlsplit(value)
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"
    scheme = parts.scheme.lower()
    host = parts.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    if parts.port:
        netloc = f"{host}:{parts.port}"
    else:
        netloc = host
    if parts.username or parts.password:
        netloc = parts.netloc
    return urlunsplit((scheme, netloc.lower(), path, parts.query, ""))


def same_domain(url: str, base_url: str, include_subdomains: bool = False) -> bool:
    """Return whether a URL is on the audit domain."""
    try:
        url_host = (urlsplit(url).hostname or "").lower().rstrip(".")
        base_host = (urlsplit(base_url).hostname or "").lower().rstrip(".")
    except ValueError:
        return False
    if include_subdomains:
        return url_host == base_host or url_host.endswith("." + base_host)
    return url_host == base_host


def absolute_url(base_url: str, href: str) -> str:
    """Resolve a link and normalize it, or return an empty string for invalid input."""
    if not href:
        return ""
    try:
        resolved = urljoin(base_url, href.strip())
        return normalize_url(validate_url(resolved))
    except (TypeError, ValueError):
        return ""

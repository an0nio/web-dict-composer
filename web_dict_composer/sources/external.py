from __future__ import annotations

import os
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from web_dict_composer.catalog.service import CatalogEntry
from web_dict_composer.core.config import cache_dir
from web_dict_composer.core.errors import SourceError


MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 30


def cached_external_wordlist(entry: CatalogEntry) -> Path | None:
    path = cache_dir() / "external-wordlists" / f"{entry.id}.txt"
    return path if path.is_file() else None


def download_external_wordlist(entry: CatalogEntry) -> Path:
    if entry.kind != "external_wordlist":
        raise SourceError(f"Only external_wordlist entries can be downloaded: {entry.id}")
    parsed = urlparse(entry.path)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise SourceError(f"External wordlist does not use a valid HTTP(S) URL: {entry.id}")

    cached = cached_external_wordlist(entry)
    if cached:
        return cached

    target = cache_dir() / "external-wordlists" / f"{entry.id}.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    request = Request(entry.path, headers={"User-Agent": "web-dict-composer/0.3"})
    descriptor: int | None = None
    temporary_name: str | None = None
    try:
        with urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            final_url = urlparse(response.geturl())
            if final_url.scheme not in {"https", "http"}:
                raise SourceError(f"Download redirected to an unsupported URL: {response.geturl()}")
            content_type = response.headers.get("Content-Type", "").casefold()
            if "text/html" in content_type:
                raise SourceError(
                    f"URL for '{entry.id}' returned HTML; use a direct raw wordlist URL."
                )
            declared_size = response.headers.get("Content-Length")
            if declared_size and int(declared_size) > MAX_DOWNLOAD_BYTES:
                maximum_mib = MAX_DOWNLOAD_BYTES // (1024 * 1024)
                raise SourceError(
                    f"External wordlist exceeds the {maximum_mib} MiB limit."
                )

            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.",
                dir=target.parent,
            )
            total = 0
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                while chunk := response.read(64 * 1024):
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise SourceError(
                            "External wordlist exceeded the download limit while reading."
                        )
                    handle.write(chunk)

        temporary = Path(temporary_name)
        if temporary.stat().st_size == 0:
            raise SourceError(f"Downloaded wordlist is empty: {entry.id}")
        try:
            temporary.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise SourceError(f"Downloaded wordlist is not UTF-8 text: {entry.id}") from exc
        os.replace(temporary, target)
        temporary_name = None
        return target
    except (HTTPError, URLError, OSError, ValueError) as exc:
        raise SourceError(f"Could not download '{entry.id}': {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name:
            temporary = Path(temporary_name)
            if temporary.exists():
                temporary.unlink()

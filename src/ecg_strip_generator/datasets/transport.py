"""Bounded HTTPS downloads. Redirects and partial HTTP responses fail closed."""

import os
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Source redirect refused; review the registry URL")


def download(url: str, destination: Path, limit: int) -> int:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "physionet.org"
        or not parsed.path.startswith("/files/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Only registered PhysioNet HTTPS file URLs are allowed")
    request = Request(
        url, headers={"Accept-Encoding": "identity", "User-Agent": "ECG-Strip-Generator/0.1"}
    )
    started = time.monotonic()
    with build_opener(NoRedirect()).open(request, timeout=30) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError("Expected unchanged URL and complete HTTP 200 response")
        if response.headers.get("Content-Encoding", "identity") != "identity":
            raise ValueError("Encoded responses cannot prove source byte identity")
        if "html" in response.headers.get("Content-Type", "").lower():
            raise ValueError("HTML response is not a source data file")
        length = response.headers.get("Content-Length")
        if length is None or not length.isdecimal() or not 0 < int(length) <= limit:
            raise ValueError("A positive, bounded Content-Length is required")
        total = 0
        with destination.open("xb") as output:
            while block := response.read(65536):
                total += len(block)
                if total > int(length) or time.monotonic() - started > 300:
                    raise ValueError("Download exceeds declared length or time limit")
                output.write(block)
            output.flush()
            os.fsync(output.fileno())
        if total != int(length):
            raise ValueError("Incomplete download")
    return total

"""HTTP boundary simulation; no live network in fast tests."""

import io

import pytest

from ecg_strip_generator.datasets import transport

URL = "https://physionet.org/files/nsrdb/1.0.0/a.dat"


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload=b"abcdef", headers=None, url=URL):
        super().__init__(payload)
        self.headers = headers if headers is not None else {"Content-Length": "6"}
        self.url = url

    def geturl(self):
        return self.url


def mock_response(monkeypatch, response):
    class Opener:
        def open(self, request, timeout):
            assert timeout == 30
            return response

    monkeypatch.setattr(transport, "build_opener", lambda *args: Opener())


def test_exact_bytes_and_no_overwrite(monkeypatch, tmp_path):
    mock_response(monkeypatch, Response())
    target = tmp_path / "a"
    assert transport.download(URL, target, 100) == 6
    assert target.read_bytes() == b"abcdef"
    mock_response(monkeypatch, Response())
    with pytest.raises(FileExistsError):
        transport.download(URL, target, 100)


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Content-Length": "0"},
        {"Content-Length": "999"},
        {"Content-Length": "bad"},
        {"Content-Length": "6", "Content-Encoding": "gzip"},
        {"Content-Length": "6", "Content-Type": "text/html"},
    ],
)
def test_invalid_headers(monkeypatch, tmp_path, headers):
    mock_response(monkeypatch, Response(headers=headers))
    with pytest.raises(ValueError):
        transport.download(URL, tmp_path / "a", 100)
    assert not (tmp_path / "a").exists()


@pytest.mark.parametrize("payload", [b"abc", b"abcdefghi"])
def test_truncated_or_oversized_response(monkeypatch, tmp_path, payload):
    mock_response(monkeypatch, Response(payload))
    with pytest.raises(ValueError):
        transport.download(URL, tmp_path / "a", 100)


@pytest.mark.parametrize(
    "url", ["http://physionet.org/files/a", "https://evil.test/files/a", URL + "?x=1", URL + "#a"]
)
def test_wrong_origin_refused(tmp_path, url):
    with pytest.raises(ValueError):
        transport.download(url, tmp_path / "a", 100)


def test_redirect_and_partial_status(monkeypatch, tmp_path):
    with pytest.raises(ValueError, match="redirect"):
        transport.NoRedirect().redirect_request(None, None, 302, "", {}, URL)
    response = Response()
    response.status = 206
    mock_response(monkeypatch, response)
    with pytest.raises(ValueError):
        transport.download(URL, tmp_path / "a", 100)


def test_changed_url_rejected(monkeypatch, tmp_path):
    mock_response(monkeypatch, Response(url="https://evil.test/a"))
    with pytest.raises(ValueError):
        transport.download(URL, tmp_path / "a", 100)

import pytest
from shortener.core import Shortener


def test_us01_six_char_code():
    assert len(Shortener().shorten("https://example.com/a")) == 6

def test_us01_idempotent():
    s = Shortener()
    assert s.shorten("https://x.io") == s.shorten("https://x.io")

def test_us01_invalid():
    with pytest.raises(ValueError):
        Shortener().shorten("notaurl")

def test_us02_resolve():
    s = Shortener(); c = s.shorten("https://x.io/p")
    assert s.resolve(c) == "https://x.io/p"

def test_us02_missing():
    with pytest.raises(KeyError):
        Shortener().resolve("zzzzzz")

def test_us03_visits():
    s = Shortener(); c = s.shorten("https://x.io/v")
    s.resolve(c); s.resolve(c)
    assert s.visits[c] == 2

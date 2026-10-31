import subprocess
import wave
from pathlib import Path
import pytest
from reader_app import speech


def write_wav(path):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x01\x00" * 1600)


@pytest.mark.parametrize("text", [None, "", " \n ", "a" * 5001])
def test_invalid_text_rejected(text):
    with pytest.raises(ValueError):
        speech.validate_text(text)


def test_text_whitespace_normalized_and_limit_inclusive():
    assert speech.validate_text(" hello \n") == "hello"
    assert len(speech.validate_text("a" * 5000)) == 5000


@pytest.mark.parametrize("rate", [99, 241, True, 170.5, "170"])
def test_invalid_rates_rejected(rate):
    with pytest.raises(ValueError):
        speech.validate_rate(rate)


def test_wav_metadata_and_empty_audio(tmp_path):
    path = tmp_path / "valid.wav"
    write_wav(path)
    assert speech.wav_info(path)["duration_seconds"] == .1
    with wave.open(str(path), "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
    with pytest.raises(ValueError, match="empty"):
        speech.wav_info(path)


def test_output_extension_and_existing_file_protected(tmp_path):
    with pytest.raises(ValueError, match="wav"):
        speech.synthesize("hello", tmp_path / "bad.mp3")
    path = tmp_path / "existing.wav"
    path.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        speech.synthesize("hello", path)
    assert path.read_bytes() == b"original"


def test_worker_receives_text_via_stdin_and_returns_valid_audio(tmp_path, monkeypatch):
    output = tmp_path / "speech.wav"
    recorded = {}
    class Process:
        returncode = 0
        def __init__(self, command, **kwargs):
            recorded["command"] = command
            recorded["kwargs"] = kwargs
        def communicate(self, input=None, timeout=None):
            recorded["input"] = input
            write_wav(output)
            return "", ""
    monkeypatch.setattr(speech.subprocess, "Popen", Process)
    text = "Literal text: $(nothing) `example` and quotes."
    assert speech.synthesize(text, output) == output
    assert recorded["input"] == text
    assert text not in recorded["command"]
    assert "shell" not in recorded["kwargs"]


def test_worker_failure_removes_partial_output(tmp_path, monkeypatch):
    output = tmp_path / "failed.wav"
    class Process:
        returncode = 1
        def __init__(self, *args, **kwargs):
            pass
        def communicate(self, **kwargs):
            output.write_bytes(b"partial")
            return "", "error"
    monkeypatch.setattr(speech.subprocess, "Popen", Process)
    with pytest.raises(RuntimeError, match="engine failed"):
        speech.synthesize("hello", output)
    assert not output.exists()

"""Generate WAV in an isolated process so Windows COM stays on its own thread."""
import os
from pathlib import Path
import subprocess
import sys
import wave
from .runtime import ROOT

MAX_TEXT_LENGTH = 5000


def validate_text(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Enter or extract some text before generating speech.")
    text = text.strip()
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError("Speech is limited to 5,000 characters at a time.")
    return text


def validate_rate(rate):
    if isinstance(rate, bool) or not isinstance(rate, int) or not 100 <= rate <= 240:
        raise ValueError("Speech rate must be an integer between 100 and 240 words per minute.")
    return rate


def wav_info(path):
    with wave.open(str(path), "rb") as audio:
        if audio.getnframes() == 0 or audio.getframerate() <= 0:
            raise ValueError("Speech engine produced an empty WAV file.")
        return {"frames": audio.getnframes(), "sample_rate": audio.getframerate(),
                "channels": audio.getnchannels(), "sample_width": audio.getsampwidth(),
                "duration_seconds": audio.getnframes() / audio.getframerate()}


def synthesize(text, output, rate=170, timeout=60):
    text = validate_text(text)
    rate = validate_rate(rate)
    output = Path(output).resolve()
    if output.suffix.lower() != ".wav":
        raise ValueError("Speech output must use a .wav extension.")
    if output.exists():
        raise FileExistsError("Choose a new output filename; an audio file already exists there.")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "reader_app.speech_worker", "--output", str(output), "--rate", str(rate)]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8", cwd=ROOT, creationflags=flags)
    try:
        _, errors = process.communicate(input=text, timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, creationflags=flags, check=False)
        else:
            process.kill()
        process.communicate()
        output.unlink(missing_ok=True)
        raise RuntimeError("Speech generation timed out. Try a shorter passage.") from None
    if process.returncode != 0:
        output.unlink(missing_ok=True)
        raise RuntimeError("The offline speech engine failed. Check that a supported system voice is installed.")
    try:
        wav_info(output)
    except (OSError, EOFError, wave.Error, ValueError):
        output.unlink(missing_ok=True)
        raise RuntimeError("Speech generation did not produce a valid nonempty WAV file.") from None
    return output

"""Internal worker: render text from stdin with the OS's offline speech voice."""
import argparse
from pathlib import Path
import sys
from .speech import validate_rate, validate_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--rate", type=int, default=170)
    args = parser.parse_args()
    text = validate_text(sys.stdin.buffer.read(20001).decode("utf-8"))
    validate_rate(args.rate)
    import pyttsx3
    engine = pyttsx3.init()
    try:
        engine.setProperty("rate", args.rate)
        engine.setProperty("volume", 1.0)
        engine.save_to_file(text, str(args.output))
        engine.runAndWait()
    finally:
        engine.stop()


if __name__ == "__main__":
    main()

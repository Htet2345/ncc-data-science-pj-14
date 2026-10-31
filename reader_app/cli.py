"""Read a document image into TXT/JSON, optionally generating a WAV."""
import argparse
import json
from pathlib import Path
from PIL import Image
from .ocr import DocumentReader
from .speech import synthesize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/document"), help="Output filename prefix")
    parser.add_argument("--speak", action="store_true")
    parser.add_argument("--rate", type=int, default=170)
    args = parser.parse_args()
    paths = [args.output.with_suffix(suffix) for suffix in (".txt", ".json")]
    if args.speak:
        paths.append(args.output.with_suffix(".wav"))
    if any(path.exists() for path in paths):
        parser.error("An output file already exists. Choose a new --output prefix.")
    try:
        with Image.open(args.image) as image:
            result = DocumentReader().extract(image)
        if args.speak and not result.text:
            parser.error("No text recognized; speech was not generated.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        paths[0].write_text(result.text + "\n", encoding="utf-8")
        paths[1].write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.speak:
            synthesize(result.text, args.output.with_suffix(".wav"), args.rate)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(result.text or "No text recognized.")
    print(f"Saved outputs using prefix: {args.output.resolve()}")


if __name__ == "__main__":
    main()

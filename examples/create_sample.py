"""Create an original, reproducible printed-text image for the OCR demo."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_sample(output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    font = ImageFont.truetype(str(font_path), 42) if font_path.is_file() else ImageFont.load_default(size=42)
    image = Image.new("RGB", (1100, 240), "white")
    draw = ImageDraw.Draw(image)
    draw.text((50, 45), "DATA SCIENCE PROJECT 14", font=font, fill="black")
    draw.text((50, 125), "Read this text and turn it into speech.", font=font, fill="black")
    image.save(output)
    return output


if __name__ == "__main__":
    path = Path(__file__).resolve().parents[1] / "artifacts/sample_document.png"
    print(create_sample(path))

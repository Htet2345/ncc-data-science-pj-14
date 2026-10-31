"""Validate document images and extract recognized lines with RapidOCR."""
from dataclasses import asdict, dataclass
from threading import Lock
import math
import numpy as np
from PIL import Image, ImageOps
from .runtime import ROOT

MAX_PIXELS = 4_000_000


def prepare_image(image):
    if not isinstance(image, Image.Image):
        raise ValueError("Upload an image before extracting text.")
    if image.width < 32 or image.height < 32:
        raise ValueError("Use an image at least 32 pixels wide and high.")
    if image.width * image.height > MAX_PIXELS:
        raise ValueError("Use an image with no more than 4 million pixels.")
    if getattr(image, "n_frames", 1) != 1:
        raise ValueError("Use a single still image.")
    image = ImageOps.exif_transpose(image)
    rgba = image.convert("RGBA")
    canvas = Image.new("RGBA", rgba.size, "white")
    canvas.alpha_composite(rgba)
    return canvas.convert("RGB")


@dataclass
class TextLine:
    text: str
    score: float
    box: list[list[float]]


@dataclass
class OCRResult:
    text: str
    lines: list[TextLine]

    def to_dict(self):
        return asdict(self)


def parse_result(raw):
    if raw.txts is None or len(raw.txts) == 0:
        return OCRResult("", [])
    if raw.scores is None or raw.boxes is None or not len(raw.txts) == len(raw.scores) == len(raw.boxes):
        raise ValueError("OCR returned inconsistent line data.")
    lines = []
    for text, score, box in zip(raw.txts, raw.scores, raw.boxes):
        score = float(score)
        points = np.asarray(box, dtype=float)
        if not math.isfinite(score) or not 0 <= score <= 1 or points.shape != (4, 2) or not np.isfinite(points).all():
            raise ValueError("OCR returned invalid confidence or coordinates.")
        text = str(text).strip()
        if text:
            lines.append(TextLine(text, score, points.tolist()))
    # Preserve the OCR engine's reading order rather than inventing column layout.
    return OCRResult("\n".join(line.text for line in lines), lines)


class DocumentReader:
    def __init__(self):
        self.engine = None
        self.lock = Lock()

    def extract(self, image):
        image = prepare_image(image)
        with self.lock:
            if self.engine is None:
                from rapidocr import RapidOCR
                self.engine = RapidOCR(params={
                    "EngineConfig.onnxruntime.intra_op_num_threads": 2,
                    "EngineConfig.onnxruntime.inter_op_num_threads": 1,
                })
            # RapidOCR's NumPy convention is BGR; Pillow above uses RGB.
            bgr = np.asarray(image)[:, :, ::-1].copy()
            raw = self.engine(bgr)
        return parse_result(raw)

from types import SimpleNamespace
import numpy as np
import pytest
from PIL import Image
from reader_app.ocr import DocumentReader, parse_result, prepare_image


def raw_result(texts=("First line", "Second line"), scores=(.9, .8)):
    box = [[0, 0], [100, 0], [100, 20], [0, 20]]
    return SimpleNamespace(txts=texts, scores=scores, boxes=[box for _ in texts])


def test_line_order_scores_and_json_serialization():
    result = parse_result(raw_result())
    assert result.text == "First line\nSecond line"
    assert result.lines[0].score == .9
    assert result.to_dict()["lines"][1]["box"][2] == [100.0, 20.0]


@pytest.mark.parametrize("texts", [None, [], ()])
def test_empty_results_are_handled(texts):
    result = parse_result(SimpleNamespace(txts=texts))
    assert result.text == "" and result.lines == []


def test_empty_lines_are_removed_without_reordering():
    result = parse_result(raw_result(("  Hello  ", " ", "World"), (.9, .7, .8)))
    assert result.text == "Hello\nWorld"


@pytest.mark.parametrize("bad_score", [-.1, 1.1, float("nan"), float("inf")])
def test_invalid_confidence_rejected(bad_score):
    with pytest.raises(ValueError):
        parse_result(raw_result(("text",), (bad_score,)))


def test_inconsistent_line_counts_rejected():
    with pytest.raises(ValueError, match="inconsistent"):
        parse_result(raw_result(("a", "b"), (.9,)))


@pytest.mark.parametrize("box", [[[1, 2]], [[0, 0], [1, 0], [1, float("nan")], [0, 1]]])
def test_invalid_boxes_rejected(box):
    raw = raw_result(("text",), (.9,))
    raw.boxes = [box]
    with pytest.raises(ValueError):
        parse_result(raw)


@pytest.mark.parametrize("image", [None, "file.png", np.zeros((40, 40))])
def test_non_image_inputs_rejected(image):
    with pytest.raises(ValueError, match="Upload"):
        prepare_image(image)


@pytest.mark.parametrize("size", [(31, 40), (40, 31), (2001, 2000)])
def test_image_dimensions_rejected(size):
    with pytest.raises(ValueError):
        prepare_image(Image.new("RGB", size))


def test_orientation_and_transparency():
    image = Image.new("RGBA", (40, 60), (0, 0, 0, 0))
    image.getexif()[274] = 6
    result = prepare_image(image)
    assert result.size == (60, 40)
    assert result.mode == "RGB" and result.getpixel((0, 0)) == (255, 255, 255)


def test_reader_passes_bgr_pixels_and_reuses_engine():
    calls = []
    def engine(image):
        calls.append(image.copy())
        return raw_result()
    reader = DocumentReader()
    reader.engine = engine
    for _ in range(2):
        assert reader.extract(Image.new("RGB", (40, 40), "red")).text.startswith("First")
    assert len(calls) == 2
    assert calls[0][0, 0].tolist() == [0, 0, 255]
    assert reader.engine is engine

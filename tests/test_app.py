import gradio as gr
import pytest
from app import create_demo
from reader_app.ocr import OCRResult, TextLine


class Reader:
    def extract(self, image):
        if image is None:
            raise ValueError("Upload an image first.")
        return OCRResult("Editable text", [TextLine("Editable text", .9, [[0, 0]] * 4)])


def callback(demo, name):
    return next(item.fn for item in demo.fns.values() if item.api_name == name)


def test_interface_actions_and_ocr_clear_old_audio(tmp_path, monkeypatch):
    import app
    monkeypatch.setattr(app, "CACHE", tmp_path)
    demo = create_demo(Reader())
    config = demo.get_config_file()
    names = {item.get("api_name") for item in config["dependencies"]}
    assert {"extract", "speak", "export_text"} <= names
    text, download, status, audio = callback(demo, "extract")(object())
    assert text == "Editable text"
    assert audio is None
    assert "Review" in status
    assert open(download, encoding="utf-8").read().strip() == "Editable text"


def test_reviewed_text_export_preserves_edits(tmp_path, monkeypatch):
    import app
    monkeypatch.setattr(app, "CACHE", tmp_path)
    demo = create_demo(Reader())
    path = callback(demo, "export_text")(" My corrected text. ")
    assert open(path, encoding="utf-8").read() == "My corrected text.\n"


def test_speech_callback_uses_edited_text_and_rate(tmp_path, monkeypatch):
    import app
    monkeypatch.setattr(app, "CACHE", tmp_path)
    recorded = []
    def speaker(text, path, rate):
        recorded.append((text, rate))
        return path
    demo = create_demo(Reader(), speaker=speaker)
    assert callback(demo, "speak")("Corrected text", 180).endswith(".wav")
    assert recorded == [("Corrected text", 180)]


def test_missing_image_callback_error():
    with pytest.raises(gr.Error, match="Upload an image"):
        callback(create_demo(Reader()), "extract")(None)

"""Gradio document reader: extract text, review it, then generate speech."""
import argparse
import logging
from uuid import uuid4
from reader_app.runtime import CACHE
from reader_app.ocr import DocumentReader
from reader_app.speech import synthesize
import gradio as gr

LOGGER = logging.getLogger(__name__)


def create_demo(reader=None, speaker=synthesize):
    reader = reader or DocumentReader()

    def extract(image):
        try:
            result = reader.extract(image)
        except ValueError as error:
            raise gr.Error(str(error)) from None
        except Exception:
            LOGGER.exception("OCR failed")
            raise gr.Error("Could not read this image. Try a clear, upright photo of printed text.") from None
        folder = CACHE / "exports"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"text-{uuid4().hex}.txt"
        path.write_text(result.text + "\n", encoding="utf-8")
        if result.lines:
            status = f"Read {len(result.lines)} text lines. Review the text before generating speech."
        else:
            status = "No text found. Try a sharper, well-lit image or enter text manually."
        return result.text, str(path), status, None

    def speak(text, rate):
        try:
            path = speaker(text, CACHE / "audio" / f"speech-{uuid4().hex}.wav", rate)
        except (ValueError, RuntimeError, OSError) as error:
            raise gr.Error(str(error)) from None
        return str(path)

    def export_reviewed(text):
        if not isinstance(text, str) or not text.strip():
            raise gr.Error("Enter or extract text first.")
        folder = CACHE / "exports"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"reviewed-{uuid4().hex}.txt"
        path.write_text(text.strip() + "\n", encoding="utf-8")
        return str(path)

    with gr.Blocks(title="Document Reader | PJ14", analytics_enabled=False,
                   delete_cache=(300, 300)) as demo:
        gr.Markdown("# Document Reader\nTurn printed text in an image into editable text and spoken audio.")
        with gr.Row():
            with gr.Column():
                image = gr.Image(type="pil", image_mode=None, sources=["upload"], label="Document image")
                extract_button = gr.Button("Extract text", variant="primary")
                status = gr.Markdown("Upload a clear image of printed English text to begin.")
            with gr.Column():
                text = gr.Textbox(label="Review and edit the text", lines=9, max_lines=18, interactive=True)
                rate = gr.Slider(100, 240, value=170, step=10, precision=0, label="Speech speed (words per minute)")
                with gr.Row():
                    speak_button = gr.Button("Generate speech", variant="primary")
                    save_button = gr.Button("Save reviewed text")
                audio = gr.Audio(type="filepath", label="Listen or download WAV", autoplay=False)
                download = gr.File(label="Download text", interactive=False)
        gr.ClearButton([image, text, audio, download, status], value="Clear")
        extract_button.click(extract, [image], [text, download, status, audio], api_name="extract", concurrency_limit=1)
        speak_button.click(speak, [text, rate], [audio], api_name="speak", concurrency_limit=1)
        save_button.click(export_reviewed, [text], [download], api_name="export_text")
        gr.Markdown("Review recognition errors before listening. One image at a time; printed English is the tested use case. "
                    "Image limit: 10 MB / 4 million pixels. Speech limit: 5,000 characters. "
                    "Speech uses an installed system voice and does not translate text.")
    return demo


demo = create_demo()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    demo.queue(max_size=8).launch(server_name=args.host, server_port=args.port,
        share=False, inbrowser=False, max_file_size="10mb", show_error=False)


if __name__ == "__main__":
    main()

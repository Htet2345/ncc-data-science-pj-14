# PJ14: OCR and Text-to-Speech

A local Gradio app that extracts printed text from an image, lets you review or edit it, and generates a playable/downloadable WAV file using an installed offline system voice. Text can also be saved as UTF-8. OCR runs with RapidOCR and ONNX Runtime on CPU; speech uses pyttsx3 with Windows SAPI5.

Course mapping: **module 6.2, videos 01–10 — OCR + TTS**. This is an original implementation based on the recorded lesson topic. The teacher's exact video contents, source code, datasets and submission rubric have not been independently verified.

## Setup in VS Code (Windows PowerShell)

Python 3.13.1 on Windows was used for verification. Open this folder in VS Code and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe app.py
```

Open [Document Reader](http://127.0.0.1:7860). Alternatively, use the included **PJ14: Document reader** F5 debugger configuration. Press Ctrl+C in the terminal to stop the server.

Install `requirements-dev.txt` instead if you prefer compatible package ranges over exact tested versions. The selected RapidOCR wheel includes its default detection, orientation and recognition models, so a separate Tesseract installer is not required. No GPU, paid API or speech-service account is needed. The first OCR initialization may take longer than later requests.

## Use the app

1. Upload a clear, upright photo of printed text and select **Extract text**.
2. Review and correct the recognized text in the editable text box.
3. Choose the speech speed, then select **Generate speech**.
4. Play or download the generated WAV using the audio control. Audio does not autoplay.
5. Select **Save reviewed text** to download your corrected text; the initial text download contains the unedited OCR result.

You can type text directly and generate speech without uploading an image. Extracting another image clears the previous audio result. Clear removes the visible input and outputs.

Input limits are 10 MB per upload, 4 million image pixels, a minimum width and height of 32 pixels, and 5,000 characters per speech request. The speed range is 100–240 words per minute. Use still PNG/JPEG/WebP images. The reader validates animation when it receives a multi-frame image, but Gradio may re-encode uploads first; ordinary still images are the intended input.

The tested use case is **printed English**. Recognition and pronunciation of other languages depend on the bundled OCR model and installed speech voices and are not verified. The app does not translate text. Handwriting, small/blurred print, complex tables and multiple columns may yield recognition or reading-order errors.

## Reproducible CLI example

Create an original sample image and run OCR plus speech:

```powershell
.\.venv\Scripts\python.exe examples\create_sample.py
.\.venv\Scripts\python.exe -m reader_app.cli artifacts\sample_document.png --output artifacts\demo --speak
```

This produces `artifacts/demo.txt`, `artifacts/demo.json` (recognized lines, confidence scores and boxes), and `artifacts/demo.wav`. Existing output files are protected; use another output prefix for a new run. Without `--speak`, only TXT and JSON are produced. Choose a rate with `--rate 180`.

The sample generator draws two printed lines with a system font; it does not download or redistribute any photos or fonts. OCR scores describe the recognition engine's own confidence, not a guarantee that the text is correct. The engine's line ordering is preserved; the app does not infer a new document layout.

## How the implementation works

Image preparation applies EXIF orientation, composites transparency against white, validates dimensions and converts Pillow RGB data into the BGR convention used by RapidOCR's NumPy input. The OCR service initializes lazily and serializes requests using a lock. It validates returned line scores and four-point coordinates before exporting them.

Speech receives the reviewed text, never an interpolated shell command. Each synthesis runs in a separate Python process so Windows COM speech initialization stays on that process's main thread. Text is passed through standard input; a 60-second timeout bounds each rendering job. The parent checks that the output is a readable, nonempty WAV before returning it. Failed or timed-out jobs remove partial output. This produces a file without playing it through the computer's speakers.

Generated text and audio use unique filenames under `.cache/`. Gradio is configured to sweep tracked temporary uploads/outputs every five minutes and remove items older than five minutes. Locally generated files that Gradio does not track can remain until the project cache is removed. The application has no permanent document-history database.

After dependencies are installed, OCR and synthesis use local models/voices. Uploaded document content is not submitted to a cloud OCR or speech service. Gradio analytics are disabled. A browser can still contact external resources through its own extensions or links. The run command binds to 127.0.0.1 and does not create a public share link.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Automated tests cover image validation, orientation/transparency, BGR conversion, empty OCR output, line/score/box validation, speech text/rate limits, WAV validation, protection of existing audio, safe stdin delivery to the worker, partial-output cleanup and UI callback behavior. Unit tests use deterministic OCR/worker substitutes; separate real OCR, native speech and HTTP checks validate the installed engines.

### Verified run

On 31 October 2026, **38 automated tests passed**. The real OCR engine recognized both lines of the generated sample exactly: `DATA SCIENCE PROJECT 14` and `Read this text and turn it into speech.` The CLI produced TXT, JSON and a nonempty WAV file.

Live Gradio-client checks verified image upload and extraction, downloading the text, exporting an edited passage, generating non-silent native speech, blank-image handling and an empty-speech error. Browser checks confirmed the interface rendered and generating speech from typed text displayed a waveform, duration and download control. The live-check WAV was mono PCM at 22,050 Hz and approximately 2.87 seconds long. These examples are functional checks, not a benchmark of OCR accuracy. The verification server was stopped afterward.

## System notes

Windows needs an installed SAPI-compatible voice; standard Windows English voices are the verified setup. Voice availability and pronunciation depend on the operating system. No online speech provider is used. If audio generation fails, check your Windows speech voices and try a shorter English passage.

Other operating systems are not verified. pyttsx3 uses different native speech backends there and may require additional packages. In particular, this Windows-tested submission does not claim to run unchanged on Hugging Face Spaces or a Linux server.

## Files

```text
app.py                      Gradio image/text/audio interface
reader_app/
  runtime.py                Project-local runtime/cache configuration
  ocr.py                    Image preparation and OCR service
  speech.py                 Worker isolation, limits and WAV checks
  speech_worker.py          Native offline speech renderer
  cli.py                    Image-to-TXT/JSON/WAV command
examples/create_sample.py   Reproducible original text image
tests/                     Unit and interface checks
.vscode/                   Interpreter, debugger and tasks
requirements*.txt          Dependency ranges and exact tested versions
```

Only source, configuration, tests and dependencies are submitted. Environments, caches, generated samples/audio and the local verification report are excluded from GitHub. No demo screenshots are included.

## Attribution and references

- [RapidOCR project](https://github.com/RapidAI/RapidOCR), [installation](https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/install/) and [usage](https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/usage/). RapidOCR provides PaddleOCR-derived models; see its [model attribution statement](https://rapidai.github.io/RapidOCRDocs/main/en/model_licenses/) for upstream terms.
- [ONNX Runtime](https://onnxruntime.ai/docs/): local CPU inference backend.
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3): native offline speech engine integration.
- [Gradio](https://www.gradio.app/): local web interface, uploads and audio output.

Repository: [ncc-data-science-pj-14](https://github.com/Htet2345/ncc-data-science-pj-14)

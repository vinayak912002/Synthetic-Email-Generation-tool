# Synthetic Email Data Creation Pipeline

Small utilities to generate synthetic email JSON files for testing, demos, and data experiments.

## What this project contains

- [email_generator.py](email_generator.py), [email_generator_nojson.py](email_generator_nojson.py), [email_generator_nojson_multiline.py](email_generator_nojson_multiline.py): scripts to generate synthetic emails in JSON or plain formats.
- `emails/`: output directory containing generated email JSON files (example: `email_0001.json`).
- [requirements.txt](requirements.txt): Python dependencies.
- [ollama_test.py](ollama_test.py): small experiment script (if using Ollama or local LLMs).

## Requirements

- Python 3.8+ (recommended)
- Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Usage

Basic usage examples — run the generator scripts to produce synthetic emails into the `emails/` folder.

- Generate JSON emails (default generator):

```bash
python email_generator.py
```

- Generate plain-text/multiline outputs (alternative generators):

```bash
python email_generator_nojson.py
python email_generator_nojson_multiline.py
```

Outputs are written to the `emails/` directory as `email_XXXX.json` (or other formats depending on the script).

## Examples

- Inspect a sample output:

```bash
dir emails
type emails\email_0001.json
```

## Customization

- Open the generator scripts to adjust templates, fields, or the number of generated samples.
- Add new fields or modify recipients and subject lines to simulate different datasets.

## Contributing

PRs welcome. Please keep changes focused (templates, additional output formats, or improved CLI options).

## Ollama integration

If you want to use a local LLM via Ollama to generate email bodies or templates, follow these simple steps.

- Install Ollama for your OS (see the official docs at https://ollama.com/docs).
- Pull a model you want to use, for example:

```bash
ollama pull llama2
```

- Quick CLI test — generate a short email using the model:

```bash
ollama run llama2 --prompt "Write a short professional email introducing a new product, ~100 words"
```

- Python example (calls the `ollama` CLI and captures output). This is a minimal approach that requires no additional HTTP client:

```python
import subprocess

model = "llama2"
prompt = "Write a short professional email introducing a new product, ~100 words"

result = subprocess.run(["ollama", "run", model, "--prompt", prompt], capture_output=True, text=True)
print(result.stdout)
```

- Integration tip: call the CLI or subprocess from your generator scripts to fetch model-generated bodies, then insert them into your JSON templates before saving to `emails/`.

Notes:
- Running `ollama run` requires a pulled model and sufficient local resources. If you prefer a server-based flow, consult Ollama docs for serving or HTTP API options.

## Notes

- This repo contains small utilities intended for synthetic data creation and experimentation. If you integrate LLMs (e.g., via [ollama_test.py](ollama_test.py)), ensure any API keys or credentials are kept out of the repo and loaded via environment variables or a config file.

---
Generated with simple Python scripts. If you want, I can add CLI options, README badges, or a small demo notebook next.

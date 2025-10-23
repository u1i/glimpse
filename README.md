# Glimpse

A command-line tool for analyzing images using OpenRouter API with multimodal models.

3G-CLI Suite: [Glean](https://github.com/u1i/glean) (text analysis) | [Glimpse](https://github.com/u1i/glimpse) (image analysis) | [Graft](https://github.com/u1i/graft) (image generation and editing)

## Installation

1. Clone this repository
2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

Create a `~/.glimpse_cfg` file in your home directory with the following format:

```ini
[openrouter]
# Required setting
api_key = your_api_key_here

# Optional settings (defaults shown)
model = google/gemini-2.5-flash
temperature = 0.4  # Controls randomness (0.0 to 1.0, lower is more deterministic)
```

Only the API key is mandatory. If model or temperature are not specified, default values will be used.

## Usage

```
./glimpse.py path/to/image.jpg
```

With a custom prompt:
```
./glimpse.py path/to/image.png --prompt "Identify all objects in this image"
```

Override the model (instead of using the one from .env):
```
./glimpse.py path/to/image.jpg --model mistralai/mistral-medium-3
```

Override the temperature setting:
```
./glimpse.py path/to/image.jpg --temperature 0.8
```

Combining options:
```
./glimpse.py path/to/image.jpg -m openai/o4-mini -t 0.2 -p "What brand is this?"
```

Or using the short form:
```
./glimpse.py path/to/image.jpg -p "What's happening in this scene?"
```

## Supported Image Formats

- JPEG/JPG
- PNG

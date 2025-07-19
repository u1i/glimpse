# Glimpse

A command-line tool for analyzing images using OpenRouter API with multimodal models.

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

Create a `.env` file in the project root with the following variables:

```
# Required settings
OPENROUTER_LLM=google/gemini-2.5-flash
OPENROUTER_API_KEY=your_api_key_here

# Optional settings
OPENROUTER_TEMPERATURE=0.4  # Controls randomness (0.0 to 1.0, lower is more deterministic)
```

## Usage

```
./glimpse.py path/to/image.jpg
```

With a custom prompt:
```
./glimpse.py path/to/image.png --prompt "Identify all objects in this image"
```

Or using the short form:
```
./glimpse.py path/to/image.jpg -p "What's happening in this scene?"
```

## Supported Image Formats

- JPEG/JPG
- PNG

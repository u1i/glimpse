#!/usr/bin/env python3
"""
Glimpse - A command-line tool for image analysis using OpenRouter API.
"""

import os
import sys
import base64
import json
import argparse
import configparser
from pathlib import Path
from typing import Optional

import requests
from PIL import Image


def load_config():
    """Load configuration from $HOME/.glimpse_cfg file."""
    config_path = os.path.expanduser("~/.glimpse_cfg")
    config = configparser.ConfigParser()
    
    # Default values
    default_model = "google/gemini-2.5-flash"
    default_temperature = 0.4
    
    # Config file existence is already checked in main()
    try:
        config.read(config_path)
        
        # Get API key (required)
        if 'openrouter' in config and 'api_key' in config['openrouter']:
            api_key = config['openrouter']['api_key']
        else:
            print("Error: Missing 'api_key' in [openrouter] section of config file.", file=sys.stderr)
            print("Please add your OpenRouter API key to ~/.glimpse_cfg", file=sys.stderr)
            sys.exit(1)
            
        # Get model (optional, use default if not specified)
        if 'openrouter' in config and 'model' in config['openrouter']:
            model = config['openrouter']['model']
        else:
            model = default_model
            print(f"Notice: Using default model: {default_model}", file=sys.stderr)
        
        # Get temperature (optional, use default if not specified)
        if 'openrouter' in config and 'temperature' in config['openrouter']:
            try:
                temperature = float(config['openrouter']['temperature'])
            except ValueError:
                print(f"Warning: Invalid temperature value in config. Using default: {default_temperature}", file=sys.stderr)
                temperature = default_temperature
        else:
            temperature = default_temperature
            
    except Exception as e:
        print(f"Error reading config file: {e}", file=sys.stderr)
        print("Please ensure the file has the correct format:", file=sys.stderr)
        print("[openrouter]\napi_key = your_api_key_here", file=sys.stderr)
        sys.exit(1)
        
    return api_key, model, temperature


def encode_image(image_path):
    """Encode image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_image(image_path: str, prompt: str, api_key: str, model: str, temperature: Optional[float] = None) -> str:
    """Send image to OpenRouter API and get the analysis."""
    base64_image = encode_image(image_path)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
    }
    
    # Add temperature to payload if provided
    if temperature is not None:
        payload["temperature"] = temperature
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenRouter API: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response:
            print(f"Response status code: {e.response.status_code}", file=sys.stderr)
            print(f"Response body: {e.response.text}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to handle command line arguments and process the image."""
    # Check if config file exists before parsing arguments
    config_path = os.path.expanduser("~/.glimpse_cfg")
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}", file=sys.stderr)
        print("\nPlease create a config file with your OpenRouter API key:", file=sys.stderr)
        print("\n[openrouter]\napi_key = your_api_key_here\n", file=sys.stderr)
        print("Optional settings:\nmodel = google/gemini-2.5-flash\ntemperature = 0.4\n", file=sys.stderr)
        print("Run 'glimpse.py --help' for more information on command-line options.", file=sys.stderr)
        sys.exit(1)
        
    parser = argparse.ArgumentParser(description="Analyze images using OpenRouter API.")
    parser.add_argument(
        "image_path", 
        type=str, 
        help="Path to the image file (JPG or PNG)"
    )
    parser.add_argument(
        "--prompt", 
        "-p", 
        type=str, 
        default="Describe what you see in the image",
        help="Prompt to send with the image (default: 'Describe what you see in the image')"
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        help="Override the default model specified in config (e.g., 'mistralai/mistral-medium-3', 'openai/o4-mini')"
    )
    parser.add_argument(
        "--temperature",
        "-t",
        type=float,
        help="Override the temperature value from config (0.0 to 1.0, lower is more deterministic)"
    )
    
    args = parser.parse_args()
    
    # Validate image path
    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"Error: Image file not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)
    
    # Check file extension
    if image_path.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
        print(f"Error: Unsupported image format. Please use JPG or PNG.", file=sys.stderr)
        sys.exit(1)
    
    # Load configuration
    api_key, config_model, config_temperature = load_config()
    
    # Use command-line model if provided, otherwise use the one from config
    model = args.model if args.model else config_model
    
    # Use command-line temperature if provided, otherwise use the one from config
    temperature = args.temperature if args.temperature is not None else config_temperature
    
    # Analyze the image (silently)
    result = analyze_image(args.image_path, args.prompt, api_key, model, temperature)
    
    # Output only the result to stdout
    print(result)


if __name__ == "__main__":
    main()

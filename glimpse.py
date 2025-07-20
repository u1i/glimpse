#!/usr/bin/env python3
"""
Glimpse - A command-line tool for image analysis using OpenRouter API.
"""

import os
import sys
import base64
import json
import argparse
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from PIL import Image


def load_env_variables():
    """Load environment variables from .env file."""
    load_dotenv()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_LLM")
    temperature = os.getenv("OPENROUTER_TEMPERATURE")
    
    if not api_key or not model:
        print("Error: Missing required environment variables in .env file.", file=sys.stderr)
        print("Please ensure OPENROUTER_API_KEY and OPENROUTER_LLM are set.", file=sys.stderr)
        sys.exit(1)
    
    # Convert temperature to float if provided, otherwise use default
    if temperature is not None:
        try:
            temperature = float(temperature)
        except ValueError:
            print(f"Warning: Invalid OPENROUTER_TEMPERATURE value: {temperature}. Using default.", file=sys.stderr)
            temperature = None
    
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
        help="Override the default model specified in .env (e.g., 'mistralai/mistral-medium-3', 'openai/o4-mini')"
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
    
    # Load environment variables
    api_key, env_model, temperature = load_env_variables()
    
    # Use command-line model if provided, otherwise use the one from .env
    model = args.model if args.model else env_model
    
    # Analyze the image (silently)
    result = analyze_image(args.image_path, args.prompt, api_key, model, temperature)
    
    # Output only the result to stdout
    print(result)


if __name__ == "__main__":
    main()

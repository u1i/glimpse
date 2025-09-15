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
import time
import tempfile
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
        "Content-Type": "application/json",
        "X-Title": "glimpse",
        "HTTP-Referer": "https://github.com/u1i/glimpse"
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


def get_cache_file_path():
    """Get the path for the models cache file."""
    return os.path.join(tempfile.gettempdir(), 'glimpse_models_cache.json')


def is_cache_valid(cache_file_path, max_age_hours=6):
    """Check if the cache file exists and is not older than max_age_hours."""
    if not os.path.exists(cache_file_path):
        return False
    
    file_age = time.time() - os.path.getmtime(cache_file_path)
    max_age_seconds = max_age_hours * 3600
    return file_age < max_age_seconds


def load_models_from_cache(cache_file_path):
    """Load models data from cache file."""
    try:
        with open(cache_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_models_to_cache(models_data, cache_file_path):
    """Save models data to cache file."""
    try:
        with open(cache_file_path, 'w', encoding='utf-8') as f:
            json.dump(models_data, f)
    except IOError:
        # If we can't write to cache, just continue without caching
        pass


def fetch_models_data():
    """Fetch models data from API or cache."""
    cache_file_path = get_cache_file_path()
    
    # Try to load from cache first
    if is_cache_valid(cache_file_path):
        cached_data = load_models_from_cache(cache_file_path)
        if cached_data is not None:
            return cached_data
    
    # Cache miss or invalid - fetch from API
    try:
        response = requests.get("https://openrouter.ai/api/v1/models")
        response.raise_for_status()
        
        models_data = response.json()
        
        # Save to cache
        save_models_to_cache(models_data, cache_file_path)
        
        return models_data
        
    except requests.exceptions.RequestException as e:
        # If API fails, try to load from cache even if expired
        cached_data = load_models_from_cache(cache_file_path)
        if cached_data is not None:
            print(f"Warning: API request failed, using cached data: {e}", file=sys.stderr)
            return cached_data
        else:
            raise e


def list_models(detailed=True):
    """List all available OpenRouter models that support image input."""
    try:
        models_data = fetch_models_data()
        
        if 'data' in models_data:
            models = models_data['data']
        else:
            models = models_data  # Fallback if response format is different
        
        # Filter models that support image input
        image_models = []
        for model in models:
            architecture = model.get('architecture', {})
            modalities = architecture.get('input_modalities', [])
            if 'image' in modalities:
                image_models.append(model)
        
        if detailed:
            print(f"Available OpenRouter Models with Image Support ({len(image_models)} total):")
            print("=" * 70)
            
            for model in image_models:
                model_id = model.get('id', 'Unknown')
                name = model.get('name', 'Unknown')
                context_length = model.get('context_length', 'Unknown')
                
                # Get pricing info
                pricing = model.get('pricing', {})
                prompt_price = pricing.get('prompt', '0')
                completion_price = pricing.get('completion', '0')
                
                # Format pricing (convert to more readable format)
                try:
                    prompt_cost = f"${float(prompt_price) * 1000:.4f}/1K"
                    completion_cost = f"${float(completion_price) * 1000:.4f}/1K"
                except (ValueError, TypeError):
                    prompt_cost = "N/A"
                    completion_cost = "N/A"
                
                print(f"ID: {model_id}")
                print(f"Name: {name}")
                print(f"Context: {context_length} tokens")
                print(f"Pricing: {prompt_cost} prompt, {completion_cost} completion")
                
                # Add description if available and not too long
                description = model.get('description', '')
                if description and len(description) <= 100:
                    print(f"Description: {description}")
                elif description:
                    print(f"Description: {description[:97]}...")
                
                print("-" * 70)
        else:
            # Simple list of model IDs only
            print(f"Available OpenRouter Models with Image Support ({len(image_models)} total):")
            for model in image_models:
                model_id = model.get('id', 'Unknown')
                print(model_id)
            
    except Exception as e:
        print(f"Error fetching models: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to handle command line arguments and process the image."""
    parser = argparse.ArgumentParser(description="Analyze images using OpenRouter API.")
    parser.add_argument(
        "image_path", 
        nargs='?',
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
    parser.add_argument(
        "--list-models", 
        action='store_true', 
        help="List all available OpenRouter models with image support"
    )
    parser.add_argument(
        "--list-models-with-details", 
        action='store_true', 
        help="List all available OpenRouter models with image support and detailed information"
    )
    
    args = parser.parse_args()
    
    # Handle --list-models commands
    if args.list_models:
        list_models(detailed=False)
        sys.exit(0)
    
    if args.list_models_with_details:
        list_models(detailed=True)
        sys.exit(0)
    
    # Check if image_path is provided for analysis
    if not args.image_path:
        print("Error: Image path is required for analysis.", file=sys.stderr)
        print("Use --help for usage information or --list-models to see available models.", file=sys.stderr)
        sys.exit(1)
    
    # Check if config file exists
    config_path = os.path.expanduser("~/.glimpse_cfg")
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}", file=sys.stderr)
        print("\nPlease create a config file with your OpenRouter API key:", file=sys.stderr)
        print("\n[openrouter]\napi_key = your_api_key_here\n", file=sys.stderr)
        print("Optional settings:\nmodel = google/gemini-2.5-flash\ntemperature = 0.4\n", file=sys.stderr)
        print("Run 'glimpse.py --help' for more information on command-line options.", file=sys.stderr)
        sys.exit(1)
    
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

#!/usr/bin/env python3
"""
Simple Hello World with LiteLLM
Uses cost-effective models like gpt-4o-mini
"""

from litellm import completion
import litellm
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Disable debug for cleaner output
# litellm.set_verbose = True

def main():
    # Load configuration from .env file
    api_key = os.getenv("LITELLM_PROXY_API_KEY")
    api_base = os.getenv("LITELLM_PROXY_API_BASE")
    key_alias = os.getenv("KEY_ALIAS")
    
    if not api_key or not api_base:
        print("Error: Required environment variables not found in .env file")
        print("Make sure you have LITELLM_PROXY_API_KEY and LITELLM_PROXY_API_BASE configured")
        return
    
    print(f"Using key alias: {key_alias}")
    print(f"Connecting to: {api_base}")
    
    try:
        print("Connecting to Thomson Reuters proxy...")
        
        # Example with GPT-4o-mini using internal proxy
        response = completion(
            model="openai/gpt-4o-mini",  # Proxy format for OpenAI
            messages=[
                {"role": "user", "content": "Say 'Hello World' in Portuguese"}
            ],
            api_base=api_base,
            api_key=api_key
        )
        
        print("Model response:")
        print(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPossible solutions:")
        
        if "Authentication Error" in str(e) or "Virtual Key expected" in str(e):
            print("1. You need a virtual API key starting with 'sk-'")
            print("2. Contact your administrator to obtain a virtual key")
            print("3. The email alias alone is not sufficient for authentication")
        else:
            print("1. Check network connectivity")
            print("2. Verify that the model is available")
            print("3. Review proxy configuration")

if __name__ == "__main__":
    main()
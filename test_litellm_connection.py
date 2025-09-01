#!/usr/bin/env python3
"""
Test LiteLLM connection independently
"""

import sys
sys.path.insert(0, 'src')

import asyncio
from windvoice.core.config import LiteLLMConfig
from windvoice.services.transcription import TranscriptionService
from windvoice.utils.logging import setup_logging

async def test_litellm_connection():
    """Test LiteLLM connection with example credentials"""
    
    print("=== LiteLLM Connection Test ===\n")
    
    # Setup logging
    logger = setup_logging("DEBUG", False)  # Console only
    
    # Example configuration - replace with your actual credentials
    print("Please enter your LiteLLM credentials:")
    api_base = input("API Base URL: ").strip() or "https://your-proxy.com"
    api_key = input("API Key: ").strip() or "sk-your-key-here"
    key_alias = input("Key Alias: ").strip() or "your-username"
    
    config = LiteLLMConfig(
        api_base=api_base,
        api_key=api_key,
        key_alias=key_alias,
        model="whisper-1"
    )
    
    print(f"\n🔍 Testing Connection...")
    print(f"API Base: {config.api_base}")
    print(f"Key Alias: {config.key_alias}")
    print(f"API Key: {config.api_key[:10]}...{config.api_key[-4:] if len(config.api_key) > 14 else '[REDACTED]'}")
    print("-" * 60)
    
    service = TranscriptionService(config)
    
    try:
        success, message = await service.test_connection()
        
        print(f"\n📊 FINAL RESULT:")
        if success:
            print(f"✅ SUCCESS: {message}")
        else:
            print(f"❌ FAILED: {message}")
            
        print(f"\n💡 What this means:")
        if success:
            print("  - Your LiteLLM credentials are correct")
            print("  - The API endpoint is reachable")
            print("  - WindVoice should be able to transcribe audio")
        else:
            print("  - Check your credentials and API endpoint")
            print("  - Make sure the LiteLLM proxy is running")
            print("  - Verify network connectivity")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        
    finally:
        await service.close()
        print("\n" + "="*60)
        print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_litellm_connection())
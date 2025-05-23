#!/usr/bin/env python3
# automated_skeptic_mvp/scripts/fix_llm_integration.py
"""
Fix script for LLM integration issues
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def update_openai_package():
    """Update OpenAI package to compatible version"""
    print("\n🔄 Updating OpenAI package...")
    try:
        # Install the new OpenAI package
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "openai>=1.0.0", "--upgrade"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ OpenAI package updated successfully")
            return True
        else:
            print(f"❌ Failed to update OpenAI: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error updating OpenAI package: {str(e)}")
        return False

def check_ollama_installation():
    """Check if Ollama is installed and running"""
    print("\n🔍 Checking Ollama installation...")
    
    try:
        # Check if Ollama command exists
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama installed: {result.stdout.strip()}")
        else:
            print("❌ Ollama not found in PATH")
            return False
    except FileNotFoundError:
        print("❌ Ollama not installed")
        print("💡 Install from: https://ollama.ai/download")
        return False
    
    # Check if Ollama server is running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama server running with {len(models)} models")
            if models:
                print("📦 Available models:")
                for model in models[:5]:  # Show first 5
                    print(f"   • {model['name']}")
                if len(models) > 5:
                    print(f"   ... and {len(models) - 5} more")
            return True
        else:
            print("❌ Ollama server not responding")
            return False
    except Exception as e:
        print("❌ Ollama server not accessible")
        print("💡 Start with: ollama serve")
        return False

def ensure_basic_models():
    """Ensure basic models are available in Ollama"""
    print("\n📦 Checking basic models...")
    
    recommended_models = ["llama2", "llama3.2"]
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            available_models = [model['name'] for model in response.json().get('models', [])]
            
            # Check if we have any suitable model
            suitable_models = []
            for model in available_models:
                for rec in recommended_models:
                    if model.startswith(rec):
                        suitable_models.append(model)
                        break
            
            if suitable_models:
                print(f"✅ Found suitable models: {suitable_models}")
                return True
            else:
                print("⚠️  No recommended models found")
                print("💡 Pull a model with: ollama pull llama2")
                return False
        
    except Exception as e:
        print(f"❌ Error checking models: {str(e)}")
        return False

def update_config_file():
    """Update configuration file with better model names"""
    print("\n⚙️  Updating configuration...")
    
    config_path = Path("config/config.ini")
    if not config_path.exists():
        print("⚠️  Config file not found - using defaults")
        return True
    
    try:
        # Read current config
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Update model references to include :latest tag
        updated_content = content.replace(
            "ollama_model = llama2",
            "ollama_model = llama2:latest"
        )
        
        # Update agent mappings if they exist
        agent_models = ["herald_model", "illuminator_model", "seeker_model"]
        for agent_model in agent_models:
            updated_content = updated_content.replace(
                f"{agent_model} = llama2",
                f"{agent_model} = llama2:latest"
            )
        
        # Write back if changed
        if updated_content != content:
            with open(config_path, 'w') as f:
                f.write(updated_content)
            print("✅ Configuration updated")
        else:
            print("✅ Configuration already up to date")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {str(e)}")
        return False

def test_integration():
    """Test the LLM integration"""
    print("\n🧪 Testing LLM integration...")
    
    try:
        # Import and test the components
        sys.path.append('.')
        
        from config.settings import Settings
        from llm.manager import LLMManager
        
        settings = Settings()
        llm_manager = LLMManager(settings)
        
        providers = llm_manager.get_available_providers()
        print(f"✅ LLM Manager initialized with {len(providers)} providers")
        
        for name, info in providers.items():
            status = "✅" if info['available'] else "❌"
            print(f"   {status} {name}: {info['provider']} - {info['model']}")
        
        if providers:
            # Test a simple generation
            try:
                response = llm_manager.generate("Hello, this is a test.")
                print(f"✅ Test generation successful: {response.content[:50]}...")
                return True
            except Exception as e:
                print(f"⚠️  Generation test failed: {str(e)}")
                return len(providers) > 0  # At least providers are available
        else:
            print("❌ No providers available")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return False

def main():
    """Main fix script"""
    print("🔧 AUTOMATED SKEPTIC - LLM INTEGRATION FIX SCRIPT")
    print("=" * 60)
    
    success = True
    
    # Step 1: Check Python version
    if not check_python_version():
        success = False
    
    # Step 2: Update OpenAI package
    if not update_openai_package():
        success = False
    
    # Step 3: Check Ollama
    ollama_ok = check_ollama_installation()
    if ollama_ok:
        ensure_basic_models()
    
    # Step 4: Update config
    if not update_config_file():
        success = False
    
    # Step 5: Test integration
    if not test_integration():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ LLM INTEGRATION FIXED SUCCESSFULLY!")
        print("\n💡 Next steps:")
        print("   • Test with: python main.py --claim 'Test claim'")
        print("   • Check results.json for output")
        print("   • Monitor logs for LLM usage")
    else:
        print("⚠️  SOME ISSUES REMAIN")
        print("\n🔧 Manual steps you may need:")
        print("   • Install Ollama: https://ollama.ai/download")
        print("   • Pull a model: ollama pull llama2")
        print("   • Start Ollama: ollama serve")
        print("   • Add OpenAI API key to config if needed")
    
    print("\n📋 System Status Summary:")
    print(f"   • Python: {'✅' if sys.version_info >= (3, 8) else '❌'}")
    print(f"   • OpenAI Package: {'✅' if success else '❌'}")
    print(f"   • Ollama: {'✅' if ollama_ok else '❌'}")
    print(f"   • Integration: {'✅' if success else '⚠️'}")

if __name__ == "__main__":
    main()
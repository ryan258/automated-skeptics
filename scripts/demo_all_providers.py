#!/usr/bin/env python3
# automated_skeptic_mvp/scripts/demo_all_providers.py
"""
Demo script to test all LLM providers with the same prompt
"""

import time
import sys
from pathlib import Path

def test_all_providers():
    """Test all available LLM providers"""
    
    print("🚀 MULTI-PROVIDER LLM DEMONSTRATION")
    print("Testing OpenAI + Claude + Gemini + Ollama")
    print("=" * 60)
    
    try:
        sys.path.append('.')
        
        from config.settings import Settings
        from llm.manager import LLMManager
        from llm.base import LLMMessage
        
        # Initialize
        settings = Settings()
        llm_manager = LLMManager(settings)
        
        # Get available providers
        providers = llm_manager.get_available_providers()
        print(f"\\n📋 Available Providers ({len(providers)}):")
        
        for name, info in providers.items():
            status = "✅" if info['available'] else "❌"
            provider_type = info['provider'].upper()
            model = info['model']
            print(f"   {status} {name}: {provider_type} - {model}")
        
        if not providers:
            print("❌ No providers available!")
            print("💡 Make sure to:")
            print("   • Add API keys to config.ini")
            print("   • Install provider packages")
            print("   • Start Ollama if using local models")
            return
        
        # Test prompt
        test_prompt = "Explain what fact-checking is in exactly one sentence."
        
        print(f"\\n🧪 Test Prompt: '{test_prompt}'")
        print("=" * 60)
        
        # Test each provider
        results = {}
        
        for provider_name, provider_info in providers.items():
            if not provider_info['available']:
                continue
                
            try:
                print(f"\\n🔄 Testing {provider_name}...")
                start_time = time.time()
                
                # Create message
                message = LLMMessage(role="user", content=test_prompt)
                
                # Generate response
                response = llm_manager.generate(
                    [message],
                    provider_name=provider_name,
                    temperature=0.1,
                    max_tokens=100
                )
                
                elapsed = time.time() - start_time
                
                # Store results
                results[provider_name] = {
                    'response': response.content,
                    'time': elapsed,
                    'provider': response.provider.value,
                    'model': response.model,
                    'usage': response.usage
                }
                
                print(f"✅ Success! ({elapsed:.2f}s)")
                print(f"📝 Response: {response.content[:150]}...")
                
                if response.usage:
                    tokens = response.usage.get('total_tokens', 'unknown')
                    cost = response.usage.get('estimated_cost', 0)
                    print(f"📊 Usage: {tokens} tokens, ${cost:.4f}")
                
            except Exception as e:
                print(f"❌ Failed: {str(e)}")
                results[provider_name] = {'error': str(e)}
        
        # Summary comparison
        print("\\n" + "=" * 60)
        print("📊 PROVIDER COMPARISON SUMMARY")
        print("=" * 60)
        
        successful_results = {k: v for k, v in results.items() if 'error' not in v}
        
        if successful_results:
            print(f"\\n✅ {len(successful_results)} providers working successfully\\n")
            
            # Speed comparison
            print("⚡ Speed Ranking:")
            speed_ranking = sorted(successful_results.items(), key=lambda x: x[1]['time'])
            for i, (name, data) in enumerate(speed_ranking, 1):
                print(f"   {i}. {name}: {data['time']:.2f}s")
            
            # Cost comparison (if available)
            cost_data = {k: v for k, v in successful_results.items() 
                        if v.get('usage', {}).get('estimated_cost', 0) > 0}
            
            if cost_data:
                print("\\n💰 Cost Ranking (per request):")
                cost_ranking = sorted(cost_data.items(), 
                                    key=lambda x: x[1]['usage']['estimated_cost'])
                for i, (name, data) in enumerate(cost_ranking, 1):
                    cost = data['usage']['estimated_cost']
                    print(f"   {i}. {name}: ${cost:.4f}")
            
            # Model info
            print("\\n🤖 Models Used:")
            for name, data in successful_results.items():
                provider_type = data['provider'].upper()
                model = data['model']
                print(f"   • {name}: {provider_type} - {model}")
        
        error_results = {k: v for k, v in results.items() if 'error' in v}
        if error_results:
            print(f"\\n❌ {len(error_results)} providers had errors:")
            for name, data in error_results.items():
                print(f"   • {name}: {data['error']}")
        
        # Recommendations
        print("\\n" + "=" * 60)
        print("💡 RECOMMENDATIONS")
        print("=" * 60)
        
        if successful_results:
            fastest = min(successful_results.items(), key=lambda x: x[1]['time'])
            print(f"🏃 Fastest: {fastest[0]} ({fastest[1]['time']:.2f}s)")
            
            if cost_data:
                cheapest = min(cost_data.items(), 
                             key=lambda x: x[1]['usage']['estimated_cost'])
                print(f"💸 Cheapest: {cheapest[0]} (${cheapest[1]['usage']['estimated_cost']:.4f})")
            
            # Get free options
            free_options = [name for name, data in successful_results.items() 
                          if data.get('usage', {}).get('estimated_cost', 0) == 0]
            if free_options:
                print(f"🆓 Free: {', '.join(free_options)}")
        
        print("\\n🎯 Optimal Strategy:")
        print("   • Use Ollama for development (free, private)")
        print("   • Use Claude for complex reasoning (best quality)")
        print("   • Use Gemini for fast inference (good balance)")
        print("   • Use OpenAI as reliable fallback")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        print("\\n🔧 Troubleshooting:")
        print("   • Ensure config.ini has your API keys")
        print("   • Check if all packages are installed")
        print("   • Verify Ollama is running (if using local models)")

def test_fact_checking_workflow():
    """Test the providers in a fact-checking context"""
    
    print("\\n" + "=" * 60)
    print("🔍 FACT-CHECKING WORKFLOW TEST")
    print("=" * 60)
    
    try:
        sys.path.append('.')
        
        from config.settings import Settings
        from llm.manager import LLMManager
        from llm.base import LLMMessage
        
        settings = Settings()
        llm_manager = LLMManager(settings)
        
        # Different tasks for different providers
        tasks = [
            {
                'agent': 'herald',
                'task': 'Input Processing',
                'prompt': 'Clean and validate this claim: "The Berlin Wall fell in 1989."'
            },
            {
                'agent': 'illuminator', 
                'task': 'Context Analysis',
                'prompt': 'Classify this claim type: "The Berlin Wall fell in 1989."'
            },
            {
                'agent': 'logician',
                'task': 'Claim Deconstruction',
                'prompt': 'Break down this claim into verifiable parts: "The Berlin Wall fell in 1989."'
            },
            {
                'agent': 'oracle',
                'task': 'Evidence Analysis',
                'prompt': 'Analyze if this evidence supports the claim: "The Berlin Wall fell on November 9, 1989..."'
            }
        ]
        
        print("\\n🎭 Testing agent-specific models:")
        
        for task in tasks:
            agent_name = task['agent']
            task_name = task['task']
            prompt = task['prompt']
            
            try:
                provider_name = llm_manager.get_provider_for_agent(agent_name)
                if provider_name:
                    providers = llm_manager.get_available_providers()
                    provider_info = providers.get(provider_name, {})
                    model = provider_info.get('model', 'unknown')
                    
                    print(f"\\n🎯 {task_name} ({agent_name}):")
                    print(f"   Model: {model}")
                    print(f"   Task: {prompt[:50]}...")
                    
                    start_time = time.time()
                    response = llm_manager.generate(
                        prompt,
                        agent_name=agent_name,
                        max_tokens=150
                    )
                    elapsed = time.time() - start_time
                    
                    print(f"   ✅ Response ({elapsed:.2f}s): {response.content[:100]}...")
                else:
                    print(f"\\n❌ {task_name}: No provider assigned")
                    
            except Exception as e:
                print(f"\\n❌ {task_name}: Error - {str(e)}")
    
    except Exception as e:
        print(f"❌ Workflow test failed: {str(e)}")

def main():
    """Main demo function"""
    test_all_providers()
    test_fact_checking_workflow()
    
    print("\\n" + "=" * 60)
    print("🎉 MULTI-PROVIDER DEMO COMPLETE!")
    print("=" * 60)
    
    print("\\n🚀 Ready to run full fact-checking with multiple models:")
    print("   python main.py --claim 'The Berlin Wall fell in 1989.'")

if __name__ == "__main__":
    main()
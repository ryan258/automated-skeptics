# automated_skeptic_mvp/examples/mixed_llm_demo.py
"""
Demonstration of mixed local and external LLM usage
"""

import logging
import time
from typing import Dict, Any
from config.settings import Settings
from llm.manager import LLMManager
from llm.base import LLMMessage
from data.models import Claim
from agents.logician_agent import LogicianAgent

def setup_demo_logging():
    """Setup detailed logging for the demo"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def demonstrate_provider_capabilities(llm_manager: LLMManager):
    """Demonstrate different LLM providers"""
    print("=" * 60)
    print("🤖 LLM PROVIDER DEMONSTRATION")
    print("=" * 60)
    
    # Show available providers
    providers = llm_manager.get_available_providers()
    print(f"\n📋 Available Providers ({len(providers)}):")
    for name, info in providers.items():
        status = "✅ Available" if info['available'] else "❌ Unavailable"
        print(f"  • {name}: {info['provider']} - {info['model']} ({status})")
    
    # Test message for comparison
    test_message = "Explain what fact-checking is in one sentence."
    
    print(f"\n🧪 Test Query: '{test_message}'")
    print("-" * 60)
    
    # Test each available provider
    for provider_name in providers.keys():
        if providers[provider_name]['available']:
            try:
                print(f"\n🔄 Testing {provider_name}...")
                start_time = time.time()
                
                response = llm_manager.generate(
                    test_message,
                    provider_name=provider_name,
                    temperature=0.1,
                    max_tokens=100
                )
                
                elapsed = time.time() - start_time
                
                print(f"✅ Provider: {response.provider.value}")
                print(f"📦 Model: {response.model}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                print(f"🎯 Response: {response.content[:200]}...")
                
                if response.usage:
                    tokens = response.usage.get('total_tokens', 'unknown')
                    cost = response.usage.get('estimated_cost', 0)
                    print(f"📊 Usage: {tokens} tokens, ${cost:.4f}")
                
            except Exception as e:
                print(f"❌ Error with {provider_name}: {str(e)}")

def demonstrate_agent_llm_mapping(settings: Settings):
    """Show how different agents use different LLMs"""
    print("\n" + "=" * 60)
    print("🎭 AGENT LLM MAPPING DEMONSTRATION")
    print("=" * 60)
    
    llm_manager = LLMManager(settings)
    
    agents = ['herald', 'illuminator', 'logician', 'seeker', 'oracle']
    
    print("\n📍 Agent-to-LLM Assignments:")
    for agent in agents:
        provider = llm_manager.get_provider_for_agent(agent)
        if provider:
            provider_info = llm_manager.get_available_providers().get(provider, {})
            model = provider_info.get('model', 'unknown')
            provider_type = provider_info.get('provider', 'unknown')
            status = "🟢" if provider_info.get('available', False) else "🔴"
            
            print(f"  {status} {agent.title()} Agent → {provider} ({provider_type}: {model})")
        else:
            print(f"  🔴 {agent.title()} Agent → No provider assigned")

def demonstrate_cost_optimization(llm_manager: LLMManager):
    """Show cost implications of different provider choices"""
    print("\n" + "=" * 60)
    print("💰 COST OPTIMIZATION DEMONSTRATION")
    print("=" * 60)
    
    sample_claims = [
        "The Berlin Wall fell in 1989.",
        "Apple was founded in 1976.",
        "Einstein was born in Germany.",
        "The COVID-19 pandemic began in 2019.",
        "Microsoft was founded by Bill Gates and Paul Allen."
    ]
    
    print(f"\n📊 Cost Estimation for {len(sample_claims)} sample claims:")
    
    total_local_cost = 0
    total_external_cost = 0
    
    for i, claim in enumerate(sample_claims, 1):
        # Estimate cost for local vs external processing
        local_cost = llm_manager.estimate_cost(claim, 'ollama_default')
        external_cost = llm_manager.estimate_cost(claim, 'openai_default')
        
        total_local_cost += local_cost
        total_external_cost += external_cost
        
        print(f"  {i}. {claim}")
        print(f"     Local (Ollama): ${local_cost:.4f}")
        print(f"     External (OpenAI): ${external_cost:.4f}")
    
    print(f"\n💵 Total Estimated Costs:")
    print(f"  • Local Processing: ${total_local_cost:.4f}")
    print(f"  • External Processing: ${total_external_cost:.4f}")
    print(f"  • Potential Savings: ${total_external_cost - total_local_cost:.4f} ({((total_external_cost - total_local_cost) / max(total_external_cost, 0.001) * 100):.1f}%)")

def demonstrate_fallback_behavior(llm_manager: LLMManager):
    """Demonstrate fallback behavior when providers fail"""
    print("\n" + "=" * 60)
    print("🔄 FALLBACK BEHAVIOR DEMONSTRATION")
    print("=" * 60)
    
    print("\n🎯 Testing fallback logic:")
    print("  1. Attempting to use primary provider")
    print("  2. If primary fails, trying fallback")
    print("  3. Graceful degradation to rule-based processing")
    
    # Simulate different scenarios
    test_scenarios = [
        ("Normal operation", "logician", None),
        ("Specific provider request", None, "ollama_default"),
        ("Agent without specific mapping", "nonexistent_agent", None),
    ]
    
    for scenario_name, agent_name, provider_name in test_scenarios:
        print(f"\n🧪 Scenario: {scenario_name}")
        try:
            response = llm_manager.generate(
                "Break down this claim: The Earth revolves around the Sun.",
                agent_name=agent_name,
                provider_name=provider_name,
                max_tokens=100
            )
            print(f"  ✅ Success: Used {response.provider.value} ({response.model})")
        except Exception as e:
            print(f"  ❌ Failed: {str(e)}")

def demonstrate_real_claim_processing():
    """Show real claim processing with mixed LLM usage"""
    print("\n" + "=" * 60)
    print("🔬 REAL CLAIM PROCESSING DEMONSTRATION")
    print("=" * 60)
    
    # Initialize components
    settings = Settings()
    logician = LogicianAgent(settings)
    
    test_claim = Claim(text="Apple was founded by Steve Jobs and Steve Wozniak in 1976 in California.")
    
    print(f"\n🎯 Processing Claim: '{test_claim.text}'")
    
    # Show LLM configuration for the agent
    llm_info = logician.get_llm_info()
    print(f"\n⚙️  Logician Agent LLM Configuration:")
    print(f"  • Status: {llm_info['status']}")
    if llm_info['status'] == 'available':
        print(f"  • Assigned Provider: {llm_info['assigned_provider']}")
        provider_info = llm_info.get('provider_info', {})
        print(f"  • Model: {provider_info.get('model', 'unknown')}")
        print(f"  • Provider Type: {provider_info.get('provider', 'unknown')}")
    
    # Process the claim
    print(f"\n🔄 Processing...")
    start_time = time.time()
    
    try:
        processed_claim = logician.process(test_claim)
        elapsed = time.time() - start_time
        
        print(f"✅ Processing completed in {elapsed:.2f}s")
        print(f"\n📋 Results:")
        print(f"  • Original claim: {processed_claim.text}")
        print(f"  • Sub-claims identified: {len(processed_claim.sub_claims)}")
        
        for i, sub_claim in enumerate(processed_claim.sub_claims, 1):
            print(f"    {i}. {sub_claim.text}")
            if sub_claim.entities:
                entities = [e.text for e in sub_claim.entities]
                print(f"       Entities: {', '.join(entities)}")
        
    except Exception as e:
        print(f"❌ Processing failed: {str(e)}")

def main():
    """Main demonstration function"""
    setup_demo_logging()
    
    print("🚀 AUTOMATED SKEPTIC - MIXED LLM INTEGRATION DEMO")
    print("This demo showcases the flexible LLM integration system")
    
    try:
        # Load settings
        settings = Settings()
        llm_manager = LLMManager(settings)
        
        # Run demonstrations
        demonstrate_provider_capabilities(llm_manager)
        demonstrate_agent_llm_mapping(settings)
        demonstrate_cost_optimization(llm_manager)
        demonstrate_fallback_behavior(llm_manager)
        demonstrate_real_claim_processing()
        
        print("\n" + "=" * 60)
        print("✅ DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("\n💡 Key Takeaways:")
        print("  • Multiple LLM providers can coexist")
        print("  • Each agent can use a different LLM")
        print("  • Automatic fallback ensures reliability")
        print("  • Local models provide cost savings and privacy")
        print("  • External models offer enhanced capabilities")
        print("\n🎯 Next Steps:")
        print("  • Configure your preferred LLM mapping in config.ini")
        print("  • Install Ollama for local LLM support")
        print("  • Test with your own claims and requirements")
        print("  • Monitor costs and performance metrics")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("  • Ensure config.ini is properly configured")
        print("  • Check if Ollama is running (if using local models)")
        print("  • Verify API keys for external providers")
        print("  • Check network connectivity")

if __name__ == "__main__":
    main()
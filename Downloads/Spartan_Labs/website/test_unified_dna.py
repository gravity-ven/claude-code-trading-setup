#!/usr/bin/env python3
"""
Demonstrate the unified AI DNA working across Claude and Gemini
"""

import json
from ai_dna_bridge import AIDNABridge

def test_unified_dna():
    print("🧬 Testing Unified AI DNA Bridge")
    print("=" * 50)
    
    # Create bridge
    bridge = AIDNABridge()
    
    # Sample system status
    sample_status = {
        "timestamp": "2025-11-22T12:15:00",
        "containers": [
            {"name": "spartan-research-station", "state": "running"},
            {"name": "spartan-postgres", "state": "running"},
            {"name": "spartan-correlation-api", "state": "restarting"}
        ],
        "endpoints": [
            {"name": "Web Server", "status": "healthy"},
            {"name": "Correlation API", "status": "unhealthy"}
        ],
        "disk_memory": {
            "disk": "50% used",
            "memory": "75% used"
        },
        "recent_errors": [
            "Connection timeout in correlation API",
            "High memory usage warning"
        ]
    }
    
    print("📊 Sample System Status:")
    print(json.dumps(sample_status, indent=2))
    print()
    
    # Test Claude prompt
    print("🧠 Claude DNA Prompt Sample:")
    print("-" * 30)
    claude_prompt = bridge.get_claude_prompt_wrapper(
        json.dumps(sample_status, indent=2), 
        "ROUTINE_MONITORING"
    )
    print(claude_prompt[:500] + "...")
    print()
    
    # Test Gemini prompt  
    print("💎 Gemini DNA Prompt Sample:")
    print("-" * 30)
    gemini_prompt = bridge.get_gemini_prompt_wrapper(
        json.dumps(sample_status, indent=2), 
        "ROUTINE_MONITORING"
    )
    print(gemini_prompt[:500] + "...")
    print()
    
    # Show unified personality
    print("🤖 Unified AI Personality:")
    print("-" * 30)
    personality = bridge.get_unified_personality_prompt()
    print(personality[:300] + "...")
    print()
    
    # Display DNA profile
    print("🧬 DNA Profile Summary:")
    print("-" * 30)
    profile = bridge.dna_profile
    print(f"Name: {profile['name']}")
    print(f"Version: {profile['version']}")
    print(f"Core Concepts: {', '.join(profile['core_concepts'])}")
    print(f"Claude Compatibility: {'✅' if profile['claude_compatibility']['native_mode'] else '❌'}")
    print(f"Gemini Compatibility: {'✅' if profile['gemini_compatibility']['prompt_engineering'] else '❌'}")
    
    print("\n✅ Unified DNA Bridge Ready!")
    print("\🎯 Both AIs now share:")
    print("   • Same monitoring personality")
    print("   • Identical priority framework")  
    print("   • Compatible response formats")
    print("   • Coordinated analysis approach")

if __name__ == "__main__":
    test_unified_dna()

#!/usr/bin/env python3
"""
Test script for the Person OSINT Orchestrator
"""
import asyncio
import json
from orchestrator import PersonOSINTOrchestrator

async def test_orchestrator():
    """Test the orchestrator with sample data"""
    
    # Sample test data
    test_data = {
        "name": "Aman Paswan",
        "phone": "+918085234483",
        "context_info": "This person is very much interested in tech products and AI solutions."
    }
    
    print("🧪 Testing Person OSINT Orchestrator")
    print("=" * 50)
    print(f"Name: {test_data['name']}")
    print(f"Phone: {test_data['phone']}")
    print(f"Context: {test_data['context_info']}")
    print("=" * 50)
    
    try:
        orchestrator = PersonOSINTOrchestrator()
        
        result = await orchestrator.enrich_person(
            test_data["phone"],
            test_data["name"], 
            test_data["context_info"]
        )
        
        # Save test results
        with open("test_result.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("\n✅ Test completed successfully!")
        print("📁 Results saved to: test_result.json")
        
        # Display key results
        final_summary = result.get("final_summary", {})
        if final_summary:
            print(f"\n📊 Verification Status: {final_summary.get('verification_status')}")
            print(f"🎯 Confidence Score: {final_summary.get('confidence_score', 0.0):.2f}")
            
            # Show some key insights
            sales_intel = final_summary.get("sales_intelligence", {})
            if sales_intel.get("talking_points"):
                print(f"\n💡 Top Talking Points:")
                for i, point in enumerate(sales_intel["talking_points"][:3], 1):
                    print(f"   {i}. {point}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orchestrator())

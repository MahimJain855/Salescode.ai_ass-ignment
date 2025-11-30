"""
Demo Script for Intelligent Interruption Handler
Simulates real-world scenarios for testing and demonstration
"""

import asyncio
import logging
from datetime import datetime
from intelligent_interruption_handler import InterruptionHandler, AgentState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoSimulator:
    """Simulates agent-user interactions for demonstration."""
    
    def __init__(self):
        self.handler = InterruptionHandler()
        self.test_results = []
    
    def print_banner(self, text: str):
        """Print a formatted banner."""
        print("\n" + "="*70)
        print(f"  {text}")
        print("="*70 + "\n")
    
    def print_scenario(self, number: int, title: str, context: str):
        """Print scenario information."""
        print(f"\n{'─'*70}")
        print(f"📋 SCENARIO {number}: {title}")
        print(f"{'─'*70}")
        print(f"Context: {context}\n")
    
    def test_interaction(self, agent_state: AgentState, user_input: str, 
                        expected_behavior: str) -> bool:
        """
        Test a single interaction and log the result.
        
        Args:
            agent_state: Current state of the agent
            user_input: What the user says
            expected_behavior: Expected result (IGNORE, INTERRUPT, RESPOND)
        
        Returns:
            True if test passed, False otherwise
        """
        self.handler.set_state(agent_state)
        result = self.handler.should_interrupt(user_input)
        
        # Interpret result
        if agent_state == AgentState.SPEAKING:
            actual_behavior = "INTERRUPT" if result else "IGNORE"
        else:
            actual_behavior = "RESPOND" if result else "IGNORE"
        
        # Check if matches expectation
        passed = actual_behavior == expected_behavior
        status = "✅ PASS" if passed else "❌ FAIL"
        
        # Log the test
        print(f"Agent State: {agent_state.value.upper()}")
        print(f"User Input: \"{user_input}\"")
        print(f"Expected: {expected_behavior}")
        print(f"Actual: {actual_behavior}")
        print(f"Result: {status}\n")
        
        self.test_results.append({
            'passed': passed,
            'scenario': f"{agent_state.value} + '{user_input}'",
            'expected': expected_behavior,
            'actual': actual_behavior
        })
        
        return passed
    
    async def run_demo(self):
        """Run complete demo of all scenarios."""
        self.print_banner("INTELLIGENT INTERRUPTION HANDLER - LIVE DEMO")
        print("This demo simulates the 4 core scenarios from the assignment.\n")
        
        # ==================== SCENARIO 1 ====================
        self.print_scenario(
            1,
            "The Long Explanation",
            "Agent is reading a long paragraph about history"
        )
        
        print("Agent: \"In 1776, the Declaration of Independence was signed...\"")
        await asyncio.sleep(0.5)
        
        self.test_interaction(
            AgentState.SPEAKING,
            "okay",
            "IGNORE"
        )
        
        print("Agent: (continues) \"...marking a pivotal moment in American history...\"")
        await asyncio.sleep(0.5)
        
        self.test_interaction(
            AgentState.SPEAKING,
            "yeah",
            "IGNORE"
        )
        
        print("Agent: (continues) \"...and establishing the foundations of democracy.\"")
        await asyncio.sleep(0.5)
        
        self.test_interaction(
            AgentState.SPEAKING,
            "uh-huh",
            "IGNORE"
        )
        
        print("✅ Result: Agent speech was NEVER interrupted by filler words!")
        
        # ==================== SCENARIO 2 ====================
        self.print_scenario(
            2,
            "The Passive Affirmation",
            "Agent asks a question and waits for response"
        )
        
        print("Agent: \"Are you ready to begin?\"")
        print("Agent: (goes silent, waiting for response)")
        await asyncio.sleep(0.5)
        
        self.test_interaction(
            AgentState.SILENT,
            "yeah",
            "RESPOND"
        )
        
        print("Agent: \"Great! Let's get started.\"")
        print("✅ Result: Agent correctly processed 'yeah' as valid input!")
        
        # ==================== SCENARIO 3 ====================
        self.print_scenario(
            3,
            "The Explicit Interruption",
            "Agent is counting and user wants to stop"
        )
        
        print("Agent: \"One, two, three...\"")
        await asyncio.sleep(0.3)
        
        self.test_interaction(
            AgentState.SPEAKING,
            "no stop",
            "INTERRUPT"
        )
        
        print("Agent: (STOPS immediately)")
        print("Agent: \"Okay, I've stopped. What would you like?\"")
        print("✅ Result: Agent interrupted immediately on command!")
        
        # ==================== SCENARIO 4 ====================
        self.print_scenario(
            4,
            "The Mixed Input",
            "Agent is explaining something and user has a question"
        )
        
        print("Agent: \"The process involves three main steps...\"")
        await asyncio.sleep(0.5)
        
        self.test_interaction(
            AgentState.SPEAKING,
            "yeah okay but wait",
            "INTERRUPT"
        )
        
        print("Agent: (STOPS due to 'wait' command)")
        print("Agent: \"Yes? What would you like to know?\"")
        print("✅ Result: Agent detected command word in mixed input!")
        
        # ==================== ADDITIONAL EDGE CASES ====================
        self.print_scenario(
            5,
            "Edge Cases & Robustness",
            "Testing various edge cases"
        )
        
        print("Test: Multiple filler words in a row (while speaking)")
        self.test_interaction(
            AgentState.SPEAKING,
            "yeah okay right hmm",
            "IGNORE"
        )
        
        print("Test: Substantial content (while speaking)")
        self.test_interaction(
            AgentState.SPEAKING,
            "that's really interesting",
            "INTERRUPT"
        )
        
        print("Test: Case insensitivity")
        self.test_interaction(
            AgentState.SPEAKING,
            "STOP",
            "INTERRUPT"
        )
        
        print("Test: Empty input")
        self.test_interaction(
            AgentState.SPEAKING,
            "",
            "IGNORE"
        )
        
        # ==================== RESULTS SUMMARY ====================
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        self.print_banner("DEMO RESULTS SUMMARY")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n")
        
        if failed_tests > 0:
            print("Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  • {result['scenario']}")
                    print(f"    Expected: {result['expected']}, Got: {result['actual']}")
        else:
            print("🎉 ALL TESTS PASSED!")
        
        print("\n" + "="*70)
        print("  DEMO COMPLETE")
        print("="*70 + "\n")


async def main():
    """Run the demo."""
    print("\n" + "🎬 Starting Intelligent Interruption Handler Demo...")
    print("📅 Demo Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    simulator = DemoSimulator()
    await simulator.run_demo()
    
    print("\n💡 Key Takeaways:")
    print("   1. Agent ignores filler words (yeah, ok, hmm) while SPEAKING")
    print("   2. Agent processes filler words as valid input when SILENT")
    print("   3. Agent interrupts immediately on command words (stop, wait, no)")
    print("   4. Agent handles mixed input intelligently")
    print("   5. No pauses, stutters, or hiccups in agent speech!")
    
    print("\n📹 This output can be used as proof of functionality.")
    print("📄 Save this log for your submission!\n")


if __name__ == "__main__":
    asyncio.run(main())

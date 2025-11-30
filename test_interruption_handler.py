"""
Test cases for Intelligent Interruption Handler
Validates all scenarios from the assignment requirements
"""

import pytest
import asyncio
from intelligent_interruption_handler import (
    InterruptionHandler, 
    AgentState,
    IntelligentAgent
)


class TestInterruptionHandler:
    """Test suite for InterruptionHandler logic."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.handler = InterruptionHandler()
    
    # ==================== Scenario 1: Long Explanation ====================
    
    def test_ignore_filler_while_speaking(self):
        """
        Test: Agent ignores filler words while speaking
        Context: Agent is reading a long paragraph
        User says: "Okay... yeah... uh-huh"
        Expected: Return False (do NOT interrupt)
        """
        self.handler.set_state(AgentState.SPEAKING)
        
        # Test single filler words
        assert not self.handler.should_interrupt("yeah")
        assert not self.handler.should_interrupt("okay")
        assert not self.handler.should_interrupt("hmm")
        assert not self.handler.should_interrupt("uh-huh")
        assert not self.handler.should_interrupt("right")
        
        # Test multiple filler words
        assert not self.handler.should_interrupt("yeah okay")
        assert not self.handler.should_interrupt("hmm right uh-huh")
        
        print("✅ Scenario 1 PASSED: Filler words ignored while speaking")
    
    # ==================== Scenario 2: Passive Affirmation ====================
    
    def test_respond_to_filler_when_silent(self):
        """
        Test: Agent responds to filler words when silent
        Context: Agent asks "Are you ready?" and goes silent
        User says: "Yeah"
        Expected: Return True (process as valid input)
        """
        self.handler.set_state(AgentState.SILENT)
        
        # Filler words should be processed when agent is silent
        assert self.handler.should_interrupt("yeah")
        assert self.handler.should_interrupt("okay")
        assert self.handler.should_interrupt("hmm")
        
        print("✅ Scenario 2 PASSED: Filler words processed when silent")
    
    # ==================== Scenario 3: Explicit Interruption ====================
    
    def test_interrupt_on_command_words(self):
        """
        Test: Agent stops on explicit command words
        Context: Agent is counting "One, two, three..."
        User says: "No stop"
        Expected: Return True (interrupt immediately)
        """
        self.handler.set_state(AgentState.SPEAKING)
        
        # Test command words
        assert self.handler.should_interrupt("stop")
        assert self.handler.should_interrupt("wait")
        assert self.handler.should_interrupt("no")
        assert self.handler.should_interrupt("hold on")
        
        # Test command in sentence
        assert self.handler.should_interrupt("no stop")
        assert self.handler.should_interrupt("please wait")
        assert self.handler.should_interrupt("hold on a second")
        
        print("✅ Scenario 3 PASSED: Command words trigger interrupt")
    
    # ==================== Scenario 4: Mixed Input ====================
    
    def test_mixed_input_with_command(self):
        """
        Test: Agent interrupts on mixed input containing commands
        Context: Agent is speaking
        User says: "Yeah okay but wait"
        Expected: Return True (interrupt because of "wait")
        """
        self.handler.set_state(AgentState.SPEAKING)
        
        # Mixed input with command word
        assert self.handler.should_interrupt("yeah okay but wait")
        assert self.handler.should_interrupt("hmm actually stop")
        assert self.handler.should_interrupt("right but no")
        
        print("✅ Scenario 4 PASSED: Mixed input with commands interrupts")
    
    def test_mixed_input_without_command(self):
        """
        Test: Agent interrupts on mixed input with non-filler content
        Context: Agent is speaking
        User says: "Yeah that's interesting"
        Expected: Return True (interrupt - contains substantial content)
        """
        self.handler.set_state(AgentState.SPEAKING)
        
        # Mixed input with substantial content (not just fillers)
        assert self.handler.should_interrupt("yeah that's interesting")
        assert self.handler.should_interrupt("okay tell me more")
        assert self.handler.should_interrupt("hmm what about this")
        
        print("✅ PASSED: Mixed input with content interrupts")
    
    # ==================== Edge Cases ====================
    
    def test_empty_input(self):
        """Test handling of empty input."""
        self.handler.set_state(AgentState.SPEAKING)
        assert not self.handler.should_interrupt("")
        assert not self.handler.should_interrupt("   ")
        
        print("✅ PASSED: Empty input handled correctly")
    
    def test_case_insensitivity(self):
        """Test that comparison is case-insensitive."""
        self.handler.set_state(AgentState.SPEAKING)
        
        assert not self.handler.should_interrupt("YEAH")
        assert not self.handler.should_interrupt("Yeah")
        assert not self.handler.should_interrupt("yEaH")
        
        assert self.handler.should_interrupt("STOP")
        assert self.handler.should_interrupt("Stop")
        
        print("✅ PASSED: Case-insensitive matching works")
    
    def test_state_transitions(self):
        """Test state transitions work correctly."""
        # Start silent
        assert self.handler.agent_state == AgentState.SILENT
        
        # Change to speaking
        self.handler.set_state(AgentState.SPEAKING)
        assert self.handler.is_speaking()
        
        # Change back to silent
        self.handler.set_state(AgentState.SILENT)
        assert not self.handler.is_speaking()
        
        print("✅ PASSED: State transitions work correctly")
    
    def test_custom_ignore_words(self):
        """Test custom ignore words configuration."""
        custom_handler = InterruptionHandler(
            ignore_words=['custom', 'filler', 'word']
        )
        custom_handler.set_state(AgentState.SPEAKING)
        
        # Custom words should be ignored
        assert not custom_handler.should_interrupt("custom")
        assert not custom_handler.should_interrupt("filler word")
        
        # Default words not in custom list should interrupt
        assert custom_handler.should_interrupt("yeah")
        
        print("✅ PASSED: Custom ignore words work correctly")


class TestFullIntegration:
    """Integration tests simulating full conversation flows."""
    
    @pytest.mark.asyncio
    async def test_full_scenario_flow(self):
        """
        Test complete conversation flow:
        1. Agent speaks -> User says "yeah" -> Agent continues
        2. Agent finishes -> User says "yeah" -> Agent responds
        3. Agent speaks -> User says "wait" -> Agent stops
        """
        handler = InterruptionHandler()
        
        # Step 1: Agent speaking, user says filler
        handler.set_state(AgentState.SPEAKING)
        result1 = handler.should_interrupt("yeah")
        assert not result1, "Agent should ignore 'yeah' while speaking"
        
        # Step 2: Agent finishes, becomes silent, user says filler
        handler.set_state(AgentState.SILENT)
        result2 = handler.should_interrupt("yeah")
        assert result2, "Agent should process 'yeah' when silent"
        
        # Step 3: Agent speaking again, user says command
        handler.set_state(AgentState.SPEAKING)
        result3 = handler.should_interrupt("wait")
        assert result3, "Agent should interrupt on 'wait' command"
        
        print("✅ PASSED: Full integration scenario works correctly")


def run_all_tests():
    """Run all test cases and print results."""
    print("\n" + "="*60)
    print("  INTELLIGENT INTERRUPTION HANDLER - TEST SUITE")
    print("="*60 + "\n")
    
    test_handler = TestInterruptionHandler()
    
    try:
        # Scenario tests
        test_handler.setup_method()
        test_handler.test_ignore_filler_while_speaking()
        
        test_handler.setup_method()
        test_handler.test_respond_to_filler_when_silent()
        
        test_handler.setup_method()
        test_handler.test_interrupt_on_command_words()
        
        test_handler.setup_method()
        test_handler.test_mixed_input_with_command()
        
        test_handler.setup_method()
        test_handler.test_mixed_input_without_command()
        
        # Edge case tests
        test_handler.setup_method()
        test_handler.test_empty_input()
        
        test_handler.setup_method()
        test_handler.test_case_insensitivity()
        
        test_handler.setup_method()
        test_handler.test_state_transitions()
        
        test_handler.setup_method()
        test_handler.test_custom_ignore_words()
        
        # Integration test
        integration_test = TestFullIntegration()
        asyncio.run(integration_test.test_full_scenario_flow())
        
        print("\n" + "="*60)
        print("  ✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

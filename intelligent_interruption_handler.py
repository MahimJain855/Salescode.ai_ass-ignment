"""
LiveKit Intelligent Interruption Handler
Implements context-aware interruption logic to distinguish between
passive acknowledgements and active interruptions.
"""

import asyncio
import logging
from typing import List, Set
from enum import Enum
from livekit import agents
from livekit.agents import llm, stt, tts

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Tracks whether the agent is currently speaking or silent."""
    SPEAKING = "speaking"
    SILENT = "silent"


class InterruptionHandler:
    """
    Handles intelligent interruption detection based on agent state.
    
    Core Logic:
    - If agent is SPEAKING and user says filler words -> IGNORE
    - If agent is SPEAKING and user says command words -> INTERRUPT
    - If agent is SILENT and user says anything -> RESPOND
    """
    
    def __init__(self, ignore_words: List[str] = None):
        """
        Initialize the interruption handler.
        
        Args:
            ignore_words: List of words to ignore when agent is speaking
        """
        # Default ignore list (configurable)
        self.ignore_words: Set[str] = set(
            ignore_words or [
                'yeah', 'ok', 'okay', 'hmm', 'uh-huh', 'mhm', 
                'right', 'aha', 'yep', 'sure', 'gotcha'
            ]
        )
        
        # Command words that should always interrupt
        self.interrupt_words: Set[str] = {
            'wait', 'stop', 'no', 'hold', 'pause', 'hold on'
        }
        
        self.agent_state = AgentState.SILENT
        self._speaking_lock = asyncio.Lock()
        self._pending_interruptions = []
        
    def set_state(self, state: AgentState):
        """Update the current agent state."""
        self.agent_state = state
        logger.debug(f"Agent state changed to: {state.value}")
    
    def is_speaking(self) -> bool:
        """Check if agent is currently speaking."""
        return self.agent_state == AgentState.SPEAKING
    
    def should_interrupt(self, user_input: str) -> bool:
        """
        Determine if user input should interrupt the agent.
        
        Args:
            user_input: The transcribed user speech
            
        Returns:
            True if agent should be interrupted, False otherwise
        """
        if not user_input:
            return False
        
        # Normalize input
        normalized_input = user_input.lower().strip()
        words = normalized_input.split()
        
        # If agent is SILENT, all input is valid
        if not self.is_speaking():
            logger.debug(f"Agent is silent, processing input: '{user_input}'")
            return True  # Not really an interruption, but valid input
        
        # Agent is SPEAKING - check if this should interrupt
        
        # Check for explicit interrupt commands
        for word in self.interrupt_words:
            if word in normalized_input:
                logger.info(f"Interrupt command detected: '{word}' in '{user_input}'")
                return True
        
        # Check if input contains ONLY ignore words
        non_ignore_words = [w for w in words if w not in self.ignore_words]
        
        if not non_ignore_words:
            # Only filler words - IGNORE
            logger.debug(f"Ignoring filler input while speaking: '{user_input}'")
            return False
        
        # Contains non-filler words - INTERRUPT
        logger.info(f"Valid interruption detected: '{user_input}'")
        return True


class IntelligentAgent:
    """
    Main agent class with intelligent interruption handling.
    """
    
    def __init__(
        self,
        vad: agents.vad.VAD,
        stt_instance: stt.STT,
        tts_instance: tts.TTS,
        llm_instance: llm.LLM,
        ignore_words: List[str] = None
    ):
        self.vad = vad
        self.stt = stt_instance
        self.tts = tts_instance
        self.llm = llm_instance
        
        # Initialize interruption handler
        self.interrupt_handler = InterruptionHandler(ignore_words)
        
        # Audio playback tracking
        self._current_speech_task = None
        self._speech_queue = asyncio.Queue()
        self._transcription_buffer = []
        
    async def _play_speech(self, text: str):
        """
        Play TTS audio and track agent state.
        
        Args:
            text: Text to convert to speech and play
        """
        try:
            # Set state to SPEAKING before starting
            self.interrupt_handler.set_state(AgentState.SPEAKING)
            logger.info(f"Agent speaking: '{text}'")
            
            # Generate and play audio
            audio_stream = self.tts.synthesize(text)
            
            async for audio_chunk in audio_stream:
                # Check if we should stop due to valid interruption
                if self._should_stop_speech():
                    logger.info("Speech interrupted by valid user input")
                    break
                
                # Play audio chunk
                # await self.play_audio(audio_chunk)
                await asyncio.sleep(0)  # Yield control
                
        except asyncio.CancelledError:
            logger.info("Speech playback cancelled")
            raise
        finally:
            # Set state back to SILENT
            self.interrupt_handler.set_state(AgentState.SILENT)
            logger.info("Agent finished speaking")
    
    def _should_stop_speech(self) -> bool:
        """
        Check if speech should be stopped based on interruptions.
        
        Returns:
            True if valid interruption detected
        """
        # Process any pending transcriptions
        while self._transcription_buffer:
            transcription = self._transcription_buffer.pop(0)
            if self.interrupt_handler.should_interrupt(transcription):
                return True
        return False
    
    async def _handle_user_input(self, transcription: str):
        """
        Handle incoming user speech transcription.
        
        Args:
            transcription: User speech converted to text
        """
        logger.debug(f"Received transcription: '{transcription}'")
        
        # Add to buffer for processing
        self._transcription_buffer.append(transcription)
        
        # If agent is speaking, check if this should interrupt
        if self.interrupt_handler.is_speaking():
            should_interrupt = self.interrupt_handler.should_interrupt(transcription)
            
            if not should_interrupt:
                # Filler word while speaking - ignore completely
                logger.debug(f"Ignoring filler while speaking: '{transcription}'")
                self._transcription_buffer.clear()
                return
            else:
                # Valid interruption - cancel current speech
                logger.info(f"Interrupting speech for: '{transcription}'")
                if self._current_speech_task:
                    self._current_speech_task.cancel()
                    self._current_speech_task = None
        
        # Process the input (agent is silent or interrupted)
        await self._process_user_message(transcription)
    
    async def _process_user_message(self, message: str):
        """
        Process valid user message and generate response.
        
        Args:
            message: User message to process
        """
        logger.info(f"Processing user message: '{message}'")
        
        # Generate LLM response
        response = await self.llm.generate(message)
        
        # Queue speech
        self._current_speech_task = asyncio.create_task(
            self._play_speech(response)
        )
        await self._current_speech_task
    
    async def start(self):
        """Start the agent event loop."""
        logger.info("Starting intelligent agent...")
        
        # Start VAD and STT streams
        async with self.vad.stream() as vad_stream:
            async with self.stt.stream() as stt_stream:
                
                async for event in vad_stream:
                    # VAD detected speech
                    if event.type == "speech_started":
                        logger.debug("VAD: Speech started")
                        
                    elif event.type == "speech_ended":
                        logger.debug("VAD: Speech ended")
                        
                        # Get transcription
                        transcription = await stt_stream.get_transcription()
                        
                        # Handle with intelligent logic
                        await self._handle_user_input(transcription)


# Configuration loader
def load_config():
    """Load configuration from environment or config file."""
    import os
    
    # Load ignore words from environment variable if available
    ignore_words_str = os.getenv('IGNORE_WORDS', '')
    if ignore_words_str:
        ignore_words = [w.strip() for w in ignore_words_str.split(',')]
    else:
        ignore_words = None  # Use defaults
    
    return {
        'ignore_words': ignore_words
    }


# Main entry point
async def main():
    """Initialize and run the intelligent agent."""
    
    # Load configuration
    config = load_config()
    
    # Initialize LiveKit components (pseudo-code - adjust to actual SDK)
    vad = agents.vad.SileroVAD()
    stt_instance = stt.DeepgramSTT()
    tts_instance = tts.ElevenLabsTTS()
    llm_instance = llm.OpenAILLM()
    
    # Create intelligent agent
    agent = IntelligentAgent(
        vad=vad,
        stt_instance=stt_instance,
        tts_instance=tts_instance,
        llm_instance=llm_instance,
        ignore_words=config['ignore_words']
    )
    
    # Start the agent
    await agent.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

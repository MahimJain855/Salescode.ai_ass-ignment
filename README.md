# LiveKit Intelligent Interruption Handler

## 🎯 Overview

This solution implements context-aware interruption handling for LiveKit AI agents. The agent intelligently distinguishes between passive acknowledgements (backchanneling) and active interruptions based on its current speaking state.

## 🧠 Core Logic

The system operates on a state-based logic matrix:

| User Input | Agent State | Behavior |
|------------|-------------|----------|
| "Yeah/Ok/Hmm" | SPEAKING | **IGNORE** - Agent continues without pause |
| "Wait/Stop/No" | SPEAKING | **INTERRUPT** - Agent stops immediately |
| "Yeah/Ok/Hmm" | SILENT | **RESPOND** - Treated as valid input |
| Any input | SILENT | **RESPOND** - Normal conversation |

## 🔧 How It Works

### 1. State Tracking
The agent maintains two states:
- **SPEAKING**: Agent is currently generating/playing audio
- **SILENT**: Agent is listening for user input

### 2. Input Classification
Incoming transcriptions are classified into three categories:
- **Filler words** (ignore list): "yeah", "ok", "hmm", "uh-huh", etc.
- **Command words** (interrupt list): "wait", "stop", "no", "hold", etc.
- **Regular speech**: Everything else

### 3. Decision Logic

```python
if agent_state == SPEAKING:
    if input contains ONLY filler words:
        → IGNORE (continue speaking)
    elif input contains command words OR non-filler content:
        → INTERRUPT (stop speaking)
else:  # agent_state == SILENT
    → RESPOND (process as normal input)
```

### 4. Key Implementation Features

#### Transcription Buffer
- VAD triggers faster than STT completion
- Transcriptions are buffered and checked against agent state
- Only valid interruptions stop speech playback

#### Seamless Continuation
- When filler words are detected during speech, they're completely ignored
- No pause, stutter, or hiccup in agent audio
- Speech task continues uninterrupted

#### Mixed Input Handling
- Input like "Yeah okay but wait" is analyzed word-by-word
- Presence of command word "wait" triggers interruption
- Semantic understanding of intent, not just keyword matching

## 📦 Installation

### Prerequisites
- Python 3.8+
- LiveKit SDK
- Required dependencies in `requirements.txt`

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/Dark-Sys-Jenkins/agents-assignment.git
cd agents-assignment
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

## 🚀 Usage

### Basic Usage

```python
from intelligent_interruption_handler import IntelligentAgent, load_config

# Load configuration
config = load_config()

# Initialize agent
agent = IntelligentAgent(
    vad=your_vad_instance,
    stt_instance=your_stt_instance,
    tts_instance=your_tts_instance,
    llm_instance=your_llm_instance,
    ignore_words=config['ignore_words']
)

# Start the agent
await agent.start()
```

### Running the Agent

```bash
python intelligent_interruption_handler.py
```

### Configuration

#### Custom Ignore Words

Set via environment variable:
```bash
export IGNORE_WORDS="yeah,ok,hmm,right,uh-huh,gotcha,sure"
```

Or modify in code:
```python
agent = IntelligentAgent(
    ...,
    ignore_words=['yeah', 'ok', 'custom_word']
)
```

#### Logging

Adjust log level for debugging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🧪 Test Scenarios

### Scenario 1: Long Explanation
**Context**: Agent reading a paragraph about history

**User Action**: Says "Okay... yeah... uh-huh" while agent talks

**Expected Result**: ✅ Agent continues without interruption

**How to test**:
```bash
# Start agent, let it speak, then say filler words
# Observe: No pause or break in agent speech
```

### Scenario 2: Passive Affirmation
**Context**: Agent asks "Are you ready?" and goes silent

**User Action**: Says "Yeah"

**Expected Result**: ✅ Agent processes "Yeah" as answer

**How to test**:
```bash
# Wait for agent to finish speaking
# Say "yeah" during silence
# Observe: Agent responds appropriately
```

### Scenario 3: Explicit Interruption
**Context**: Agent counting "One, two, three..."

**User Action**: Says "No stop"

**Expected Result**: ✅ Agent stops immediately

**How to test**:
```bash
# While agent is speaking
# Say "stop" or "wait"
# Observe: Agent cuts off immediately
```

### Scenario 4: Mixed Input
**Context**: Agent is speaking

**User Action**: Says "Yeah okay but wait"

**Expected Result**: ✅ Agent stops (contains "wait")

**How to test**:
```bash
# While agent speaks
# Say a mixed phrase with command word
# Observe: Agent interrupts on command word
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────┐
│                  User Speech                     │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │   VAD Stream    │ (Fast detection)
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   STT Stream    │ (Transcription)
         └────────┬────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │   InterruptionHandler           │
    │                                 │
    │  • Check agent state            │
    │  • Classify input               │
    │  • Decide: IGNORE/INTERRUPT     │
    └────────┬────────────────────────┘
             │
             ├─► IGNORE → Continue speech
             │
             └─► INTERRUPT → Cancel speech task
                              ↓
                    Generate new response
```

## 🔍 Key Technical Details

### State Management
```python
class AgentState(Enum):
    SPEAKING = "speaking"  # Set when TTS starts
    SILENT = "silent"      # Set when TTS ends
```

### Interruption Detection
```python
def should_interrupt(self, user_input: str) -> bool:
    # Agent silent → Always process input
    if not self.is_speaking():
        return True
    
    # Agent speaking → Check content
    if contains_only_filler_words(user_input):
        return False  # IGNORE
    else:
        return True   # INTERRUPT
```

### Speech Cancellation
```python
# During speech playback, continuously check buffer
if self._should_stop_speech():
    self._current_speech_task.cancel()
```

## 📝 Requirements

```txt
livekit-agents>=0.8.0
livekit-api>=0.4.0
python-dotenv>=1.0.0
```

## 🎬 Demo Video

[Include link to demo video showing:]
1. Agent ignoring "yeah" while speaking
2. Agent responding to "yeah" when silent
3. Agent stopping for "stop" command

## 🐛 Troubleshooting

### Issue: Agent still pauses on filler words

**Solution**: Check that `ignore_words` is properly configured and agent state is correctly tracked.

### Issue: Agent doesn't respond when silent

**Solution**: Verify that `should_interrupt()` returns `True` when agent state is SILENT.

### Issue: Latency in interruption detection

**Solution**: Ensure STT is optimized and transcription buffer is processed efficiently.


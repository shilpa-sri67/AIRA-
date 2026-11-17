# AIRA AI Assistant Backend

Modular, real-time AI Assistant architecture powered by **Gemini 3.8 Flash**, featuring live voice transcription, function calling tool router (OS, App, IoT), execution verification, and real-time speech synthesis.

---

## 🏛 System Architecture

```text
             AIRA FRONTEND
                   │
             MICROPHONE
                   │
       Gemini 3.5 Transcribe Live
                   │
             TRANSCRIBED TEXT
                   │
           PYTHON AGENT CORE
                   │
           Gemini 3.8 Flash
                   │
          DECISION + PLANNING
                   │
             TOOL ROUTER
                   │
       ┌───────────┼────────────┐
       │           │            │
   OS Control  App Control   IoT Control
       │           │            │
       └───────────┼────────────┘
                   │
              VERIFICATION
                   │
           RESPONSE GENERATION
                   │
          Gemini 3.8 Flash TTS
                   │
              AIRA SPEAKS
```

---

## ⚙️ Core Architecture Modules

### 1. Voice Ingestion & Live Transcription
- **Microphone Capture**: Captures real-time audio streams and WAV inputs via `voice/audio_manger.py` and WebSockets.
- **Gemini 3.5 Transcribe Live (`voice/speech_to_text.py`)**: Streams audio to Gemini Live STT / Multimodal Audio for low-latency speech-to-text. Includes automatic local fallback to `faster-whisper`.

### 2. Python Agent Core (`backend/agent_core.py`)
- Powered by **Gemini 3.8 Flash**.
- Implements multi-turn reasoning, conversational personality, and automatic tool orchestration.
- System prompt instructs AIRA to formulate execution plans, invoke tools, verify outputs, and generate friendly responses.

### 3. Tool Router & Domain Controllers (`backend/tools/`)
The Tool Router dynamically maps planned actions to specific hardware/software subsystems:
- **OS Control (`backend/tools/os_control.py`)**:
  - System volume (`adjust_volume`: set, mute, up, down)
  - Screen brightness (`adjust_brightness`)
  - Workstation lock (`lock_screen`)
  - Screenshot capture (`take_screenshot`)
  - Clipboard operations (`manage_clipboard`: copy/paste)
  - System telemetry (`get_system_stats`: CPU %, RAM GB/%, Disk free, Battery status)
  - File explorer navigation (`open_folder`)
- **App Control (`backend/tools/app_control.py`)**:
  - Desktop application launch (`launch_app`: Chrome, Spotify, VS Code, Notepad, Calc, Terminal, etc.)
  - Application termination (`close_app`)
  - Web browser URL navigation (`open_url`)
  - Media key controls (`media_control`: play/pause, next, previous, stop)
  - Active process inspection (`list_running_apps`)
- **IoT Control (`backend/tools/iot_control.py`)**:
  - Smart Lights (`control_light`: living room, bedroom, studio, kitchen, all; brightness, RGB/warm/daylight colors)
  - Smart Plugs (`control_plug`: desk charger, coffee maker, fan)
  - Smart Thermostat / AC (`control_thermostat`: target temp in °C, modes: cool, heat, eco, fan)
  - Smart Scenes (`activate_scene`: `movie_night`, `focus_mode`, `good_morning`, `sleep`)
  - Environment state query (`get_iot_status`)

### 4. Verification Engine (`backend/tools/router.py`)
- **Pre-execution validation**: Sanitizes and verifies parameter constraints (e.g., brightness 0–100%, temperature ranges 16–32°C).
- **Post-execution verification**: Validates that system, application, or IoT calls completed successfully and formats a structured result report back into the agent context (`verified: True / False`).

### 5. Response Generation & Speech Synthesis ("AIRA SPEAKS")
- **Gemini 3.8 Flash TTS (`voice/text_to_speech.py`)**: Converts generated responses into natural neural voice using high-fidelity Edge-TTS / Pyttsx3 fallback.
- Plays directly over host speakers and streams audio files over HTTP/WebSocket to the frontend.

---

## 🚀 Getting Started

### 1. Environment Configuration
Ensure your `.env` contains:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_CORE_MODEL=gemini-3.8-flash
GEMINI_LIVE_STT_MODEL=gemini-3.8-flash
GEMINI_TTS_MODEL=gemini-3.8-flash
TTS_ENGINE=edge_tts
TTS_VOICE=en-US-AriaNeural
```

### 2. Interactive Terminal Runner
Run the full architecture directly in your console:
```bash
python run_aira.py
```
Options available:
- **1. Text Mode**: Chat with AIRA, see decisions, tool routing, verification, and listen to voice output.
- **2. Voice Mode**: Speak into your microphone and test the full STT -> Agent -> Tool -> TTS pipeline.
- **3. View IoT Devices & OS Status**: Live hardware and smart home dashboard.
- **4. Start FastAPI Server**: Launch the HTTP/WebSocket backend.

### 3. Run FastAPI Backend
```bash
python main.py
```
or
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs available at: `http://127.0.0.1:8000/docs`.

---

## 📡 API & WebSocket Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/agent/interact` | Send text or transcribed query; returns reply, executed tools, verification, and audio URL |
| `GET` | `/api/v1/agent/tools` | List all available tools and schema definitions |
| `POST` | `/api/v1/voice/transcribe` | Upload an audio file to transcribe via Gemini Live STT |
| `POST` | `/api/v1/voice/speak` | Synthesize speech for any text via Gemini Flash TTS |
| `POST` | `/api/v1/voice/mic-listen` | Trigger backend microphone record & end-to-end voice processing |
| `GET` | `/api/v1/iot/devices` | Query current real-time state of all IoT smart devices |
| `POST` | `/api/v1/iot/scene` | Activate smart scene preset (`movie_night`, `focus_mode`, etc.) |
| `WS` | `/api/v1/ws/live` | Real-time bidirectional streaming for microphone audio, live events, and TTS chunks |


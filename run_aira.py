import sys
import os
import time

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from backend.agent_core import agent_core
from backend.tools.router import tool_router
from voice.text_to_speech import aira_tts
from voice.speech_to_text import gemini_stt
from voice.audio_manger import audio_manager


BANNER = """
========================================================================
                      AIRA ARCHITECTURE RUNNER
========================================================================
  [AIRA FRONTEND / CLI]
           |
     [MICROPHONE]
           |
  [Gemini 3.5 Transcribe Live]
           |
     [TRANSCRIBED TEXT]
           |
  [PYTHON AGENT CORE - Gemini 3.8 Flash]
           |
    [DECISION + PLANNING]
           |
      [TOOL ROUTER]
    ┌──────┼──────┐
    |      |      |
  [OS]   [App]  [IoT]
    |      |      |
    └──────┼──────┘
           |
    [VERIFICATION]
           |
  [RESPONSE GENERATION]
           |
  [Gemini 3.8 Flash TTS]
           |
     [AIRA SPEAKS]
========================================================================
"""


def print_tool_execution(tools_called):
    if not tools_called:
        return
    print("\n------------------- [TOOL ROUTER & VERIFICATION] -------------------")
    for idx, t in enumerate(tools_called, 1):
        domain = t.get("domain", "Unknown")
        tool = t.get("tool", "Unnamed")
        verified = t.get("verified", False)
        status = t.get("status", "unknown")
        notes = t.get("verification_notes", "")
        result = t.get("result", {})

        icon = "✓" if verified else "✗"
        print(f" [{idx}] Domain: {domain} | Tool: {tool}")
        print(f"     Verification: [{icon}] {status.upper()} - {notes}")
        if result and "message" in result:
            print(f"     Outcome: {result['message']}")
    print("--------------------------------------------------------------------\n")


def text_mode():
    print("\n[AIRA Text Mode] Type your instruction (e.g. 'Turn on living room light', 'Check battery', 'Take a screenshot')")
    print("Type 'exit' or 'back' to return.\n")

    while True:
        try:
            query = input("You > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "back"]:
                break

            print("\n[Decision + Planning] Python Agent Core analyzing...")
            start = time.time()
            res = agent_core.process(query)
            elapsed = round(time.time() - start, 2)

            print_tool_execution(res.get("tools_called", []))

            reply = res["text"]
            print(f"AIRA ({elapsed}s) > {reply}\n")

            # Voice synthesis
            try:
                aira_tts.speak(reply, block=False)
            except Exception as e:
                pass

        except KeyboardInterrupt:
            print("\nExiting text mode.")
            break


def voice_mode():
    print("\n[AIRA Voice Mode] End-to-end voice architecture activated!")
    print("Commands:")
    print("  [Enter] : Record 5 seconds of microphone audio")
    print("  'back'  : Return to main menu\n")

    while True:
        try:
            cmd = input("Press [Enter] to speak (or type 'back'): ").strip()
            if cmd.lower() in ["back", "exit", "quit"]:
                break

            result = audio_manager.listen_and_process(duration=5)
            print_tool_execution(result.get("tools_called", []))
            print(f"AIRA > {result.get('response')}\n")

        except KeyboardInterrupt:
            print("\nExiting voice mode.")
            break


def show_devices():
    status = tool_router.execute_and_verify("get_iot_status", {})
    print("\n================== [CURRENT IOT ENVIRONMENT] ==================")
    env = status["result"]["environment"]
    print("Lights:")
    for k, v in env["lights"].items():
        print(f"  * {v['name']} ({k}): {v['state'].upper()} | Brightness: {v['brightness']}% | Color: {v['color']}")
    print("\nPlugs:")
    for k, v in env["plugs"].items():
        print(f"  * {v['name']} ({k}): {v['state'].upper()} | {v['current_watts']}W")
    print("\nThermostat:")
    t = env["thermostat"]
    print(f"  * Current: {t['current_temp']}°C | Target: {t['target_temp']}°C | Mode: {t['mode'].upper()}")
    print("================================================================\n")


def main():
    print(BANNER)
    while True:
        print("Choose an option:")
        print("  1. Text Mode (Interact via keyboard)")
        print("  2. Voice Mode (Microphone -> Gemini STT -> Core -> Tools -> Gemini TTS)")
        print("  3. View IoT Devices & OS Status")
        print("  4. Start FastAPI Server")
        print("  5. Exit")

        choice = input("\nSelect (1-5): ").strip()
        if choice == "1":
            text_mode()
        elif choice == "2":
            voice_mode()
        elif choice == "3":
            show_devices()
        elif choice == "4":
            print("\nStarting FastAPI server on http://127.0.0.1:8000 ...")
            import uvicorn
            uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
        elif choice in ["5", "exit", "quit"]:
            print("Exiting AIRA.")
            break
        else:
            print("Invalid choice, please select 1 to 5.")


if __name__ == "__main__":
    main()


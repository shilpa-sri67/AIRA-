import logging
import json
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from app.core.config import settings
from backend.tools.router import tool_router

logger = logging.getLogger("aira.agent_core")


class AiraAgentCore:
    """
    PYTHON AGENT CORE (Powered by Gemini 3.8 Flash / Gemini 2.5 Flash)
    Orchestrates:
    - User input (transcribed speech or text)
    - Decision + Planning
    - Tool Router (OS Control, App Control, IoT Control)
    - Verification
    - Response Generation
    """

    SYSTEM_INSTRUCTION = """
You are AIRA (Artificial Intelligence Responsive Assistant), an advanced, intelligent personal AI companion.
You have direct, real-time control over:
1. OS Control: volume, brightness, battery stats, system performance, clipboard, screenshot, file browsing.
2. App Control: opening/closing apps (browser, spotify, notepad, vscode, calculator, etc.), navigating URLs, media playback (play/pause/next/previous).
3. IoT Control: smart lights (on/off, brightness, colors), smart plugs, AC/thermostat (temperature and modes), and smart scene presets ('movie_night', 'focus_mode', 'good_morning', 'sleep').

Behavior and Personality:
- Be natural, friendly, articulate, concise, and helpful.
- When the user asks you to perform an action or check status, ALWAYS plan and call the appropriate tool(s).
- You are connected to a Tool Router that executes and verifies every action.
- Once a tool action is verified, summarize the outcome naturally and pleasantly.
- Keep spoken responses crisp, conversational, and direct for seamless voice interaction.
"""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_CORE_MODEL
        self.client = None
        self.history: List[Dict[str, Any]] = []

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Gemini Client for model {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini Client: {e}")

    def _convert_tool_declarations_to_gemini(self) -> List[Any]:
        """Convert router tools to google-genai FunctionDeclaration types."""
        declarations = []
        for decl in tool_router.get_tool_declarations():
            declarations.append(types.FunctionDeclaration(
                name=decl["name"],
                description=decl["description"],
                parameters=decl.get("parameters"),
            ))
        return [types.Tool(function_declarations=declarations)]

    def _fallback_process(self, user_message: str) -> Dict[str, Any]:
        """
        Local / Offline Fallback Engine:
        Executes intent matching for OS/App/IoT commands if Gemini API is unreachable or key is unset.
        """
        msg = user_message.lower().strip()
        executed_tools = []
        response_text = ""

        # Intent detection
        if "stats" in msg or "battery" in msg or "cpu" in msg or "system" in msg or "memory" in msg or "ram" in msg:
            res = tool_router.execute_and_verify("get_system_stats", {})
            executed_tools.append(res)
            response_text = f"Here is your system status: CPU is at {res['result'].get('cpu_percent')}, memory used is {res['result'].get('memory_used')}, and disk has {res['result'].get('disk_free')} free."

        elif "volume" in msg:
            action = "set"
            val = 50
            if "up" in msg or "increase" in msg or "raise" in msg:
                action = "up"
                val = 5
            elif "down" in msg or "decrease" in msg or "lower" in msg:
                action = "down"
                val = 5
            elif "mute" in msg:
                action = "mute"
                val = None
            elif "unmute" in msg:
                action = "unmute"
                val = None
            res = tool_router.execute_and_verify("adjust_volume", {"action": action, "value": val})
            executed_tools.append(res)
            response_text = f"Done! {res['result'].get('message', 'Volume adjusted.')}"

        elif "screenshot" in msg:
            res = tool_router.execute_and_verify("take_screenshot", {})
            executed_tools.append(res)
            response_text = "I've taken a screenshot of your desktop and saved it to cache."

        elif "light" in msg or "lights" in msg:
            room = "all"
            for r in ["living_room", "bedroom", "studio", "kitchen"]:
                if r.replace("_", " ") in msg or r in msg:
                    room = r
                    break
            state = "on" if ("on" in msg or "turn on" in msg or "enable" in msg) else ("off" if "off" in msg else None)
            res = tool_router.execute_and_verify("control_light", {"room": room, "state": state})
            executed_tools.append(res)
            response_text = f"Smart lighting updated: {res['result'].get('message')}"

        elif "scene" in msg or "movie night" in msg or "focus mode" in msg or "good morning" in msg or "sleep mode" in msg:
            scene = "focus_mode"
            if "movie" in msg:
                scene = "movie_night"
            elif "morning" in msg:
                scene = "good_morning"
            elif "sleep" in msg or "night" in msg:
                scene = "sleep"
            res = tool_router.execute_and_verify("activate_scene", {"scene_name": scene})
            executed_tools.append(res)
            response_text = res['result'].get('message', 'Scene activated.')

        elif "open" in msg or "launch" in msg:
            target_app = msg.replace("open", "").replace("launch", "").replace("the", "").replace("app", "").strip()
            if target_app:
                res = tool_router.execute_and_verify("launch_app", {"app_name": target_app})
                executed_tools.append(res)
                response_text = f"Launching {target_app} for you."
            else:
                response_text = "What application would you like me to open?"

        elif "close" in msg:
            target_app = msg.replace("close", "").replace("kill", "").replace("exit", "").strip()
            res = tool_router.execute_and_verify("close_app", {"app_name": target_app})
            executed_tools.append(res)
            response_text = res['result'].get('message', f"Closed {target_app}.")

        else:
            # Try Ollama if installed
            try:
                import ollama
                res = ollama.chat(
                    model=settings.OLLAMA_FALLBACK_MODEL,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_INSTRUCTION},
                        {"role": "user", "content": user_message}
                    ]
                )
                response_text = res["message"]["content"]
            except Exception:
                response_text = f"I heard you say: '{user_message}'. I am ready to control your OS, desktop applications, or smart home devices."

        return {
            "text": response_text,
            "tools_called": executed_tools,
            "engine": "local_fallback",
        }

    def process(self, user_message: str) -> Dict[str, Any]:
        """
        PRIMARY PIPELINE:
        Decision + Planning -> Tool Router -> Verification -> Response Generation
        """
        logger.info(f"AIRA Agent Core received input: {user_message}")

        if not self.client:
            logger.info("No Gemini API client configured, using fallback engine.")
            return self._fallback_process(user_message)

        try:
            tools = self._convert_tool_declarations_to_gemini()
            config = types.GenerateContentConfig(
                system_instruction=self.SYSTEM_INSTRUCTION,
                tools=tools,
                temperature=0.7,
            )

            # Build chat messages
            contents = []
            for item in self.history[-6:]:  # Keep recent context
                contents.append(types.Content(
                    role=item["role"],
                    parts=[types.Part.from_text(text=item["text"])]
                ))

            # Add current user message
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)]
            ))

            # 1. Decision & Planning via Gemini 3.8 Flash
            logger.info("Invoking Gemini Core for Decision + Planning...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            executed_tools = []
            tool_parts = []

            # Check if model produced function calls
            if response.function_calls:
                for call in response.function_calls:
                    fn_name = call.name
                    fn_args = dict(call.args) if call.args else {}
                    logger.info(f"Model planned function call: {fn_name}({fn_args})")

                    # 2. Tool Router & 3. Verification
                    verification_result = tool_router.execute_and_verify(fn_name, fn_args)
                    executed_tools.append(verification_result)

                    # Prepare function response for verification loop
                    tool_parts.append(types.Part.from_function_response(
                        name=fn_name,
                        response={"result": verification_result}
                    ))

                # 4. Response Generation with Verification Results
                # Append model's tool calls and our verified function responses (with role='user')
                contents.append(response.candidates[0].content)
                contents.append(types.Content(role="user", parts=tool_parts))

                logger.info("Invoking Gemini Core for final Response Generation...")
                final_response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
                final_text = final_response.text or "All actions executed and verified."
            else:
                final_text = response.text or "I am listening."

            # Update conversation history
            self.history.append({"role": "user", "text": user_message})
            self.history.append({"role": "model", "text": final_text})

            return {
                "text": final_text,
                "tools_called": executed_tools,
                "engine": "gemini",
                "model": self.model_name,
            }

        except Exception as e:
            logger.error(f"Gemini Agent Core error: {e}", exc_info=True)
            # Graceful fallback so user never gets broken experience
            return self._fallback_process(user_message)


agent_core = AiraAgentCore()

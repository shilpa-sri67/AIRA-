from backend.agent_core import agent_core

def get_response(user_message: str) -> str:
    """
    AIRA Agent Core entry point.
    Executes: Transcribed Text -> Python Agent Core (Gemini 3.8 Flash) -> Decision & Planning -> Tool Router (OS/App/IoT) -> Verification -> Response Generation.
    """
    result = agent_core.process(user_message)
    return result["text"]


def process_with_verification(user_message: str):
    """
    Full pipeline entry point returning text, executed tools, and verification results.
    """
    return agent_core.process(user_message)

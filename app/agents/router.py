class AgentRouter:
    """
    Placeholder for the higher-level voice-agent router.

    The actual tool selection is currently performed by
    the Groq agent using function calling.

    This layer will become important in the next stages
    when we connect voice sessions, interruption handling,
    and streaming.
    """

    def route(self, message: str) -> str:

        return "agent"
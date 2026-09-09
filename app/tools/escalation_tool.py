def escalate_to_human(reason: str) -> dict:
    """
    Simulates escalation to a human support agent.

    In production this could create a ticket or push
    the conversation into a contact-center queue.
    """

    return {
        "escalated": True,
        "reason": reason,
        "message": "The conversation has been escalated to a human support agent.",
    }
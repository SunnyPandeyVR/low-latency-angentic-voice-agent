import asyncio
import os

import websockets


WEBSOCKET_URL = os.getenv(
    "VOICE_WEBSOCKET_URL",
    "ws://127.0.0.1:8000/ws/voice",
)


async def test_llm_interrupt():

    print("=" * 80)
    print("LLM INTERRUPT TEST")
    print("=" * 80)

    async with websockets.connect(
        WEBSOCKET_URL
    ) as websocket:

        # =========================================================
        # SESSION
        # =========================================================

        response = await websocket.recv()

        print("\nServer:")
        print(response)

        # =========================================================
        # START AUDIO
        # =========================================================

        await websocket.send(
            "start_audio"
        )

        response = await websocket.recv()

        print("\nServer:")
        print(response)

        # =========================================================
        # START LLM
        # =========================================================

        print(
            "\nClient: Starting LLM generation..."
        )

        await websocket.send(
            "llm_start: Explain what a low latency voice agent is in detail."
        )

        response = await websocket.recv()

        print("\nServer:")
        print(response)

        # Give the LLM a short amount of time
        # to start generating.

        await asyncio.sleep(0.5)

        # =========================================================
        # USER BARGE-IN
        # =========================================================

        print(
            "\nClient: User starts speaking..."
        )

        fake_audio = bytes(
            [1] * 1024
        )

        await websocket.send(
            fake_audio
        )

        # =========================================================
        # RECEIVE SERVER EVENTS
        # =========================================================

        response = await websocket.recv()

        print("\nServer:")
        print(response)

        response = await websocket.recv()

        print("\nServer:")
        print(response)

        # =========================================================
        # STOP AUDIO
        # =========================================================

        await websocket.send(
            "stop_audio"
        )

        response = await websocket.recv()

        print("\nServer:")
        print(response)

    print("\nLLM interrupt test complete.")

    print("=" * 80)


if __name__ == "__main__":

    asyncio.run(
        test_llm_interrupt()
    )
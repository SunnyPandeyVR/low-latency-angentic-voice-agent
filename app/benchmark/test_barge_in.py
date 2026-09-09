import asyncio
import os

import websockets


WEBSOCKET_URL = os.getenv(
    "VOICE_WEBSOCKET_URL",
    "ws://127.0.0.1:8000/ws/voice",
)


async def test_barge_in():

    print("=" * 80)
    print("BARGE-IN TEST")
    print("=" * 80)

    async with websockets.connect(
        WEBSOCKET_URL
    ) as websocket:

        # =========================================================
        # SESSION START
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
        # AI STARTS SPEAKING
        # =========================================================

        print("\nClient: AI starts speaking")

        await websocket.send(
            "ai_start"
        )

        response = await websocket.recv()

        print("Server:")
        print(response)

        # =========================================================
        # SIMULATE AI SPEAKING
        # =========================================================

        await asyncio.sleep(1)

        # =========================================================
        # USER STARTS SPEAKING
        #
        # This should trigger BARGE-IN.
        # =========================================================

        print(
            "\nClient: User starts speaking..."
        )

        fake_user_audio = bytes(
            [1] * 1024
        )

        await websocket.send(
            fake_user_audio
        )

        # First response: barge-in
        response = await websocket.recv()

        print("\nServer:")
        print(response)

        # Second response: audio acknowledgement
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

    print("\nBarge-in test complete.")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(
        test_barge_in()
    )
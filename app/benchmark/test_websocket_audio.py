import asyncio
import os

import websockets


WEBSOCKET_URL = os.getenv(
    "VOICE_WEBSOCKET_URL",
    "ws://127.0.0.1:8000/ws/voice",
)


async def test_audio_stream():

    print("=" * 80)
    print("WEBSOCKET AUDIO STREAM TEST")
    print("=" * 80)

    print(f"Connecting to: {WEBSOCKET_URL}")

    async with websockets.connect(
        WEBSOCKET_URL
    ) as websocket:

        # ---------------------------------------------------------
        # SESSION START
        # ---------------------------------------------------------

        response = await websocket.recv()

        print("\nServer:")
        print(response)

        # ---------------------------------------------------------
        # START AUDIO
        # ---------------------------------------------------------

        await websocket.send(
            "start_audio"
        )

        response = await websocket.recv()

        print("\nServer:")
        print(response)

        # ---------------------------------------------------------
        # SEND AUDIO CHUNKS
        #
        # These are dummy bytes for transport testing.
        # They are NOT real audio yet.
        # ---------------------------------------------------------

        for chunk_number in range(1, 6):

            fake_audio_chunk = bytes(
                [chunk_number] * 1024
            )

            print(
                f"\nClient: sending audio "
                f"chunk {chunk_number}"
            )

            await websocket.send(
                fake_audio_chunk
            )

            response = await websocket.recv()

            print("Server:")
            print(response)

            await asyncio.sleep(0.1)

        # ---------------------------------------------------------
        # STOP AUDIO
        # ---------------------------------------------------------

        await websocket.send(
            "stop_audio"
        )

        response = await websocket.recv()

        print("\nServer:")
        print(response)

    print("\nConnection closed.")

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(
        test_audio_stream()
    )
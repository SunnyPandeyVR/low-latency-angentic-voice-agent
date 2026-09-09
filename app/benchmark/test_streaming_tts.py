from app.services.groq_streaming import (
    GroqStreamingService,
)

from app.services.groq_tts import (
    GroqTTSService,
)


def main():

    llm_service = (
        GroqStreamingService()
    )

    tts_service = (
        GroqTTSService()
    )

    user_message = (
        "Tell me a short story about "
        "an AI assistant helping a customer."
    )

    print("=" * 70)
    print("STREAMING LLM → CHUNKING → TTS")
    print("=" * 70)

    result = (
        llm_service.stream_response(
            user_message
        )
    )

    print()
    print(
        f"LLM TTFT: "
        f"{result['ttft_ms']} ms"
    )

    print(
        f"LLM total: "
        f"{result['total_generation_ms']} ms"
    )

    print(
        f"Speech chunks: "
        f"{result['speech_chunk_count']}"
    )

    print()

    speech_chunks = (
        result["speech_chunks"]
    )

    for index, text in enumerate(
        speech_chunks,
        start=1,
    ):

        print("-" * 70)

        print(
            f"Chunk {index}"
        )

        print(
            f"Text: {text}"
        )

        filename = (
            f"chunk_{index}.wav"
        )

        tts_result = (
            tts_service.synthesize(
                text=text,
                output_filename=filename,
            )
        )

        print(
            f"TTS latency: "
            f"{tts_result['tts_latency_ms']} ms"
        )

        print(
            f"Audio: "
            f"{tts_result['audio_path']}"
        )

    print()
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
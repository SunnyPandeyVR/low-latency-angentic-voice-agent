from app.services.realtime_voice_pipeline import (
    RealtimeVoicePipeline,
)


def main():

    print()
    print("=" * 80)
    print("REAL-TIME VOICE AGENT BENCHMARK")
    print("=" * 80)

    pipeline = RealtimeVoicePipeline()

    result = pipeline.run(
        user_message=(
            "Explain what a low latency voice agent is "
            "in two short sentences."
        )
    )

    latency = result["latency"]

    print()
    print("=" * 80)
    print("FINAL BENCHMARK")
    print("=" * 80)

    print(
        f"TTFT               : "
        f"{latency['ttft_ms']} ms"
    )

    print(
        f"First chunk        : "
        f"{latency['first_chunk_ms']} ms"
    )

    print(
        f"First TTS latency  : "
        f"{latency['first_tts_latency_ms']} ms"
    )

    print(
        f"TTFA               : "
        f"{latency['ttfa_ms']} ms"
    )

    print(
        f"LLM generation     : "
        f"{latency['llm_generation_ms']} ms"
    )

    print(
        f"Total pipeline     : "
        f"{latency['total_ms']} ms"
    )

    print()
    print("Generated audio:")

    for audio in result["audio"]:

        print(
            f"  {audio['audio_path']}"
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
from app.services.voice_latency_pipeline import (
    VoiceLatencyPipeline,
)


def main():

    print()
    print("=" * 80)
    print("TIME-TO-FIRST-AUDIO BENCHMARK")
    print("=" * 80)

    pipeline = VoiceLatencyPipeline()

    result = pipeline.run(
        user_message=(
            "Explain what a low latency voice agent is "
            "in two short sentences."
        )
    )

    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    latency = result["latency"]

    print(
        f"TTFT             : "
        f"{latency['ttft_ms']} ms"
    )

    print(
        f"First chunk      : "
        f"{latency['first_chunk_ready_ms']} ms"
    )

    print(
        f"First TTS        : "
        f"{latency['first_tts_latency_ms']} ms"
    )

    print(
        f"TTFA             : "
        f"{latency['ttfa_ms']} ms"
    )

    print(
        f"Total pipeline   : "
        f"{latency['total_ms']} ms"
    )

    print()
    print("Generated audio files:")

    for audio in result["audio"]:
        print(
            f"  {audio['audio_path']}"
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
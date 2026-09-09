from app.services.groq_tts import (
    GroqTTSService,
)


def main():

    service = GroqTTSService()

    text = (
        "Hello. This is a latency optimized "
        "AI voice assistant."
    )

    print("=" * 70)
    print("GROQ TTS TEST")
    print("=" * 70)

    print(
        f"Model : {service.model}"
    )

    print(
        f"Voice : {service.voice}"
    )

    print()

    print(
        "Generating speech..."
    )

    result = service.synthesize(
        text=text,
        output_filename="test_tts.wav",
    )

    print()

    print("=" * 70)
    print("TTS RESULT")
    print("=" * 70)

    print(
        f"Status        : "
        f"{result['status']}"
    )

    print(
        f"Model         : "
        f"{result['model']}"
    )

    print(
        f"Voice         : "
        f"{result['voice']}"
    )

    print(
        f"Format        : "
        f"{result['audio_format']}"
    )

    print(
        f"Audio path    : "
        f"{result['audio_path']}"
    )

    print(
        f"Audio size    : "
        f"{result['audio_size_bytes']} bytes"
    )

    print(
        f"TTS latency   : "
        f"{result['tts_latency_ms']} ms"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
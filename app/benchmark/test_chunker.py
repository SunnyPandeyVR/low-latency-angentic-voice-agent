from app.services.response_chunker import (
    ResponseChunker,
)


def main():

    chunker = ResponseChunker(
        min_chunk_length=20,
        max_chunk_length=180,
    )

    simulated_stream = [
        "Sure, ",
        "I can ",
        "help you ",
        "with your ",
        "order. ",
        "Your order ",
        "is currently ",
        "being processed. ",
        "It should ",
        "arrive tomorrow.",
    ]

    print("=" * 70)
    print("RESPONSE CHUNKING TEST")
    print("=" * 70)

    for token in simulated_stream:

        print(
            f"\nLLM token: {token!r}"
        )

        chunks = chunker.add_text(
            token
        )

        for chunk in chunks:

            print(
                f"  >>> SPEECH CHUNK: "
                f"{chunk!r}"
            )

    remaining = chunker.flush()

    if remaining:

        print(
            f"  >>> FINAL CHUNK: "
            f"{remaining!r}"
        )

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
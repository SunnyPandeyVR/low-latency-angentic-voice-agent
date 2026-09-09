from typing import Optional


class ResponseChunker:
    """
    Converts a streaming LLM response into
    meaningful speech-ready chunks.

    The chunker does NOT perform TTS.

    Its only responsibility is deciding:
        "Is this text ready to be sent to TTS?"
    """

    def __init__(
        self,
        min_chunk_length: int = 20,
        max_chunk_length: int = 180,
    ):
        self.min_chunk_length = min_chunk_length
        self.max_chunk_length = max_chunk_length

        self.buffer = ""

    def add_text(
        self,
        text: str,
    ) -> list[str]:
        """
        Add newly received LLM text.

        Returns zero or more completed chunks.
        """

        if not text:
            return []

        self.buffer += text

        chunks = []

        while True:

            boundary = self._find_boundary()

            if boundary is None:
                break

            chunk = self.buffer[
                :boundary
            ].strip()

            self.buffer = self.buffer[
                boundary:
            ]

            if chunk:
                chunks.append(chunk)

        return chunks

    def flush(self) -> Optional[str]:
        """
        Return any remaining text after
        the LLM stream finishes.
        """

        remaining = self.buffer.strip()

        self.buffer = ""

        if not remaining:
            return None

        return remaining

    def _find_boundary(
        self,
    ) -> Optional[int]:
        """
        Find a natural place where speech
        can be split.
        """

        if not self.buffer:
            return None

        # -------------------------------------------------
        # 1. Prefer sentence boundaries
        # -------------------------------------------------

        sentence_endings = [
            ". ",
            "? ",
            "! ",
            ".\n",
            "?\n",
            "!\n",
        ]

        boundaries = []

        for ending in sentence_endings:

            position = self.buffer.find(
                ending
            )

            if position != -1:

                boundary = (
                    position
                    + len(ending)
                )

                if (
                    boundary
                    >= self.min_chunk_length
                ):
                    boundaries.append(
                        boundary
                    )

        if boundaries:
            return min(boundaries)

        # -------------------------------------------------
        # 2. If buffer is getting too large,
        #    split on a comma.
        # -------------------------------------------------

        if (
            len(self.buffer)
            >= self.max_chunk_length
        ):

            comma_position = (
                self.buffer.rfind(", ")
            )

            if (
                comma_position
                >= self.min_chunk_length
            ):
                return (
                    comma_position
                    + 2
                )

        # -------------------------------------------------
        # 3. Otherwise split at whitespace
        #    when maximum size is exceeded.
        # -------------------------------------------------

        if (
            len(self.buffer)
            >= self.max_chunk_length
        ):

            space_position = (
                self.buffer.rfind(
                    " ",
                    self.min_chunk_length,
                )
            )

            if space_position != -1:
                return space_position + 1

        return None
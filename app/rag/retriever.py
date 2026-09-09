import json
import re
from pathlib import Path


FAQ_FILE = Path(__file__).resolve().parents[2] / "data" / "faq.json"


def tokenize(text: str) -> set[str]:
    """
    Convert text into normalized tokens.
    """

    return set(
        re.findall(
            r"\b[a-zA-Z0-9]+\b",
            text.lower(),
        )
    )


def search_faq(query: str, top_k: int = 3) -> list[dict]:
    """
    Lightweight lexical retrieval.

    For the interview POC this gives us a transparent
    retrieval layer without introducing another remote
    service into the latency-critical path.
    """

    with open(FAQ_FILE, "r", encoding="utf-8") as file:
        documents = json.load(file)

    query_tokens = tokenize(query)

    scored_documents = []

    for document in documents:

        document_text = (
            document["question"]
            + " "
            + document["answer"]
        )

        document_tokens = tokenize(document_text)

        overlap = query_tokens.intersection(document_tokens)

        score = len(overlap)

        if score > 0:
            scored_documents.append(
                {
                    "question": document["question"],
                    "answer": document["answer"],
                    "score": score,
                }
            )

    scored_documents.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored_documents[:top_k]
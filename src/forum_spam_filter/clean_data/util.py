from typing import Sequence

LABEL_MAP = {
    "ham": 0,
    "spam": 1,
}


def chunk_greater_than_512(s: str, token_limit: int = 512) -> list[str]:
    tokens = s.split()
    return [
        " ".join(tokens[i : i + token_limit])
        for i in range(0, len(tokens), token_limit)
    ]


def chunk_greater_than_512_list(lst: Sequence[str], token_limit: int = 512) -> list[str]:
    res = []
    for s in lst:
        res.extend(chunk_greater_than_512(s, token_limit))
    return res

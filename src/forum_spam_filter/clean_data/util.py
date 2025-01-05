LABEL_MAP = {
    "ham": 0,
    "spam": 1,
}


def chunk_greater_than_512(l: list[str]) -> list[str]:
    res: list[str] = []
    for s in l:
        tokens = s.split()
        if len(tokens) > 512:
            res.extend(
                [" ".join(tokens[i : i + 512]) for i in range(0, len(tokens), 512)]
            )
        else:
            res.append(s)
    return res

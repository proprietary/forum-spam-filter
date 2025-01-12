"""
Load the Spam Assassin dataset.

See: https://spamassassin.apache.org/old/publiccorpus/
"""

import pandas as pd
import email
import email.message
import email.parser
from pathlib import Path
import tarfile
from typing import IO
from bs4 import BeautifulSoup
from .util import LABEL_MAP, chunk_greater_than_512_list

tarballs = [
    "20021010_easy_ham.tar.bz2",
    "20021010_hard_ham.tar.bz2",
    "20021010_spam.tar.bz2",
    "20030228_easy_ham.tar.bz2",
    "20030228_easy_ham_2.tar.bz2",
    "20030228_hard_ham.tar.bz2",
    "20030228_spam.tar.bz2",
    "20030228_spam_2.tar.bz2",
    "20050311_spam_2.tar.bz2",
]


def _safe_decode(bytes_content: str, encoding: str) -> str:
    try:
        return bytes_content.decode(encoding, errors="ignore")
    except LookupError:
        return bytes_content.decode("utf-8", errors="ignore")


def parse_email(f: IO[bytes]) -> str:
    msg = email.parser.BytesParser().parse(f)

    def extract_text(part: email.message.Message) -> str:
        content_type = part.get_content_type()
        content_disposition = str(part.get("Content-Disposition") or "")
        if "attachment" in content_disposition:
            return ""
        content = part.get_payload(decode=True) or b""
        if content_type == "text/plain":
            return _safe_decode(content, part.get_content_charset() or "utf-8")
        if content_type == "text/html":
            decoded_html = _safe_decode(content, part.get_content_charset() or "utf-8")
            soup = BeautifulSoup(decoded_html, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        return ""

    if msg.is_multipart():
        parts_text = []
        for part in msg.walk():
            part_text = extract_text(part)
            if part_text:
                parts_text.append(part_text)
        body = "\n".join(parts_text)
    else:
        payload = msg.get_payload(decode=True) or b""
        assert payload is not None
        assert isinstance(payload, bytes)
        body = _safe_decode(payload, msg.get_content_charset() or "utf-8")
    body = body.strip()
    return body


def load_spam_assassin() -> pd.DataFrame:
    ham: list[str] = []
    spam: list[str] = []
    for tb in tarballs:
        p = Path(__file__).parent / "datasets" / "spamassassin-public-corpus" / tb
        with tarfile.open(p, mode="r:bz2") as tar:
            for member in tar.getmembers():
                if member.isfile():
                    f = tar.extractfile(member)
                    if f is None:
                        continue
                    body = parse_email(f)
                    if "spam" in member.name:
                        spam.append(body)
                    else:
                        ham.append(body)
    ham = chunk_greater_than_512_list(ham)
    spam = chunk_greater_than_512_list(spam)
    return pd.DataFrame(
        {
            "text": ham + spam,
            "label": [LABEL_MAP["ham"]] * len(ham) + [LABEL_MAP["spam"]] * len(spam),
        }
    )

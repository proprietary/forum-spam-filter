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
from .util import LABEL_MAP, chunk_greater_than_512

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


def parse_email(f: IO[bytes]) -> str:
    msg = email.parser.BytesParser().parse(f)
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            content = part.get_payload(decode=True)
            if content_type == "text/plain" and "attachment" not in content_disposition:
                assert isinstance(content, bytes)
                encoding = part.get_content_charset()
                body += content.decode(encoding or "utf-8", errors="ignore")
            elif (
                content_type == "text/html" and "attachment" not in content_disposition
            ):
                assert isinstance(content, bytes)
                soup = BeautifulSoup(content, "html.parser")
                body += soup.get_text()
    else:
        payload = msg.get_payload(decode=True)
        assert payload is not None
        assert isinstance(payload, bytes)
        soup = BeautifulSoup(payload, "html.parser")
        body = soup.get_text()
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
    ham = chunk_greater_than_512(ham)
    spam = chunk_greater_than_512(spam)
    return pd.DataFrame(
        {
            "text": ham + spam,
            "label": [LABEL_MAP["ham"]] * len(ham) + [LABEL_MAP["spam"]] * len(spam),
        }
    )

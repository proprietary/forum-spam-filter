"""
CSDMC2010 SPAM corpus, which is one of the datasets for
the data mining competition associated with ICONIP 2010.

See: https://web.archive.org/web/20170623023845/https://csmining.org/index.php/spam-email-datasets-.html
"""

from .spam_assassin import parse_email
import pandas as pd
import zipfile
from .util import LABEL_MAP, chunk_greater_than_512_list
from pathlib import Path


def load_csdmc2010_corpus() -> pd.DataFrame:
    ham: list[str] = []
    spam: list[str] = []
    p = Path(__file__).parent / "datasets" / "CSDMC2010_SPAM.zip"
    prefix = "CSDMC2010_SPAM/CSDMC2010_SPAM"
    with zipfile.ZipFile(p) as z:
        with z.open(f"{prefix}/SPAMTrain.label", "r") as f:
            labels: dict[str, str] = {}
            for line in f:
                line = line.decode("utf-8")
                label, filename = line.strip().split(" ")
                labels[filename] = "spam" if label == "0" else "ham"
        for email_filename in labels.keys():
            label = labels[email_filename]
            with z.open(
                f"{prefix}/TRAINING/{email_filename}"
                if email_filename.startswith("TRAIN")
                else f"{prefix}/TESTING/{email_filename}"
            ) as f:
                body = parse_email(f)
                if label == "spam":
                    spam.append(body)
                elif label == "ham":
                    ham.append(body)
                else:
                    raise ValueError(f"Unexpected label: {label}")
    ham = chunk_greater_than_512_list(ham)
    spam = chunk_greater_than_512_list(spam)
    return pd.DataFrame(
        {
            "text": ham + spam,
            "label": [LABEL_MAP["ham"]] * len(ham) + [LABEL_MAP["spam"]] * len(spam),
        }
    )

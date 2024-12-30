import pandas as pd
from pathlib import Path

LABEL_MAP = {
    "ham": 0,
    "spam": 1,
}


def load_sms_spam_collection() -> pd.DataFrame:
    """
    Load the SMS Spam Collection dataset.

    See: https://archive.ics.uci.edu/dataset/228/sms+spam+collection
    """
    path = Path(__file__).parent / "datasets" / "SMSSpamCollection.tsv"
    df = pd.read_csv(path, sep="\t", header=None, names=["label", "text"])
    df["label"] = df["label"].map(lambda x: LABEL_MAP[x])
    return df


def load_spam_assassin():
    """
    Load the Spam Assassin dataset.

    See: https://spamassassin.apache.org/old/publiccorpus/
    """
    raise NotImplementedError


def load_enron_spam():
    """
    Load the Enron Spam dataset.

    See: https://www.cs.cmu.edu/~enron/
    """
    raise NotImplementedError


def load_datasets() -> pd.DataFrame:
    return pd.concat(
        [
            load_sms_spam_collection(),
        ]
    )

import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from .spam_assassin import load_spam_assassin
from .private_dataset import load_private_dataset
from .csdmc2010 import load_csdmc2010_corpus
from .util import LABEL_MAP


def load_sms_spam_collection() -> pd.DataFrame:
    """
    Load the SMS Spam Collection dataset.

    See: https://archive.ics.uci.edu/dataset/228/sms+spam+collection
    """
    path = Path(__file__).parent / "datasets" / "SMSSpamCollection.tsv"
    df = pd.read_csv(path, sep="\t", header=None, names=["label", "text"])
    df["label"] = df["label"].map(lambda x: LABEL_MAP[x])
    return df


def load_enron_spam():
    """
    Load the Enron Spam dataset.

    See: https://www.cs.cmu.edu/~enron/
    """
    raise NotImplementedError


def load_datasets() -> pd.DataFrame:
    with ProcessPoolExecutor() as pool:
        f1 = pool.submit(load_sms_spam_collection)
        f2 = pool.submit(load_spam_assassin)
        f3 = pool.submit(load_csdmc2010_corpus)
        f4 = pool.submit(load_private_dataset)
        datasets = [f1.result(), f2.result(), f3.result()]
        if f4.result() is not None and f4.exception() is None:
            datasets.append(f4.result())
    df = pd.concat(datasets, ignore_index=True)
    df = df.sample(frac=1).reset_index(drop=True)
    return df

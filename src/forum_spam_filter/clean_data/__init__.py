import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from .spam_assassin import load_spam_assassin
from .private_dataset import load_private_dataset
from .csdmc2010 import load_csdmc2010_corpus
from .trec_public_corpus import load_trec_dataset
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
        futs = [
            pool.submit(t)
            for t in [
                load_sms_spam_collection,
                load_spam_assassin,
                load_csdmc2010_corpus,
                load_trec_dataset,
            ]
        ]
        f5 = pool.submit(load_private_dataset)
        datasets = [f.result() for f in futs]
        if f5.result() is not None and f5.exception() is None:
            datasets.append(f5.result())
    df = pd.concat(datasets, ignore_index=True)
    df = df.sample(frac=1).reset_index(drop=True)
    return df

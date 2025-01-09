from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from .util import chunk_greater_than_512


def clean_text(s: str) -> str:
    return BeautifulSoup(s, "html.parser").get_text()


def load_private_dataset() -> pd.DataFrame:
    p = Path(__file__).parent / "datasets" / "private.csv"
    df = pd.read_csv(p, sep=",", header=None, names=["text", "label"])
    df["text"] = df["text"].map(clean_text)
    # Split text into chunks of 512 tokens
    df["text_chunks"] = df["text"].apply(chunk_greater_than_512)
    df = df.explode("text_chunks", ignore_index=True)
    df = df.drop(columns=["text"])
    df = df.rename(columns={"text_chunks": "text"})
    df = df.sample(frac=1).reset_index(drop=True)  # shuffle
    return df

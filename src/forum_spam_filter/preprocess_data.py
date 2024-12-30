import pandas as pd
from sklearn.model_selection import train_test_split
from datasets import Dataset
from transformers import DistilBertTokenizer
from .model import checkpoint


def preprocess_data(df: pd.DataFrame):
    tokenizer = DistilBertTokenizer.from_pretrained(checkpoint)

    def tokenize_function(example):
        return tokenizer(
            example["text"], padding="max_length", truncation=True, max_length=512
        )

    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["label"]
    )
    train_dataset, test_dataset = (
        Dataset.from_pandas(train_df),
        Dataset.from_pandas(test_df),
    )
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    test_dataset = test_dataset.map(tokenize_function, batched=True)
    train_dataset.set_format(
        type="torch", columns=["input_ids", "attention_mask", "label"]
    )
    test_dataset.set_format(
        type="torch", columns=["input_ids", "attention_mask", "label"]
    )

    return train_dataset, test_dataset, tokenizer

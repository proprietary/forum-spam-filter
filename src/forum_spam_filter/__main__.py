from .clean_data import load_datasets
from .preprocess_data import preprocess_data
from .train import train
from .export_model import export_model
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%m-%d %H:%M:%S%z")


def main():
    df = load_datasets()
    train_dataset, test_dataset, tokenizer = preprocess_data(df)
    train(train_dataset, test_dataset, Path.cwd() / "results" / "model")
    export_model(
        Path.cwd() / "results" / "model",
        tokenizer,
        Path.cwd() / "results" / "onnx",
    )


if __name__ == "__main__":
    main()

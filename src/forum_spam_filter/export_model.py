from optimum.onnxruntime import ORTModelForSequenceClassification
from pathlib import Path


def export_model(checkpoint: Path, tokenizer, dest_dir: Path):
    ort_model = ORTModelForSequenceClassification.from_pretrained(
        checkpoint, export=True
    )
    ort_model.save_pretrained(dest_dir)
    tokenizer.save_pretrained(dest_dir)

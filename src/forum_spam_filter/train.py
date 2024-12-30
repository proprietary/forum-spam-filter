from pathlib import Path
import numpy as np
from transformers import DistilBertForSequenceClassification, Trainer, TrainingArguments
from .model import checkpoint
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    warmup_steps=500,
    weight_decay=5e-4,
    eval_strategy="epoch",
    logging_dir="./logs",
    logging_steps=10,
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
)


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary"
    )
    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def train(train_dataset, test_dataset, output_dir: Path):
    model = DistilBertForSequenceClassification.from_pretrained(
        checkpoint, num_labels=2
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )
    trainer.train()
    trainer.evaluate()
    model.save_pretrained(output_dir)

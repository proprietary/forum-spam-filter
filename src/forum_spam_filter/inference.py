import sys
import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
from pathlib import Path

onnx_path = Path.cwd() / "results" / "onnx"

if not onnx_path.exists():
    raise FileNotFoundError(f"Model not found at {onnx_path}")


if __name__ == "__main__":
    text = sys.argv[1]
    tokenizer = AutoTokenizer.from_pretrained(onnx_path)
    ort_model = ort.InferenceSession(onnx_path / "model.onnx")
    inputs = tokenizer(text, return_tensors="pt")
    onnx_inputs = {key: inputs[key].cpu().numpy() for key in inputs}
    onnx_outputs = ort_model.run(None, onnx_inputs)
    logit = np.argmax(onnx_outputs[0], axis=-1)[0]
    res = {0: "ham", 1: "spam"}[logit]
    print(res)

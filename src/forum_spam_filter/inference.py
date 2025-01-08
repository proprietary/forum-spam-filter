import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
from pathlib import Path
import argparse

onnx_path = Path.cwd() / "results" / "onnx_quantized" / "model_quantized.onnx"

if not onnx_path.exists():
    raise FileNotFoundError(f"Model not found at {onnx_path}")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("text", type=str, help="Text to classify")
    arg_parser.add_argument(
        "--model", type=str, help="Path to ONNX model", default=onnx_path
    )
    args = arg_parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(onnx_path.parent)
    ort_model = ort.InferenceSession(onnx_path)
    inputs = tokenizer(args.text, return_tensors="pt")
    onnx_inputs = {key: inputs[key].cpu().numpy() for key in inputs}
    onnx_outputs = ort_model.run(None, onnx_inputs)
    softmax = np.exp(onnx_outputs[0]) / np.sum(np.exp(onnx_outputs[0]), axis=-1)
    print(f"Ham: {softmax[0][0]*100.:.2f}%, Spam: {softmax[0][1]*100.:.2f}%")
    logit = np.argmax(onnx_outputs[0], axis=-1)[0]
    res = {0: "ham", 1: "spam"}[logit]
    print(res)

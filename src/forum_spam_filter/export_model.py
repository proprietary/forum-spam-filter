from optimum.onnxruntime import ORTModelForSequenceClassification, ORTQuantizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig
from pathlib import Path


def export_model(checkpoint: Path, tokenizer, dest_dir: Path):
    ort_model = ORTModelForSequenceClassification.from_pretrained(
        checkpoint, export=True
    )
    ort_model.save_pretrained(dest_dir)
    tokenizer.save_pretrained(dest_dir)
    quantizer = ORTQuantizer.from_pretrained(dest_dir)
    dqconfig = AutoQuantizationConfig.arm64(is_static=False, per_channel=False)
    quantizer.quantize(
        quantization_config=dqconfig,
        save_dir=(dest_dir.parent / (dest_dir.name + "_quantized")).as_posix(),
    )

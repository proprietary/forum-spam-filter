use ndarray::{Array1, Array2, ArrayView2};
use ort::{session::Session, value::Tensor};
use std::path::PathBuf;
use tokenizers::{Encoding, Tokenizer};

tonic::include_proto!("forum_spam_filter");

static DISTILBERT_BASE_TOKENIZER: &[u8] =
    include_bytes!("../resources/distilbert-base-uncased/tokenizer.json");

#[derive(Debug)]
pub struct SpamTextClassifier {
    tokenizer: Tokenizer,
    session: Session,
}

impl Default for SpamTextClassifier {
    fn default() -> Self {
        let tokenizer =
            Tokenizer::from_bytes(DISTILBERT_BASE_TOKENIZER).expect("Failed to load tokenizer");
        ort::init()
            .with_name("forum_spam_filter")
            .with_telemetry(false)
            .commit()
            .expect("Failed to initialize ONNX runtime");
        let model_path = std::env::var("MODEL_PATH").expect("MODEL_PATH not set");
        let model_path = PathBuf::from(model_path);
        let session = Session::builder()
            .expect("Failed to create session builder")
            .commit_from_file(model_path)
            .expect("Failed to load model");
        Self { tokenizer, session }
    }
}

impl SpamTextClassifier {
    fn encode_text(
        &self,
        s: &str,
    ) -> Result<(Array2<i64>, Array2<i64>), Box<dyn std::error::Error + Send + Sync>> {
        const MAX_LEN: usize = 512;
        let encoding: Encoding = self.tokenizer.encode(s, true)?;
        let num_chunks = (encoding.len() + MAX_LEN - 1) / MAX_LEN;
        let mut input_ids = Array2::<i64>::zeros((num_chunks, MAX_LEN));
        let mut attention_mask = Array2::<i64>::zeros((num_chunks, MAX_LEN));
        for (chunk_idx, chunk) in encoding.get_ids().chunks(MAX_LEN).enumerate() {
            for (token_idx, &token) in chunk.iter().enumerate() {
                input_ids[[chunk_idx, token_idx]] = token as i64;
            }
        }
        for (chunk_idx, chunk) in encoding.get_attention_mask().chunks(MAX_LEN).enumerate() {
            for (token_idx, &mask_value) in chunk.iter().enumerate() {
                attention_mask[[chunk_idx, token_idx]] = mask_value as i64;
            }
        }
        Ok((input_ids, attention_mask))
    }

    pub fn is_spam(&self, s: &str) -> Result<f32, Box<dyn std::error::Error + Send + Sync>> {
        let (a_ids, a_mask) = self.encode_text(s)?;
        let a_ids = Tensor::from_array(a_ids)?;
        let a_mask = Tensor::from_array(a_mask)?;
        let outputs = self
            .session
            .run(vec![("input_ids", a_ids), ("attention_mask", a_mask)])?;
        let output = outputs[0]
            .try_extract_tensor::<f32>()?
            .into_dimensionality::<ndarray::Ix2>()?;
        let probs = probabilities(output);
        return Ok(probs[1]);
    }
}

fn softmax(logits: &Array1<f32>) -> Array1<f32> {
    let max_logit = logits.fold(f32::NEG_INFINITY, |a, &b| a.max(b));
    let exp_logits = logits.map(|&x| (x - max_logit).exp());
    let sum_exp = exp_logits.sum();
    exp_logits.mapv(|x| x / sum_exp)
}

fn mean_logits(logits: ArrayView2<f32>) -> Array1<f32> {
    logits
        .mean_axis(ndarray::Axis(0))
        .expect("Failed to compute mean logits")
}

fn probabilities(logits: ArrayView2<f32>) -> Array1<f32> {
    let mean_logits = mean_logits(logits);
    softmax(&mean_logits)
}

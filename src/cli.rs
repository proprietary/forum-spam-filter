use forum_spam_filter::SpamTextClassifier;
use std::io::Read;
use std::sync::Arc;

fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let mut input = Vec::new();
    let stdin = std::io::stdin();
    let mut handle = stdin.lock();
    handle.read_to_end(&mut input)?;
    let input_text = String::from_utf8(input)?;

    let classifier = Arc::new(SpamTextClassifier::default());
    let result = classifier.is_spam(&input_text)?;
    eprintln!("Spam: {:.2}%", result * 100.0);
    eprintln!(
        "Predicted Class: {:?}",
        if result > 0.5 { "Spam" } else { "Ham" }
    );

    Ok(())
}

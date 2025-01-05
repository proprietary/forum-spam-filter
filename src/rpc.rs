use forum_spam_filter::{
    spam_classification_server::{SpamClassification, SpamClassificationServer},
    MaybeSpam, SpamOrHam, SpamTextClassifier,
};
use std::sync::Arc;
use std::sync::Mutex;
use tonic::{transport::Server, Request, Response, Status};

#[derive(Debug, Default, Clone)]
pub struct MySpamClassificationService(Arc<Mutex<SpamTextClassifier>>);

#[tonic::async_trait]
impl SpamClassification for MySpamClassificationService {
    async fn classify(&self, request: Request<MaybeSpam>) -> Result<Response<SpamOrHam>, Status> {
        let text = request.into_inner().text;
        let classifier = self.0.lock().map_err(|e| Status::internal(e.to_string()))?;
        let probability = classifier.is_spam(&text).map_err(|e| {
            tracing::error!("Failed to classify text: {}", e);
            Status::internal(e.to_string())
        })?;
        let reply = SpamOrHam { probability };
        Ok(Response::new(reply))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    let grpc_port = std::env::var("GRPC_PORT").unwrap_or_else(|_| {
        tracing::warn!("GRPC_PORT not set, defaulting to 60066");
        "60066".to_string()
    });
    let addr = format!("[::]:{}", grpc_port).parse()?;
    let classifier = SpamTextClassifier::default();
    let svc = MySpamClassificationService(Arc::new(Mutex::new(classifier)));
    tracing::info!("Listening on [::]:{}", grpc_port);
    Server::builder()
        .add_service(SpamClassificationServer::new(svc))
        .serve(addr)
        .await?;
    Ok(())
}

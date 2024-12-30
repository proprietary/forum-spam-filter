# DistilBERT model for detecting spam messages

This trains and runs a DistilBERT model to classify text as spam. The
use case is to develop a plugin to stop spam in forums or blog
comments.

Work in Progress

## Architecture

```mermaid
graph TD
    subgraph ML Pipeline
        A[Clean Data from Public & Private Sources]
        B[Train Base DistilBERT Model with PyTorch]
        C[Export Model as ONNX]
        A --> B --> C
    end
    
    subgraph Inference Application
        D[Load ONNX Model]
        E[Load Tokenizer Config]
        F[Expose gRPC Service for Inference]
        G[Run as Persistent System Process]
        D --> E --> F --> G
    end
    
    subgraph PHP Plugin
        H[Listen for New Comments from Suspicious Users]
        I[Call Inference App over gRPC]
        J[Accept or Reject Comment]
        H --> I --> J
    end

    C --> D
    I --> F
```

FROM rust:1.83.0-bookworm AS builder

ARG ONNX_RUNTIME_AARCH64="https://github.com/microsoft/onnxruntime/releases/download/v1.20.1/onnxruntime-linux-aarch64-1.20.1.tgz"
ARG ONNX_RUNTIME_X86_64="https://github.com/microsoft/onnxruntime/releases/download/v1.20.1/onnxruntime-linux-x64-1.20.1.tgz"

WORKDIR /usr/src/app

RUN apt update && \
    apt install -y \
    curl \
    cmake \
    build-essential \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Download and extract onnxruntime
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then \
        DOWNLOAD_URL=$ONNX_RUNTIME_AARCH64; \
    elif [ "$ARCH" = "x86_64" ]; then \
        DOWNLOAD_URL=$ONNX_RUNTIME_X86_64; \
    else \
        echo "Unsupported architecture"; \
        exit 1; \
    fi && \
    mkdir ./onnxruntime && \
    curl -L $DOWNLOAD_URL \
      | tar -xz --strip-components=1 -C ./onnxruntime

COPY Cargo.toml ./Cargo.toml
COPY Cargo.lock ./Cargo.lock
RUN cargo fetch

COPY resources ./resources
COPY proto ./proto
COPY src ./src
COPY build.rs ./build.rs

RUN cargo build --release


FROM debian:bookworm-slim

WORKDIR /usr/src/app

COPY --from=builder /usr/src/app/target/release/rpc .
COPY --from=builder /usr/src/app/onnxruntime ./onnxruntime

COPY ./results/onnx_quantized/model_quantized.onnx ./model.onnx

ENV ORT_DYLIB_PATH=/usr/src/app/onnxruntime/lib/libonnxruntime.so
ENV MODEL_PATH=/usr/src/app/model.onnx
ENV GRPC_PORT=60066

EXPOSE 60066

CMD ["./rpc"]

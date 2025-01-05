FROM rust:1.83.0-bookworm AS builder

WORKDIR /usr/src/app

COPY Cargo.toml ./Cargo.toml
COPY Cargo.lock ./Cargo.lock
RUN cargo fetch

RUN apt update && apt install -y protobuf-compiler

COPY resources ./resources
COPY proto ./proto
COPY src ./src
COPY build.rs ./build.rs

RUN cargo build --release


FROM debian:bookworm-slim

WORKDIR /usr/src/app

COPY --from=builder /usr/src/app/target/release/rpc .

COPY ./results/onnx_quantized/model_quantized.onnx ./model.onnx

ENV MODEL_PATH=/usr/src/app/model.onnx
ENV GRPC_PORT=60066

EXPOSE 60066

CMD ["./rpc"]

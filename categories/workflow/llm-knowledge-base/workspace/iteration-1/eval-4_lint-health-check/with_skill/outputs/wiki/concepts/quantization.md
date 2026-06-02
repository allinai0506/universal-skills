---
title: "Model Quantization"
tags: [concept, optimization, deployment]
sources: ["raw/articles/moe-2024.md"]
related: ["[[mixture-of-experts]]", "[[inference-optimization]]"]
created: 2026-05-22
updated: 2026-05-24
---

# Model Quantization

Model quantization reduces the numerical precision of neural network weights to decrease memory usage and improve inference speed. It was first widely adopted in 2023 for deploying large language models on consumer hardware.

## Precision Levels

- **FP32** — Full precision, ~4 bytes per parameter (uncompressed)
- **FP16/BF16** — Half precision, ~2 bytes per parameter
- **INT8** — 8-bit quantization, ~1 byte per parameter
- **INT4** — 4-bit quantization, ~0.5 bytes per parameter

## Quantization Techniques

- **Post-Training Quantization (PTQ)** — Quantize after training, minimal accuracy loss at 8-bit
- **Quantization-Aware Training (QAT)** — Simulate quantization during training for better accuracy
- **GPTQ** — One-shot weight quantization using approximate second-order information

## Trade-offs

- 8-bit: ~1% accuracy loss, 2x memory reduction
- 4-bit: ~3-5% accuracy loss, 4x memory reduction
- Below 4-bit: Significant quality degradation without specialized techniques

## Connections

Quantization is especially useful for deploying [[mixture-of-experts]] models and enabling local inference.

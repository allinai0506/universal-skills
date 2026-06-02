---
title: "LLM Scaling Laws"
tags: [article, scaling, llm]
sources: ["raw/articles/moe-2024.md"]
related: ["[[transformer-architecture]]"]
created: 2026-05-10
updated: 2026-05-10
---

# LLM Scaling Laws

Scaling laws describe how model performance improves as a function of model size, dataset size, and compute budget.

## Kaplan Scaling Laws (2020)

- Model performance follows a power-law relationship with model size, data size, and compute
- Larger models are more sample-efficient than smaller models
- Compute-optimal training: given 10x more compute, use a 5.5x larger model and 1.8x more data

## Chinchilla Scaling Laws (2022)

- DeepMind found that Kaplan et al. overestimated the optimal model size
- For compute-optimal training, model size and data size should scale roughly equally
- Most existing LLMs were undertrained — they should have used more data and smaller models

## Practical Implications

- Current best practice: 20x more tokens than parameters (the "Chinchilla ratio")
- Scaling data is often more important than scaling model size
- The era of "bigger models but less data" is over

## Future Directions

- **Sparse scaling** — MoE models may follow different scaling laws
- **Data quality** — Scaling laws may change with data filtering and curation
- **Multimodal scaling** — Additional modalities change the scaling dynamics

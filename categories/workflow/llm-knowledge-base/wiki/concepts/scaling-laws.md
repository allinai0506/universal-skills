---
title: "Scaling Laws"
tags: [concept, scaling, theory, compute]
related: [["Chinchilla Scaling"]]
created: 2026-06-02
updated: 2026-06-02
---

# Scaling Laws

Scaling laws describe the empirical relationship between model size, dataset size, and compute budget for neural language models. They were systematically characterized by Kaplan et al. (2020) and later refined by Hoffmann et al. (2022, "Chinchilla").

## Key Findings

- Model performance follows a power-law relationship with compute, model size, and data size
- The Chinchilla scaling laws showed that most models were undertrained — for optimal performance, model size and training tokens should scale proportionally
- MoE architectures may exhibit different scaling behavior than dense models

## Relevance to MoE

MoE models challenge traditional scaling laws because they decouple total parameters from compute per token. This means the "effective parameter count" for scaling law purposes is the active parameter count, not the total.

## Related

See [[MoE Scaling Properties]] for a more detailed treatment of how scaling laws apply to sparse models.

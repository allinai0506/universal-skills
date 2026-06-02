---
title: "Soft MoE"
tags: [concept, moe, routing, google, 2023]
sources: ["raw/articles/moe-2024.md"]
related: ["[[Mixture of Experts]]", "[[Expert Routing]]", "[[Mixture of Experts 2024]]"]
created: 2026-06-02
updated: 2026-06-02
---

# Soft MoE

## Definition

Soft MoE is a 2023 Google approach to Mixture of Experts that replaces discrete token-to-expert routing with soft, weighted assignments. Instead of routing each token to a specific expert, each token becomes a weighted combination of all experts' outputs.

## Key Innovation

The core insight is that discrete routing introduces several problems:
- **Load imbalance**: Some experts get more tokens than others
- **Poor gradient flow**: The discrete selection is non-differentiable
- **Expert collapse**: Unused experts stop receiving training signal

Soft MoE eliminates these issues by making every expert contribute to every token, with learned weights determining the contribution strength.

## Advantages

- Eliminates the load balancing loss entirely
- Better gradient flow through soft assignments
- No expert collapse (all experts always receive signal)
- Competitive quality with hard-routing MoE

## Tradeoffs

- All expert weights must participate in computation (though the weighted combination can be efficient)
- May not achieve the same extreme sparsity ratios as hard routing
- Theoretical maximum efficiency gain is lower because all experts compute something

## Connections

- Contrasts with hard routing approaches used in [[Mixture of Experts]] like Switch Transformer and Mixtral
- The 2024 Google breakthrough ([[Mixture of Experts 2024]]) uses a different approach — dynamic selection — that is neither purely hard nor purely soft routing
- Represents a fundamentally different philosophy: "let every expert contribute" vs. "pick the best expert(s)"

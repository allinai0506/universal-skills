---
title: "MoE Innovation Timeline (2022-2024)"
tags: [connection, timeline, MoE]
sources:
  - "raw/articles/moe-2024.md"
related:
  - "[[Mixture of Experts: Scaling Transformer Models Beyond Dense Limits]]"
created: 2026-06-02
updated: 2026-06-02
---

# MoE Innovation Timeline (2022-2024)

## Progression Overview

The evolution of Mixture of Experts follows a clear trajectory toward **greater sparsity** and **smarter routing**:

```
2022 ──────────────────────────────────────────────► 2024
                                                   
Switch Transformer (Google)                          
  top-1 hard routing                                  
  7x pretraining speedup                              
                                                   
DeepSpeed-MoE (Microsoft)                            
  hierarchical experts                                
  3x speedup                                         
                                                   
       Soft MoE (Google)                             
         soft assignment                              
         no load balancing loss                       
                                                   
           Mixtral 8x7B (Mistral)                    
             46.7B params, 12.9B active              
             matches Llama 2 70B                     
                                                   
                  Google 2024 MoE                    
                    ~10% active params                
                    3x sparse activation              
```

## Key Themes

1. **Routing sophistication**: From simple top-1 to soft assignment to dynamic compatibility scoring — each generation improves how tokens find experts.
2. **Sparsity increases**: Active parameter ratio drops from ~30% to ~10% over two years.
3. **Quality maintained**: Each sparsity increase comes with techniques (specialization pressure, staged training) to preserve output quality.

## Open Directions

- Combining soft routing with extreme sparsity.
- Better fine-tuning methods for sparse MoE models.
- Serving infrastructure that can handle large total parameter counts efficiently.

| model | IFEval prompt-strict | IFEval inst-strict | IFEval strict avg | Greek MGSM |
|---|---|---|---|---|
| Llama-Krikri-8B-Instruct (ILSP card: 67.5%) | 0.614 | 0.723 | **66.8%** | 0.676 |
| Apertus-8B-Instruct-2509 (no Greek CPT) | 0.505 | 0.615 | **56.0%** | 0.532 |
| Gemma-3-12B-it (50% larger) | 0.675 | 0.763 | **71.9%** | 0.908 |
| Meltemi-7B-Instruct-v1.5 (ILSP card: 32.7%) | 0.277 | 0.375 | **32.6%** | 0.208 |
| ours: lr 1e-5, epoch 3 | 0.512 | 0.612 | **56.2%** | 0.392 |
| ours: adapted imports, epoch 2 | 0.497 | 0.601 | **54.9%** | 0.384 |
| ours: lr 5e-6, epoch 3 | 0.486 | 0.584 | **53.5%** | 0.416 |
| ours: the pick, lr 1e-5, epoch 2 | 0.479 | 0.586 | **53.3%** | 0.400 |
| ours: paired English, epoch 2 | 0.473 | 0.568 | **52.1%** | 0.404 |
| ours: raw imports, epoch 2 | 0.470 | 0.579 | **52.4%** | 0.408 |
| ours: from the terminal CPT checkpoint | 0.429 | 0.540 | **48.4%** | 0.328 |

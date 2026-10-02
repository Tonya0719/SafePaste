# SafePaste V2 Product-Scope Mapping Results

Mapping: `safepaste-label-mapping-v2-product-scope`.

These tables re-score the saved V1 prediction files with the V2 product-scope label mapping. They do not replace the official V1 frozen benchmark results and do not rerun detectors.

## AI4Privacy Frozen Re-Scored With V2 Mapping

| System | Records | Gold | Pred. | Exact typed R | Exact protective R | Overlap typed R | Overlap protective R | Exact typed P | Overlap typed P | Abstention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Presidio-only | 3000 | 8268 | 3313 | 27.47% | 27.52% | 29.06% | 29.14% | 68.55% | 72.53% | 0.00% |
| GLiNER-only | 3000 | 8268 | 8523 | 20.55% | 24.73% | 31.02% | 40.00% | 23.34% | 35.24% | 14.61% |
| Hybrid | 3000 | 8268 | 11467 | 47.86% | 51.26% | 59.91% | 65.14% | 38.36% | 48.02% | 10.05% |

## Singapore Stress Re-Scored With V2 Mapping

| System | Records | Gold | Pred. | Exact typed R | Exact protective R | Overlap typed R | Overlap protective R | Exact typed P | Overlap typed P | Abstention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Presidio-only | 30 | 53 | 38 | 43.40% | 43.40% | 60.38% | 60.38% | 60.53% | 84.21% | 0.00% |
| GLiNER-only | 30 | 53 | 39 | 50.94% | 54.72% | 50.94% | 56.60% | 72.97% | 72.97% | 5.13% |
| Hybrid | 30 | 53 | 61 | 92.45% | 94.34% | 94.34% | 96.23% | 81.67% | 83.33% | 1.64% |

## Hybrid Per-Label Results: AI4Privacy Frozen, V2 Mapping

| Label | Gold | Exact typed R | Overlap typed R | Overlap protective R | Exact typed P | Overlap typed P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ADDRESS | 2869 | 15.44% | 26.32% | 30.85% | 51.75% | 88.20% |
| EMAIL | 1092 | 98.90% | 99.54% | 99.54% | 94.74% | 95.35% |
| IP_ADDRESS | 980 | 96.73% | 97.86% | 97.86% | 97.23% | 98.36% |
| PERSON | 2560 | 49.02% | 70.66% | 73.32% | 28.32% | 40.83% |
| PHONE | 767 | 30.12% | 44.72% | 44.72% | 20.14% | 29.90% |

## Hybrid Per-Label Results: Singapore Stress, V2 Mapping

| Label | Gold | Exact typed R | Overlap typed R | Overlap protective R | Exact typed P | Overlap typed P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ADDRESS | 11 | 90.91% | 100.00% | 100.00% | 83.33% | 91.67% |
| EMAIL | 7 | 85.71% | 85.71% | 85.71% | 100.00% | 100.00% |
| GOVERNMENT_ID | 5 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| PERSON | 18 | 100.00% | 100.00% | 100.00% | 66.67% | 66.67% |
| PHONE | 12 | 83.33% | 83.33% | 83.33% | 100.00% | 100.00% |

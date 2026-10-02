# SafePaste Report Tables

## AI4Privacy Frozen Evaluation

| System | Records | Gold | Pred. | Exact typed R | Exact protective R | Overlap typed R | Overlap protective R | Exact typed P | Overlap typed P | Abstention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Presidio-only | 3000 | 14685 | 3313 | 15.46% | 19.74% | 16.36% | 21.85% | 68.55% | 72.53% | 0.00% |
| GLiNER-only | 3000 | 14685 | 8523 | 11.60% | 17.98% | 17.59% | 28.04% | 23.41% | 35.49% | 14.61% |
| Hybrid | 3000 | 14685 | 11467 | 26.98% | 37.03% | 33.85% | 47.44% | 38.41% | 48.19% | 10.05% |

## Singapore Stress Set

| System | Records | Gold | Pred. | Exact typed R | Exact protective R | Overlap typed R | Overlap protective R | Exact typed P | Overlap typed P | Abstention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Presidio-only | 30 | 53 | 38 | 43.40% | 43.40% | 60.38% | 60.38% | 60.53% | 84.21% | 0.00% |
| GLiNER-only | 30 | 53 | 39 | 50.94% | 54.72% | 50.94% | 56.60% | 72.97% | 72.97% | 5.13% |
| Hybrid | 30 | 53 | 61 | 92.45% | 94.34% | 94.34% | 96.23% | 81.67% | 83.33% | 1.64% |

## Runtime Summary

| Dataset | System | Records | Total ms | First record ms | Warm records | Warm mean ms | Warm P95 ms | Errors |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI4Privacy frozen | Presidio-only | 3000 | 16733.19 | 10480.54 | 2999 | 2.08 | 5.12 | 0 |
| AI4Privacy frozen | GLiNER-only | 3000 | 655357.87 | 12181.39 | 2999 | 214.46 | 281.15 | 0 |
| AI4Privacy frozen | Hybrid | 3000 | 647223.65 | 14212.15 | 2999 | 211.07 | 276.36 | 0 |
| Singapore stress | Presidio-only | 30 | 8322.13 | 8277.38 | 29 | 1.54 | 2.28 | 0 |
| Singapore stress | GLiNER-only | 30 | 23208.15 | 18948.78 | 29 | 146.87 | 173.73 | 0 |
| Singapore stress | Hybrid | 30 | 23225.56 | 18937.80 | 29 | 147.85 | 178.77 | 0 |

## Hybrid Per-Label Results: AI4Privacy Frozen

| Label | Gold | Exact typed R | Overlap typed R | Overlap protective R | Exact typed P | Overlap typed P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ADDRESS | 5179 | 8.65% | 14.93% | 17.47% | 52.34% | 90.30% |
| EMAIL | 1092 | 98.90% | 99.54% | 99.54% | 94.74% | 95.35% |
| GOVERNMENT_ID | 4107 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| IP_ADDRESS | 980 | 96.73% | 97.86% | 97.86% | 97.23% | 98.36% |
| PERSON | 2560 | 49.02% | 70.66% | 73.32% | 28.32% | 40.83% |
| PHONE | 767 | 30.12% | 44.72% | 44.72% | 20.14% | 29.90% |

## Hybrid Per-Label Results: Singapore Stress

| Label | Gold | Exact typed R | Overlap typed R | Overlap protective R | Exact typed P | Overlap typed P |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ADDRESS | 11 | 90.91% | 100.00% | 100.00% | 83.33% | 91.67% |
| EMAIL | 7 | 85.71% | 85.71% | 85.71% | 100.00% | 100.00% |
| GOVERNMENT_ID | 5 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| PERSON | 18 | 100.00% | 100.00% | 100.00% | 66.67% | 66.67% |
| PHONE | 12 | 83.33% | 83.33% | 83.33% | 100.00% | 100.00% |

## Top Hybrid Error Categories: AI4Privacy Frozen

| Dataset | System | Category | Count |
| --- | --- | --- | ---: |
| AI4Privacy frozen | Hybrid | missed_gold | 6409 |
| AI4Privacy frozen | Hybrid | false_positive | 4491 |
| AI4Privacy frozen | Hybrid | boundary_too_long | 2193 |
| AI4Privacy frozen | Hybrid | label_error | 1255 |
| AI4Privacy frozen | Hybrid | merged_entities | 639 |
| AI4Privacy frozen | Hybrid | overlap_wrong_label | 428 |
| AI4Privacy frozen | Hybrid | correct_range_abstained | 221 |
| AI4Privacy frozen | Hybrid | boundary_too_short | 121 |

## Hybrid Error Categories: Singapore Stress

| Dataset | System | Category | Count |
| --- | --- | --- | ---: |
| Singapore stress | Hybrid | false_positive | 9 |
| Singapore stress | Hybrid | missed_gold | 2 |
| Singapore stress | Hybrid | boundary_too_short | 1 |
| Singapore stress | Hybrid | label_error | 1 |
| Singapore stress | Hybrid | split_entity | 1 |

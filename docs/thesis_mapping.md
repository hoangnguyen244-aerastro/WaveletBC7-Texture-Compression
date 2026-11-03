# Thesis-to-code traceability

| Thesis section | Implementation | Evidence |
|---|---|---|
| Wavelet preprocessing and variants | src/wavelet.py | tests/test_research.py |
| BC7 encode/decode | src/wavelet_bc7/codec.py | DDS and decoded artifacts |
| Experimental setup | configs/pilot.json and dataset manifest | config.json, environment.json |
| Quality metrics | src/metrics.py and research.edge_mae | raw_results.csv |
| Paired comparison | src/wavelet_bc7/analysis.py | paired_summary.csv |
| Figures and tables | scripts/generate_report.py | figures/, report.md |

The 3-image pilot tests the software pipeline, not the research hypothesis. Validation selection and held-out test measurements must be documented before asserting improvements. All imagery must have verified redistribution licenses.

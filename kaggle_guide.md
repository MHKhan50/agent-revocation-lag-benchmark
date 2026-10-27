# Optional Kaggle dataset / notebook route

Kaggle is optional; this package runs locally without it.

1. Run `python3 run_benchmark.py`.
2. Create a Kaggle Dataset and upload `data/scenarios.csv`, `dataset_card.md`, `DATA_LICENSE.txt`, and `references.md`.
3. Suggested title: **RevocationLag: Synthetic Dynamic Agent Permission Scenarios**.
4. State that records are synthetic and contain no real agent traces.
5. Select the CC0 1.0 data licence and cite the repository/release once created.
6. Do not upload `outputs/episode_results.csv` as if it were raw data; label it as derived simulator output.

An optional notebook can load `scenarios.csv` and reproduce policy summaries. Keep policy definitions versioned in GitHub and record the exact commit/release used.

For this small generated CSV, Kaggle can provide discoverability and a notebook, but is not necessary. Zenodo, OSF, or Figshare may be better if the primary goal is a citable, versioned research artifact with a DOI. Hugging Face Datasets is useful if this grows into a maintained ML dataset collection. Roboflow is not relevant because there are no images.

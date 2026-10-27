# Publication checklist

## Before publishing
- [ ] Run `python3 run_benchmark.py`.
- [ ] Run `python3 -m unittest discover -s tests -v`; confirm all tests pass.
- [ ] Inspect `outputs/policy_summary.csv`, `outputs/per_seed_summary.csv`, `outputs/revocation_tradeoff.svg`, and `article_draft.md`.
- [ ] Label every result as **synthetic simulation**, not a real-world agent measurement.
- [ ] Review the optimistic immediate-notification baseline.
- [ ] Add author/contact details only if you want them public.
- [ ] Do not invent a DOI; no DOI is assigned yet.

## GitHub
- [ ] Create a public repository such as `agent-revocation-lag-benchmark`.
- [ ] Upload source, tests, dataset, outputs, article draft, licences, data card, and references.
- [ ] State Python version and exact command in the README.
- [ ] Create a tagged release after the package is stable.

## MASMATIX website
- [ ] Adapt `article_draft.md` to the existing site template as `insights/agent-revocation-lag-benchmark.html`.
- [ ] Use a plain canonical URL: `https://masmatixinnovations.co.uk/insights/agent-revocation-lag-benchmark.html`.
- [ ] Set matching `og:title`, `og:description`, and `og:url`; use a correct image URL only if an appropriate image exists.
- [ ] Add a card to `insights/index.html` and the matching URL to `sitemap.xml`.
- [ ] Validate HTML, sitemap XML, internal links, GitHub link, and mobile layout.
- [ ] Commit only intended files; do not commit local backups.
- [ ] After deployment, use Google Search Console URL Inspection to inspect the live URL and optionally request indexing.
- [ ] Google may or may not index the URL, and timing is not guaranteed. Indexing is not a certificate, endorsement, or quality award.

## Dataset / citable artifact
- [ ] Kaggle is optional; see `kaggle_guide.md`.
- [ ] If you need a DOI, consider Zenodo, OSF, or Figshare; archive a tagged release and check metadata/licence options.
- [ ] Hugging Face Datasets is an option if this grows into a maintained ML dataset collection; not required for this small simulator.
- [ ] Roboflow is not appropriate here because the package contains no images or computer-vision annotations.
- [ ] Avoid blind cross-posting. Use one canonical repository and cite the same version on other platforms.

# Paper

*Revoked, Not Stopped: Late Revocation Notices and Channel-Switching in LLM Agents*, Muzammal Hussain (2026).

| File | Content |
|---|---|
| `main.pdf` | the paper |
| `main.tex`, `references.bib`, `main.bbl` | LaTeX source (compiles with `latexmk -pdf main.tex`, or on Overleaf) |
| `figures/` | Figure 1 (exposure against control cost) and Figure 2 (disclosures under tool-scoped revocation) |
| `analysis.py` | recomputes every number, interval and figure from the repository |
| `results.json` | output of `analysis.py` |

Run from the repository root:

```bash
python3 paper/analysis.py
```

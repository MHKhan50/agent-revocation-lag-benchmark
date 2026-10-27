"""Create a dependency-free SVG summary chart."""
import csv
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
SUMMARY = ROOT / "outputs" / "policy_summary.csv"
OUT = ROOT / "outputs" / "revocation_tradeoff.svg"


def create_chart(summary_path=SUMMARY, output_path=OUT):
    with Path(summary_path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    order = ("check_once", "periodic_3", "per_sensitive", "push_revoke")
    rows.sort(key=lambda r: order.index(r["policy"]))
    width, height, left, right = 920, 500, 80, 880
    panels = [
        {"title": "Unauthorized side-effect rate", "field": "unauthorized_side_effect_rate",
         "ymax": 1.0, "fmt": lambda v: "{:.0%}".format(v), "top": 85, "bottom": 255},
        {"title": "Mean control events per episode", "field": "mean_control_events_per_episode",
         "ymax": max(1.0, max(float(r["mean_control_events_per_episode"]) for r in rows) * 1.15),
         "fmt": lambda v: "{:.2f}".format(v), "top": 305, "bottom": 445},
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="920" height="500" viewBox="0 0 920 500">',
        '<rect width="100%" height="100%" fill="none"/>',
        '<text x="460" y="32" text-anchor="middle" font-size="20" font-family="sans-serif" fill="currentColor">RevocationLag synthetic benchmark</text>',
    ]
    n, bar_w = len(rows), 90
    gap = (right - left - n * bar_w) / (n + 1)
    for panel in panels:
        top, bottom = panel["top"], panel["bottom"]
        parts.append('<text x="80" y="{}" font-size="15" font-family="sans-serif" fill="currentColor">{}</text>'.format(top - 18, escape(panel["title"])))
        parts.append('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="currentColor"/>'.format(left, bottom, right, bottom))
        for tick in (0.0, 0.5, 1.0):
            y = bottom - tick * (bottom - top)
            label = "{:.0%}".format(tick) if panel["field"] == "unauthorized_side_effect_rate" else "{:.0f}".format(tick * panel["ymax"])
            parts.append('<line x1="{}" y1="{:.1f}" x2="{}" y2="{:.1f}" stroke="currentColor" stroke-opacity="0.18"/>'.format(left, y, right, y))
            parts.append('<text x="{}" y="{:.1f}" text-anchor="end" font-size="11" font-family="sans-serif" fill="currentColor">{}</text>'.format(left - 10, y + 4, label))
        for i, row in enumerate(rows):
            x = left + gap * (i + 1) + bar_w * i
            value = float(row[panel["field"]])
            bar_h = min(1.0, value / panel["ymax"]) * (bottom - top)
            y = bottom - bar_h
            parts.append('<rect x="{:.1f}" y="{:.1f}" width="{}" height="{:.1f}" fill="currentColor" fill-opacity="0.58"/>'.format(x, y, bar_w, bar_h))
            parts.append('<text x="{:.1f}" y="{:.1f}" text-anchor="middle" font-size="12" font-family="sans-serif" fill="currentColor">{}</text>'.format(x + bar_w / 2, max(top + 12, y - 6), panel["fmt"](value)))
            if panel["field"] == "mean_control_events_per_episode":
                parts.append('<text x="{:.1f}" y="{}" text-anchor="middle" font-size="11" font-family="sans-serif" fill="currentColor">{}</text>'.format(x + bar_w / 2, bottom + 18, escape(row["policy"])))
    parts.append('<text x="460" y="490" text-anchor="middle" font-size="10" font-family="sans-serif" fill="currentColor">Synthetic scenarios only; not real-world incident estimates.</text>')
    parts.append("</svg>")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text("\n".join(parts), encoding="utf-8")
    return Path(output_path)


if __name__ == "__main__":
    print("Wrote", create_chart())

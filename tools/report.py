#!/usr/bin/env python3
"""
sysprobe_report.py
Generate an HTML report (plots + summary) from sysprobe JSONL traces.

Input: JSON Lines file with records like:
  {"type":"meta", ...}
  {"type":"sample", "ts":..., "cpu":..., "cpu_avg":..., "mem_used":..., "mem_avail":..., ...}
  {"type":"event", ...}   (optional, will be ignored unless it has ts)
  {"type":"end", ...}

Outputs:
  - report.html
  - cpu.png, mem.png, swap.png
  - (optional) raw summary JSON

Usage:
  python3 tools/sysprobe_report.py output.jsonl -o report_dir
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import math
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


# -------------------------
# Helpers
# -------------------------

def read_jsonl(path: str) -> Tuple[Optional[dict], List[dict], List[dict], Optional[dict]]:
    meta = None
    samples: List[dict] = []
    events: List[dict] = []
    end = None

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # If any non-JSON slips in, skip it rather than failing hard
                # (but you should aim for pure JSONL on stdout)
                continue

            rtype = rec.get("type")
            if rtype == "meta" and meta is None:
                meta = rec
            elif rtype == "sample":
                # Require ts
                if "ts" in rec:
                    samples.append(rec)
            elif rtype == "event":
                if "ts" in rec:
                    events.append(rec)
            elif rtype == "end":
                end = rec
            else:
                # Unknown type: ignore
                pass

    return meta, samples, events, end


def safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        return float(x)
    except Exception:
        return default


def percentile(vals: List[float], p: float) -> float:
    """p in [0, 100]"""
    clean = sorted(v for v in vals if not (math.isnan(v) or math.isinf(v)))
    if not clean:
        return float("nan")
    if p <= 0:
        return clean[0]
    if p >= 100:
        return clean[-1]
    k = (len(clean) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return clean[int(k)]
    d0 = clean[f] * (c - k)
    d1 = clean[c] * (k - f)
    return d0 + d1


@dataclass
class Summary:
    runtime_s: float
    n_samples: int
    cpu_mean: float
    cpu_p95: float
    cpu_max: float
    mem_avail_min: float
    mem_used_max: float
    swap_used_max: float
    cpu_warn_s: float
    cpu_danger_s: float
    mem_warn_s: float
    mem_danger_s: float


def compute_time_in_state(ts: List[float], state: List[str], target: str) -> float:
    """Approximate time spent in a given state using sample-to-sample dt."""
    if len(ts) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(ts)):
        dt_i = ts[i] - ts[i - 1]
        if state[i - 1] == target:
            total += max(0.0, dt_i)
    return total


def shade_state(ax, ts: List[float], state: List[str], label: str, alpha: float = 0.15):
    """
    Shade background regions where state == label.
    """
    if len(ts) < 2:
        return
    start = None
    for i in range(len(ts)):
        s = state[i]
        if s == label and start is None:
            start = ts[i]
        if (s != label or i == len(ts) - 1) and start is not None:
            end = ts[i] if s != label else ts[i]
            ax.axvspan(start, end, alpha=alpha)
            start = None


def write_html_report(
    out_path: str,
    meta: Optional[dict],
    summary: Summary,
    plots: Dict[str, str],
):
    """
    plots: mapping name -> relative filename (png)
    """
    title = "sysprobe report"
    created = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    meta_pretty = json.dumps(meta, indent=2) if meta else "{}"

    def row(k: str, v: str) -> str:
        return f"<tr><td><b>{k}</b></td><td>{v}</td></tr>"

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <style>
    body {{ font-family: sans-serif; max-width: 1000px; margin: 24px auto; padding: 0 16px; }}
    h1 {{ margin-bottom: 6px; }}
    .sub {{ color: #555; margin-bottom: 20px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    td {{ border: 1px solid #ddd; padding: 8px; }}
    .grid {{ display: grid; grid-template-columns: 1fr; gap: 18px; }}
    img {{ max-width: 100%; border: 1px solid #ddd; }}
    pre {{ background: #f6f8fa; padding: 12px; overflow-x: auto; border: 1px solid #eee; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="sub">Generated: {created}</div>

  <h2>Summary</h2>
  <table>
    {row("Runtime (s)", f"{summary.runtime_s:.3f}")}
    {row("Samples", str(summary.n_samples))}
    {row("CPU mean (%)", f"{summary.cpu_mean:.2f}")}
    {row("CPU p95 (%)", f"{summary.cpu_p95:.2f}")}
    {row("CPU max (%)", f"{summary.cpu_max:.2f}")}
    {row("Mem avail min (GB)", f"{summary.mem_avail_min:.2f}")}
    {row("Mem used max (GB)", f"{summary.mem_used_max:.2f}")}
    {row("Swap used max (GB)", f"{summary.swap_used_max:.2f}")}
    {row("CPU warn time (s)", f"{summary.cpu_warn_s:.2f}")}
    {row("CPU danger time (s)", f"{summary.cpu_danger_s:.2f}")}
    {row("MEM warn time (s)", f"{summary.mem_warn_s:.2f}")}
    {row("MEM danger time (s)", f"{summary.mem_danger_s:.2f}")}
  </table>

  <h2>Plots</h2>
  <div class="grid">
    <div><h3>CPU</h3><img src="{plots.get('cpu','')}" alt="cpu plot"></div>
    <div><h3>Memory</h3><img src="{plots.get('mem','')}" alt="mem plot"></div>
    <div><h3>Swap</h3><img src="{plots.get('swap','')}" alt="swap plot"></div>
  </div>

  <h2>Meta</h2>
  <pre>{meta_pretty}</pre>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


# -------------------------
# Main plotting/report
# -------------------------

def main():
    ap = argparse.ArgumentParser(description="Generate an HTML report from sysprobe JSONL output.")
    ap.add_argument("input", help="Path to sysprobe JSONL output")
    ap.add_argument("-o", "--outdir", default="sysprobe_report", help="Output directory (default: sysprobe_report)")
    ap.add_argument("--no-shading", action="store_true", help="Disable WARN/DANGER background shading")
    args = ap.parse_args()

    meta, samples, events, end = read_jsonl(args.input)
    if not samples:
        raise SystemExit("No sample records found. Ensure stdout contains JSONL with type=sample and a ts field.")

    os.makedirs(args.outdir, exist_ok=True)

    # Extract vectors
    ts = [safe_float(s.get("ts")) for s in samples]
    cpu = [safe_float(s.get("cpu")) for s in samples]
    cpu_avg = [safe_float(s.get("cpu_avg")) for s in samples]

    mem_used = [safe_float(s.get("mem_used")) for s in samples]
    mem_avail = [safe_float(s.get("mem_avail")) for s in samples]

    swap_used = [safe_float(s.get("mem_swap_used")) for s in samples]
    swap_avail = [safe_float(s.get("mem_swap_avail")) for s in samples]

    cpu_state = [str(s.get("CPU_STATE", "unknown")) for s in samples]
    mem_state = [str(s.get("MEM_STATE", "unknown")) for s in samples]

    runtime_s = (ts[-1] - ts[0]) if len(ts) > 1 else 0.0

    # Summary stats
    cpu_mean = sum(v for v in cpu if not math.isnan(v)) / max(1, sum(1 for v in cpu if not math.isnan(v)))
    cpu_p95 = percentile(cpu, 95)
    cpu_max = max((v for v in cpu if not math.isnan(v)), default=float("nan"))

    mem_avail_min = min((v for v in mem_avail if not math.isnan(v)), default=float("nan"))
    mem_used_max = max((v for v in mem_used if not math.isnan(v)), default=float("nan"))
    swap_used_max = max((v for v in swap_used if not math.isnan(v)), default=float("nan"))

    cpu_warn_s = compute_time_in_state(ts, cpu_state, "warn")
    cpu_danger_s = compute_time_in_state(ts, cpu_state, "danger")
    mem_warn_s = compute_time_in_state(ts, mem_state, "warn")
    mem_danger_s = compute_time_in_state(ts, mem_state, "danger")

    summary = Summary(
        runtime_s=runtime_s,
        n_samples=len(samples),
        cpu_mean=cpu_mean,
        cpu_p95=cpu_p95,
        cpu_max=cpu_max,
        mem_avail_min=mem_avail_min,
        mem_used_max=mem_used_max,
        swap_used_max=swap_used_max,
        cpu_warn_s=cpu_warn_s,
        cpu_danger_s=cpu_danger_s,
        mem_warn_s=mem_warn_s,
        mem_danger_s=mem_danger_s,
    )

    # Plot: CPU
    cpu_png = os.path.join(args.outdir, "cpu.png")
    plt.figure()
    plt.plot(ts, cpu, label="cpu (%)")
    plt.plot(ts, cpu_avg, label="cpu_avg (%)")
    ax = plt.gca()
    if not args.no_shading:
        shade_state(ax, ts, cpu_state, "warn", alpha=0.12)
        shade_state(ax, ts, cpu_state, "danger", alpha=0.18)
    plt.xlabel("time (s)")
    plt.ylabel("cpu (%)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(cpu_png, dpi=150)
    plt.close()

    # Plot: Memory
    mem_png = os.path.join(args.outdir, "mem.png")
    plt.figure()
    plt.plot(ts, mem_used, label="mem_used (GB)")
    plt.plot(ts, mem_avail, label="mem_avail (GB)")
    ax = plt.gca()
    if not args.no_shading:
        shade_state(ax, ts, mem_state, "warn", alpha=0.12)
        shade_state(ax, ts, mem_state, "danger", alpha=0.18)
    plt.xlabel("time (s)")
    plt.ylabel("GB")
    plt.legend()
    plt.tight_layout()
    plt.savefig(mem_png, dpi=150)
    plt.close()

    # Plot: Swap
    swap_png = os.path.join(args.outdir, "swap.png")
    plt.figure()
    plt.plot(ts, swap_used, label="swap_used (GB)")
    plt.plot(ts, swap_avail, label="swap_avail (GB)")
    plt.xlabel("time (s)")
    plt.ylabel("GB")
    plt.legend()
    plt.tight_layout()
    plt.savefig(swap_png, dpi=150)
    plt.close()

    # Write report.html
    report_html = os.path.join(args.outdir, "report.html")
    write_html_report(
        report_html,
        meta=meta,
        summary=summary,
        plots={"cpu": "cpu.png", "mem": "mem.png", "swap": "swap.png"},
    )

    # Also dump summary.json for programmatic use
    summary_json_path = os.path.join(args.outdir, "summary.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary.__dict__, f, indent=2)

    print(f"Wrote: {report_html}")
    print(f"Wrote: {cpu_png}, {mem_png}, {swap_png}")
    print(f"Wrote: {summary_json_path}")


if __name__ == "__main__":
    main()


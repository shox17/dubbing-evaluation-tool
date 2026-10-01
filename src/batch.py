"""Batch mode: evaluate a list of share links into one summary, and measure agreement with a person's verdicts.

The input is a text or CSV file with one link per line, optionally followed by a person's verdict
(`<link>,good` / `check` / `needs review` / `poor`). Lines starting with # and a `url,label` header are skipped.
summary_row() flattens one evaluation (or its error) into a row with every measure's level and value, which is
what threshold calibration needs; agreement() compares the tool's verdicts with the person's. Pure: no file
writes, no network.
"""
import csv
import io
import re
from typing import Optional

from src.compare import pad
from src.i18n import DEFAULT_UI_LANGUAGE, t as i18n_t

LABELS = {"good": "good", "check": "check", "needs review": "check", "needs_review": "check", "review": "check",
          "poor": "poor", "bad": "poor"}
LEVELS = ("good", "check", "poor")
BASE_COLUMNS = ["n", "link", "title", "source_language", "target_language", "lipsync", "verdict", "poor_items",
                "check_items", "problem_seconds", "meaning_score", "overlap_pct", "human_label", "agrees", "error"]


def parse_batch_file(text: str) -> list[dict]:
    """Links (and optional human verdicts) from a batch file. Raises ValueError for an unknown verdict."""
    entries = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip().lstrip("﻿")
        if not line or line.startswith("#"):
            continue
        fields = [f.strip() for f in re.split(r"[,\t;]", line, maxsplit=1)]
        if fields[0].lower() in ("url", "link", "share_url"):
            continue                                      # CSV header
        label = fields[1].strip().strip('"').lower() if len(fields) > 1 and fields[1].strip() else None
        if label is not None and label not in LABELS:
            raise ValueError(f"Line {number}: unknown verdict '{fields[1]}'. Use good, check (or needs review) or poor.")
        entries.append({"link": fields[0].strip('"'), "label": LABELS.get(label) if label else None, "line": number})
    if not entries:
        raise ValueError("The batch file has no links. Put one Perso share link per line.")
    return entries


def summary_row(n: int, entry: dict, results: Optional[dict] = None, error: Optional[str] = None) -> dict:
    """One summary row: the link, its verdict and counts, every measure's level and value, and agreement."""
    row = {c: "" for c in BASE_COLUMNS}
    row.update(n=n, link=entry["link"], human_label=entry.get("label") or "")
    if error is not None or results is None:
        row["error"] = error or "unknown error"
        return row
    rep = results["report"]
    p, tj = rep["project"], results.get("translation_judge") or {}
    counts = rep["overall"]["counts"]
    overlap = (results.get("timing_alignment") or {}).get("overlap_pct")
    row.update(title=p.get("title") or "", source_language=p.get("source_language") or "",
               target_language=p.get("target_language") or "", lipsync=p.get("is_lipsync"),
               verdict=rep["overall"]["level"], poor_items=counts["poor"], check_items=counts["check"],
               problem_seconds=rep.get("problem_seconds"),
               meaning_score=tj.get("meaning_score") if tj.get("measured") else "",
               overlap_pct=overlap if overlap is not None else "")
    for s in rep["sections"]:
        for m in s["metrics"]:
            row[f"{m['id']}_level"] = m["level"]
            row[f"{m['id']}_value"] = "" if m["value"] is None else m["value"]
    if row["human_label"]:
        row["agrees"] = row["verdict"] == row["human_label"]
    return row


def agreement(rows: list[dict]) -> Optional[dict]:
    """How often the tool's verdict matches the person's, with a confusion table (person x tool); None if unlabelled."""
    labelled = [r for r in rows if r["human_label"] and r["verdict"]]
    if not labelled:
        return None
    table = {h: {v: 0 for v in LEVELS} for h in LEVELS}
    for r in labelled:
        table[r["human_label"]][r["verdict"]] += 1
    agree = sum(table[x][x] for x in LEVELS)
    too_strict = sum(table[h][v] for h in LEVELS for v in LEVELS if LEVELS.index(v) > LEVELS.index(h))
    return {"labelled": len(labelled), "agree": agree, "agree_pct": round(agree / len(labelled) * 100, 1),
            "too_strict": too_strict, "too_lenient": len(labelled) - agree - too_strict, "table": table}


def to_csv(rows: list[dict]) -> str:
    """The summary as CSV (base columns first, then every measure's level and value)."""
    extra = sorted({k for r in rows for k in r} - set(BASE_COLUMNS))
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=BASE_COLUMNS + extra, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return out.getvalue()


def render_batch_text(rows: list[dict], lang: str = DEFAULT_UI_LANGUAGE, width: int = 100) -> str:
    """The summary as plain text: one line per link, then the agreement with the person's verdicts."""
    tr = lambda key, **p: i18n_t(key, lang, **p)
    bar, thin = "═" * width, "─" * width
    ok = [r for r in rows if not r["error"]]
    counts = {lv: sum(1 for r in ok if r["verdict"] == lv) for lv in LEVELS}
    lines = [bar, f" {tr('b.title').upper()}", bar,
             " " + tr("b.counts", n=len(rows), good=counts["good"], check=counts["check"], poor=counts["poor"],
                      failed=len(rows) - len(ok)), thin]
    for r in rows:
        if r["error"]:
            lines.append(f" {r['n']:>3}. ✗ {tr('b.failed')}: {r['error']}  ({r['link']})")
            continue
        human = f" · {tr('b.person')}: {tr('verdict.' + r['human_label'])}" + (" ✓" if r["agrees"] else " ✗") \
            if r["human_label"] else ""
        meaning = f" · {tr('b.meaning')} {r['meaning_score']}/5" if r["meaning_score"] != "" else ""
        lines.append(f" {r['n']:>3}. {tr('verdict.' + r['verdict'])} · {r['title']} ({r['source_language']} → "
                     f"{r['target_language']}) · {tr('b.items', poor=r['poor_items'], check=r['check_items'])}"
                     f" · {r['problem_seconds']} s{meaning}{human}")
    agr = agreement(rows)
    lines.append(thin)
    if agr:
        lines.append(" " + tr("b.agreement", agree=agr["agree"], n=agr["labelled"], pct=f"{agr['agree_pct']:.0f}",
                              strict=agr["too_strict"], lenient=agr["too_lenient"]))
        lines.append("   " + pad(tr("b.person_tool"), 24) + "".join(pad(tr("verdict." + v), 16) for v in LEVELS))
        for h in LEVELS:
            lines.append("   " + pad(tr("verdict." + h), 24) + "".join(pad(str(agr["table"][h][v]), 16) for v in LEVELS))
    else:
        lines.append(" " + tr("b.no_labels"))
    lines.append(bar)
    return "\n".join(lines)

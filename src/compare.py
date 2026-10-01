"""Compare mode: two Perso dubs of the same video, one recommendation, and why.

build_comparison(results_a, results_b, lang) builds both reports, applies the decision rule (decide), and
returns everything the comparison files show: the recommended version, problem intervals per dub, the
reasoning, a side-by-side table of every check, each link's metadata and measurement notes. Rendering is in
render_comparison_text / render_comparison_html. Pure: no file writes, no network.
"""
import html
import time
import unicodedata
from typing import Callable, Optional

from src.i18n import DEFAULT_UI_LANGUAGE, t as i18n_t
from src.report import ICONS, build_report, _CSS
from src.version import TOOL_VERSION

Tr = Callable[..., str]
DUBS = ("A", "B")
VERDICT_RANK = {"good": 0, "check": 1, "poor": 2}
SAME_VIDEO_PCT = 5.0              # originals differing in length by more than this may be different videos
# The decision rule, in order: (rule id, fact compared, which value is better). The first rule whose values differ
# decides; a rule is skipped when either dub has no value for it (for example, the translation wasn't checked).
RULES = (
    ("verdict", "verdict_rank", "lower"),
    ("poor_items", "poor", "lower"),
    ("check_items", "check", "lower"),
    ("problem_seconds", "problem_seconds", "lower"),
    ("meaning_score", "meaning_score", "higher"),
    ("speech_timing", "overlap_pct", "higher"),
)


def facts(rep: dict, r: dict) -> dict:
    """The values the decision rule compares, from one dub's report and results."""
    tj = r.get("translation_judge") or {}
    overlap = (r.get("timing_alignment") or {}).get("overlap_pct")
    level = rep["overall"]["level"]
    return {
        "verdict": level,
        "verdict_rank": VERDICT_RANK[level],
        "poor": rep["overall"]["counts"]["poor"],
        "check": rep["overall"]["counts"]["check"],
        "problem_seconds": round(float(rep.get("problem_seconds") or 0.0), 1),
        "meaning_score": tj.get("meaning_score") if tj.get("measured") else None,
        "overlap_pct": round(float(overlap), 1) if overlap is not None else None,
    }


def decide(a: dict, b: dict) -> dict:
    """Applies the decision rule to two dubs' facts: the winner, the rule that decided, and the values at it.

    Stops at the first rule that separates the dubs. A rule where either value is missing is skipped. If no
    rule separates them, A is recommended and the result says it is a tie.
    """
    skipped = []
    for number, (rule, key, better) in enumerate(RULES, 1):
        va, vb = a.get(key), b.get(key)
        if va is None or vb is None:
            skipped.append(rule)
            continue
        if va != vb:
            a_wins = va < vb if better == "lower" else va > vb
            return {"winner": "A" if a_wins else "B", "tie": False, "rule": rule, "rule_number": number,
                    "values": {"A": va, "B": vb}, "skipped": skipped}
    return {"winner": "A", "tie": True, "rule": None, "rule_number": None, "values": None, "skipped": skipped}


def _shown(tr: Tr, rule: str, f: dict) -> str:
    """A dub's value at a rule, as people read it."""
    key = dict((r, k) for r, k, _ in RULES)[rule]
    value = f[key]
    if value is None:
        return "—"
    if rule == "verdict":
        return tr(f"verdict.{f['verdict']}")
    if rule == "problem_seconds":
        return f"{value:.1f} s"
    if rule == "meaning_score":
        return f"{value} / 5"
    if rule == "speech_timing":
        return f"{value:.1f}%"
    return str(value)


def _problems(rep: dict, limit: int = 3) -> list[str]:
    """A dub's worst measures with their level, Poor first: 'Speech timing (Check)'."""
    rows = [m for s in rep["sections"] for m in s["metrics"]]
    return [f"{m['label']} ({rep['badges'][lv]})" for lv in ("poor", "check") for m in rows if m["level"] == lv][:limit]


def _fix_first(rep: dict, limit: int = 5) -> list[str]:
    """What to fix first in a Poor dub: its Poor measures, then its Poor problem intervals."""
    rows = [f"{m['label']}: {m['message']}" for s in rep["sections"] for m in s["metrics"] if m["level"] == "poor"]
    rows += [f"{i['start']:.1f}s-{i['end']:.1f}s {i['category_label']}: {i['description']}"
             for i in rep["problem_intervals"] if i["severity"] == "poor"]
    return rows[:limit]


def _table(reps: dict) -> list[dict]:
    """Every check of both reports side by side, in report order (A's order, then any B-only rows)."""
    order, rows = [], {}
    for dub in DUBS:
        for s in reps[dub]["sections"]:
            for m in s["metrics"]:
                if m["id"] not in rows:
                    order.append(m["id"])
                    rows[m["id"]] = {"id": m["id"], "section": s["title"], "label": m["label"], "A": None, "B": None}
                rows[m["id"]][dub] = {"level": m["level"], "display": m["display"],
                                      "badge": reps[dub]["badges"][m["level"]]}
    return [rows[i] for i in order]


def _link(tr: Tr, rep: dict) -> dict:
    """One link's metadata for the comparison."""
    p = rep["project"]
    lip = p.get("is_lipsync")
    return {"title": p.get("title"), "languages": f"{p.get('source_language') or '?'} → {p.get('target_language') or '?'}",
            "length": f"{p['duration_sec']:.1f} s" if p.get("duration_sec") else "—",
            "lipsync": "—" if lip is None else tr("c.yes" if lip else "c.no"),
            "project": f"#{p['perso_seq']}" if p.get("perso_seq") else "—",
            "evaluated": p.get("evaluated_video") or "—", "link": p.get("share_url") or "—"}


def _notes(tr: Tr, reps: dict, res: dict, no_translation: list[str]) -> list[str]:
    """What wasn't measured and why, plus warnings about the pair itself."""
    notes = []
    for dub in DUBS:
        items = reps[dub]["not_measured"]
        if items:
            notes.append(tr("c.note.not_measured", dub=dub, items="; ".join(f"{x['label']}: {x['reason']}" for x in items)))
    if no_translation:
        notes.append(tr("c.no_translation", dubs=", ".join(tr("c.dub", d=d) for d in no_translation)))
    pa, pb = reps["A"]["project"], reps["B"]["project"]
    if pa.get("perso_seq") and pa.get("perso_seq") == pb.get("perso_seq"):
        notes.append(tr("c.note.same_project"))
    oa = (res["A"].get("acoustic_metrics") or {}).get("original_duration_sec")
    ob = (res["B"].get("acoustic_metrics") or {}).get("original_duration_sec")
    if oa and ob and abs(oa - ob) / max(oa, ob) * 100 > SAME_VIDEO_PCT:
        notes.append(tr("c.note.other_video", a=f"{oa:.1f}", b=f"{ob:.1f}"))
    if (pa.get("target_language_code") or "") != (pb.get("target_language_code") or ""):
        notes.append(tr("c.note.other_language", a=pa.get("target_language") or "?", b=pb.get("target_language") or "?"))
    return notes or [tr("c.note.none")]


def build_comparison(results_a: dict, results_b: dict, lang: str = DEFAULT_UI_LANGUAGE,
                     run_seconds: Optional[float] = None) -> dict:
    """Both reports, the recommendation with its reasoning, and everything the comparison files show, in lang."""
    tr: Tr = lambda key, **p: i18n_t(key, lang, **p)
    res = {"A": results_a, "B": results_b}
    reps = {dub: build_report(res[dub], lang, dub=dub) for dub in DUBS}
    f = {dub: facts(reps[dub], res[dub]) for dub in DUBS}
    dec = decide(f["A"], f["B"])
    win = dec["winner"]
    lose = "B" if win == "A" else "A"
    both_poor = f["A"]["verdict"] == "poor" and f["B"]["verdict"] == "poor"
    no_translation = [dub for dub in DUBS if f[dub]["meaning_score"] is None]

    if dec["tie"]:
        why = tr("c.why.tie")
    else:
        why = tr(f"c.why.{dec['rule']}", win=win, lose=lose, win_value=_shown(tr, dec["rule"], f[win]),
                 lose_value=_shown(tr, dec["rule"], f[lose]))
    other = _problems(reps[lose])
    summary = [why, tr("c.loser_problems", dub=lose, items=", ".join(other)) if other else tr("c.loser_clean", dub=lose),
               tr(f"c.ready.{f[win]['verdict']}", dub=win)]
    values = ({dub: _shown(tr, dec["rule"], f[dub]) for dub in DUBS} if dec["rule"] else
              {dub: tr(f"verdict.{f[dub]['verdict']}") for dub in DUBS})
    return {
        "comparison_version": 1,
        "lang": lang,
        "recommendation": {
            "dub": win, "tie": dec["tie"], "both_poor": both_poor, "ready": not both_poor,
            "title": reps[win]["project"].get("title"), "verdict": f[win]["verdict"],
            "verdict_label": tr(f"verdict.{f[win]['verdict']}"),
            "headline": tr("c.recommend_tie") if dec["tie"] else tr("c.recommend", d=win),
            "warning": tr("c.not_ready", d=win) if both_poor else None,
            "fix_first": _fix_first(reps[win]) if both_poor else [],
        },
        "intervals": {dub: reps[dub]["problem_intervals"] for dub in DUBS},
        "possible_asr_errors": {dub: reps[dub]["possible_asr_errors"] for dub in DUBS},
        "problem_seconds": {dub: f[dub]["problem_seconds"] for dub in DUBS},
        "reasoning": {
            "rule": dec["rule"] or "tie", "rule_number": dec["rule_number"],
            "rule_label": tr(f"c.rule.{dec['rule'] or 'tie'}"),
            "values": values, "deciding_factor": why, "summary": summary,
            "skipped_rules": [tr(f"c.rule.{r}") for r in dec["skipped"]],
            "translation_used": not no_translation,
            "translation_note": (tr("c.no_translation", dubs=", ".join(tr("c.dub", d=d) for d in no_translation))
                                 if no_translation else tr("c.translation_used")),
            "rules_order": tr("c.rules_order"),
        },
        "facts": f,
        "decision": dec,
        "table": _table(reps),
        "links": {dub: _link(tr, reps[dub]) for dub in DUBS},
        "notes": _notes(tr, reps, res, no_translation),
        "meta": {"tool_version": TOOL_VERSION, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "run_seconds": round(run_seconds, 1) if run_seconds is not None else None},
        "labels": {k: tr(f"c.{k}") for k in (
            "title", "sec.recommended", "sec.intervals", "sec.reasoning", "sec.table", "sec.links", "sec.notes",
            "rule_label", "values_label", "summary_label", "fix_first", "asr", "no_intervals", "table.check",
            "verdict", "open_report", "meta.title", "meta.languages", "meta.length", "meta.lipsync", "meta.project",
            "meta.evaluated", "meta.link", "skipped")} | {
            "dub_A": tr("c.dub", d="A"), "dub_B": tr("c.dub", d="B"),
            "count_A": _count(tr, reps["A"]), "count_B": _count(tr, reps["B"]),
            "footer": tr("c.footer", version=TOOL_VERSION,
                         sec=f"{run_seconds:.0f}" if run_seconds is not None else "—",
                         time=time.strftime("%Y-%m-%d %H:%M:%S"))},
        "badges": reps["A"]["badges"],
        "reports": reps,
    }


def _count(tr: Tr, rep: dict) -> str:
    """'3 problem intervals, 7.5 s in total' for one dub."""
    n = len(rep["problem_intervals"])
    return tr(f"c.intervals_count_{'one' if n == 1 else 'many'}", n=n, sec=f"{rep['problem_seconds']:.1f}")


def interval_line(i: dict, lb: dict, badges: dict) -> str:
    """One problem interval as a line: '12.4s-15.1s | Dub B | missing speech | Poor | Translation check | ...'."""
    dub = lb.get(f"dub_{i.get('dub')}", "") if i.get("dub") else ""
    parts = [f"{i['start']:.1f}s-{i['end']:.1f}s"] + ([dub] if dub else []) + [
        i["category_label"], badges.get(i["severity"], i["severity"]), i["check_label"], i["description"]]
    return " | ".join(parts)


# ---------------- renderers ----------------
def text_width(text: str) -> int:
    """Columns text takes in a terminal: Hangul, CJK and emoji count double."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 if ch == "\ufe0f" else
               0 if unicodedata.combining(ch) else 1 for ch in text)


def pad(text: str, width: int) -> str:
    """text padded with spaces to width terminal columns."""
    return text + " " * max(0, width - text_width(text))


def wrap(text: str, width: int, first: str, rest: str = "") -> list[str]:
    """Word-wraps text to width terminal columns (Korean-aware); long words such as URLs are never split."""
    rest = rest or " " * len(first)
    lines, line = [], first
    for word in text.split():
        candidate = word if line in (first, rest) else f" {word}"
        if text_width(line + candidate) > width and line not in (first, rest):
            lines.append(line)
            line, candidate = rest, word
        line += candidate
    lines.append(line)
    return lines


def render_comparison_text(comp: dict, width: int = 100) -> str:
    """The comparison as plain text: recommended version, problem intervals, reasoning, then the details."""
    lb, rec, why = comp["labels"], comp["recommendation"], comp["reasoning"]
    bar, thin = "═" * width, "─" * width
    w_ = lambda text, first, rest="": wrap(text, width, first, rest)
    icon = ICONS[rec["verdict"]]
    title = f" {lb['title'].upper()}"
    lines = [bar, title + " " * max(1, width - text_width(title) - len(comp["meta"]["generated"])) + comp["meta"]["generated"], bar,
             f" 1. {lb['sec.recommended'].upper()}"]
    lines += w_(f"{icon} {rec['headline']}", "    ")
    lines += w_(f"{lb['dub_' + rec['dub']]}: {rec['title'] or ''} · {lb['verdict']}: {rec['verdict_label']}", "    ")
    if rec["warning"]:
        lines += w_(f"❌ {rec['warning']}", "    ")
        lines.append(f"    {lb['fix_first']}:")
        for item in rec["fix_first"]:
            lines += w_(f"- {item}", "      ", "        ")
    lines += ["", thin, f" 2. {lb['sec.intervals'].upper()}"]
    for dub in DUBS:
        lines.append(f"  {lb['dub_' + dub]} ({lb['count_' + dub]})")
        items = comp["intervals"][dub]
        if not items:
            lines.append(f"    {lb['no_intervals']}")
        for i in items:
            lines += w_(interval_line(i, lb, comp["badges"]), "    ", "      ")
        if comp["possible_asr_errors"][dub]:
            lines.append(f"    {lb['asr']}:")
            for i in comp["possible_asr_errors"][dub]:
                lines += w_(interval_line(i, lb, comp["badges"]), "      ", "        ")
    lines += ["", thin, f" 3. {lb['sec.reasoning'].upper()}"]
    lines += w_(f"{lb['rule_label']}: {why['rule_label']}", "    ")
    lines += w_(f"{lb['values_label']}: {lb['dub_A']} = {why['values']['A']} · {lb['dub_B']} = {why['values']['B']}", "    ")
    lines += w_(f"{lb['summary_label']}: " + " ".join(why["summary"]), "    ")
    lines += w_(why["translation_note"], "    ")
    if why["skipped_rules"]:
        lines += w_(f"{lb['skipped']}: " + ", ".join(why["skipped_rules"]), "    ")
    lines += w_(why["rules_order"], "    ")

    lines += ["", thin, f" {lb['sec.table'].upper()}"]
    cell = lambda c: f"{ICONS[c['level']]} {c['badge']} · {c['display']}" if c else "—"
    w = max([text_width(r["label"]) for r in comp["table"]] + [text_width(lb["table.check"])]) + 2
    col = max([text_width(cell(r["A"])) for r in comp["table"]] + [text_width(lb["dub_A"])]) + 3
    lines.append(f"    {pad(lb['table.check'], w)}{pad(lb['dub_A'], col)}{lb['dub_B']}")
    for row in comp["table"]:
        lines.append(f"    {pad(row['label'], w)}{pad(cell(row['A']), col)}{cell(row['B'])}")
    lines += ["", thin, f" {lb['sec.links'].upper()}"]
    for dub in DUBS:
        link = comp["links"][dub]
        lines.append(f"  {lb['dub_' + dub]}")
        for key in ("title", "languages", "length", "lipsync", "project", "evaluated", "link"):
            lines += w_(f"{lb['meta.' + key]}: {link[key]}", "    ", "      ")
    lines += ["", thin, f" {lb['sec.notes'].upper()}"]
    for note in comp["notes"]:
        lines += w_(f"· {note}", "    ", "      ")
    lines += [thin, f" {lb['footer']}", bar]
    return "\n".join(lines)


_EXTRA_CSS = """
.cols{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media (max-width:760px){.cols{grid-template-columns:1fr}}
.rec{border-width:2px}.rec.good{border-color:var(--good);background:var(--good-bg)}.rec.check{border-color:var(--check);
background:var(--check-bg)}.rec.poor{border-color:var(--poor);background:var(--poor-bg)}
.warn{color:var(--poor);font-weight:600}th{text-align:left;font-size:13px;color:var(--muted);padding:6px}
ol.fix li{margin:4px 0}.small{font-size:13px}
"""


def render_comparison_html(comp: dict) -> str:
    """A self-contained HTML comparison (light and dark), with the three decision sections at the top."""
    e = lambda x: html.escape(str(x)) if x is not None else ""
    lb, rec, why = comp["labels"], comp["recommendation"], comp["reasoning"]
    out = [f"<!doctype html><html lang={e(comp.get('lang', 'en'))}><head><meta charset=utf-8><meta name=viewport "
           f"content='width=device-width,initial-scale=1'><title>{e(lb['title'])}</title><style>{_CSS}{_EXTRA_CSS}"
           f"</style></head><body><main><h1>{e(lb['title'])}</h1><div class='meta muted'>"
           f"<span>{e(comp['meta']['generated'])}</span></div>",
           f"<div class='card rec {rec['verdict']}'><h2>1. {e(lb['sec.recommended'])}</h2>"
           f"<div class=big>{ICONS[rec['verdict']]} {e(rec['headline'])}</div>"
           f"<p>{e(lb['dub_' + rec['dub']])}: <b>{e(rec['title'])}</b> · {e(lb['verdict'])}: "
           f"<span class='badge b-{rec['verdict']}'>{e(rec['verdict_label'])}</span></p>"]
    if rec["warning"]:
        out.append(f"<p class=warn>{e(rec['warning'])}</p><b>{e(lb['fix_first'])}</b><ol class=fix>"
                   + "".join(f"<li>{e(x)}</li>" for x in rec["fix_first"]) + "</ol>")
    out.append("</div>")
    out.append(f"<div class=card><h2>2. {e(lb['sec.intervals'])}</h2><div class=cols>")
    for dub in DUBS:
        out.append(f"<div><b>{e(lb['dub_' + dub])}</b> <span class=muted>({e(lb['count_' + dub])})</span> "
                   f"<a href='report_{dub}.html'>{e(lb['open_report'])}</a><table>")
        if not comp["intervals"][dub]:
            out.append(f"<tr><td class=muted>{e(lb['no_intervals'])}</td></tr>")
        for i in comp["intervals"][dub]:
            out.append(f"<tr><td class='v t'>{i['start']:.1f}s–{i['end']:.1f}s</td><td><span class='badge "
                       f"b-{i['severity']}'>{e(i['category_label'])}</span> {e(i['description'])}"
                       f"<div class=th>{e(comp['badges'][i['severity']])} · {e(i['check_label'])}</div></td></tr>")
        out.append("</table>")
        if comp["possible_asr_errors"][dub]:
            out.append(f"<p class='small muted'><b>{e(lb['asr'])}</b></p><ul class='small muted'>" + "".join(
                f"<li>{i['start']:.1f}s–{i['end']:.1f}s · {e(i['category_label'])}: {e(i['description'])}</li>"
                for i in comp["possible_asr_errors"][dub]) + "</ul>")
        out.append("</div>")
    out.append("</div></div>")
    out.append(f"<div class=card><h2>3. {e(lb['sec.reasoning'])}</h2><table>"
               f"<tr><td class=l>{e(lb['rule_label'])}</td><td>{e(why['rule_label'])}</td></tr>"
               f"<tr><td class=l>{e(lb['values_label'])}</td><td>{e(lb['dub_A'])}: <b>{e(why['values']['A'])}</b> · "
               f"{e(lb['dub_B'])}: <b>{e(why['values']['B'])}</b></td></tr>"
               f"<tr><td class=l>{e(lb['summary_label'])}</td><td>{e(' '.join(why['summary']))}</td></tr></table>"
               f"<p class=note>{e(why['translation_note'])}"
               + (f" {e(lb['skipped'])}: {e(', '.join(why['skipped_rules']))}." if why["skipped_rules"] else "")
               + f"</p><p class=note>{e(why['rules_order'])}</p></div>")
    out.append(f"<div class=card><h2>{e(lb['sec.table'])}</h2><table><tr><th>{e(lb['table.check'])}</th>"
               f"<th>{e(lb['dub_A'])}</th><th>{e(lb['dub_B'])}</th></tr>")
    cell = lambda c: (f"<span class='badge b-{c['level']}'>{e(c['badge'])}</span> <span class=t>{e(c['display'])}</span>"
                      if c else "—")
    for row in comp["table"]:
        out.append(f"<tr><td class=l>{e(row['label'])}</td><td>{cell(row['A'])}</td><td>{cell(row['B'])}</td></tr>")
    out.append("</table></div>")
    out.append(f"<div class=card><h2>{e(lb['sec.links'])}</h2><div class=cols>")
    for dub in DUBS:
        link = comp["links"][dub]
        out.append(f"<div><b>{e(lb['dub_' + dub])}</b><table>" + "".join(
            f"<tr><td class=l>{e(lb['meta.' + k])}</td><td>{e(link[k])}</td></tr>"
            for k in ("title", "languages", "length", "lipsync", "project", "evaluated", "link")) + "</table></div>")
    out.append("</div></div>")
    out.append(f"<div class=card><h2>{e(lb['sec.notes'])}</h2><ul>"
               + "".join(f"<li>{e(n)}</li>" for n in comp["notes"]) + "</ul></div>")
    out.append(f"<p class=note>{e(lb['footer'])}</p></main></body></html>")
    return "".join(out)

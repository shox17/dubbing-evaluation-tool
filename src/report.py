"""The quality report: turns raw measurements into verdicts a person can act on.

build_report(results, lang) gives every measure a level (good / check / poor / info / not_measured), a
plain-language explanation and how it is graded, lists timestamped things to check, and derives an overall
verdict, all in the chosen interface language (texts live in src/report_text.py). render_text and render_html
present the same report. Pure: no file writes, no network.
"""
import html
import math
import textwrap
from pathlib import Path
from typing import Callable, Optional

from src.evaluate import base_lang, whisper_language
from src.i18n import DEFAULT_UI_LANGUAGE, t as i18n_t
from src.intervals import VOICE_OVRL_DROP, VOICE_SIG_DROP, build_intervals, local_text as _local, voice_window_level

# Thresholds, in one place so the report can print exactly what it applied.
LENGTH_PCT = (5.0, 15.0)                 # |dub - original| / original
LOUDNESS_DB = (2.0, 4.0)                 # |20 log10(rms ratio)|
SILENCE_PTS = (5.0, 15.0)                # extra silence in the dub, percentage points
CLIPPING_PCT = (0.01, 0.1)               # share of samples at full scale
# Speaking pace per dub language: chars/s for ko/ja/zh, words/s for en/es. A language without a rule is not graded.
SPEECH_RATE = {"ko": (7.5, 9.0), "ja": (8.5, 10.5), "zh": (6.0, 7.5), "en": (3.2, 3.8), "es": (3.5, 4.2)}
CLARITY_PCT = (90.0, 70.0)               # speech time Whisper recognised confidently
LANGUAGE_PROB = 0.5                      # below this the language guess is uncertain
OVERLAP_PCT = (75.0, 55.0)               # speech-timing overlap; a real Perso EN→KO dub scores ~81%
SCRIPT_PCT = (80.0, 50.0)                # accuracy against a script
MEANING_SCORE = (4, 3)                   # LLM judge, 1-5
VOICE_SIMILAR = 0.5                      # voice similarity to the original speaker: Good from this, else Check
VOICE_FLOOR = 1.6                        # voice quality: an original scoring below this (1-5) is too noisy to compare
# Voice-quality window bands (how far the dub may fall below the original) are in src/intervals.py.

LEVELS = ("good", "check", "poor")
ICONS = {"good": "✅", "check": "⚠️", "poor": "❌", "info": "ℹ️", "not_measured": "·"}
Tr = Callable[..., str]


def fmt_time(sec: Optional[float]) -> str:
    """Seconds as mm:ss.s, or an empty string."""
    if sec is None:
        return ""
    m, s = divmod(max(0.0, float(sec)), 60)
    return f"{int(m):02d}:{s:04.1f}"


def _band_max(value: float, bands: tuple[float, float]) -> str:
    """Level for a value where lower is better."""
    return "good" if value <= bands[0] else "check" if value <= bands[1] else "poor"


def _band_min(value: float, bands: tuple[float, float]) -> str:
    """Level for a value where higher is better."""
    return "good" if value >= bands[0] else "check" if value >= bands[1] else "poor"


def _pl(tr: Tr, key: str, n: int, **params) -> str:
    """The singular (key_one) or plural (key_many) text for a count."""
    return tr(f"{key}_{'one' if n == 1 else 'many'}", n=n, **params)


def _metric(tr: Tr, mid: str, level: str, message: str, value=None, display: str = "", graded: str = "") -> dict:
    """One report row. value is None when not measured."""
    return {"id": mid, "label": tr(f"r.m.{mid}"), "level": level, "value": value,
            "display": display or ("—" if value is None else str(value)), "message": message, "thresholds": graded}


def _na(tr: Tr, mid: str, reason: str) -> dict:
    """A measure that couldn't be measured, with the reason."""
    return _metric(tr, mid, "not_measured", reason)


# ---------------- sections ----------------
def _timing_audio(tr: Tr, ac: dict, sr: dict, lang: str, lang_name: str) -> list[dict]:
    """Length, loudness, silence, distortion and speaking pace."""
    rows = []
    od, dd = ac["original_duration_sec"], ac["dubbed_duration_sec"]
    if od:
        pct = abs(dd - od) / od * 100
        level = _band_max(pct, LENGTH_PCT)
        diff = dd - od
        if abs(diff) < 0.05:
            msg = tr("r.length.same", dub=f"{dd:.1f}", orig=f"{od:.1f}")
        else:
            way = "longer" if diff > 0 else "shorter"
            msg = tr(f"r.length.{way}_{'ok' if level == 'good' else 'bad'}", diff=f"{abs(diff):.1f}", pct=f"{pct:.1f}")
        rows.append(_metric(tr, "length_match", level, msg, round(pct, 1), f"{diff:+.2f} s ({pct:.1f}%)",
                            tr("r.g.length", good=f"{LENGTH_PCT[0]:g}", check=f"{LENGTH_PCT[1]:g}")))
    else:
        rows.append(_na(tr, "length_match", tr("r.length.na")))

    ratio = ac.get("rms_ratio")
    if ratio:
        db = round(20 * math.log10(ratio), 1) + 0.0  # + 0.0 turns -0.0 into 0.0
        level = _band_max(abs(db), LOUDNESS_DB)
        if abs(db) < 0.5:
            msg = tr("r.loud.same")
        else:
            way = "louder" if db > 0 else "quieter"
            msg = tr(f"r.loud.{way}_{'ok' if level == 'good' else 'bad'}", db=f"{abs(db):.1f}")
        rows.append(_metric(tr, "loudness_match", level, msg, db, f"{db:+.1f} dB",
                            tr("r.g.loudness", good=f"{LOUDNESS_DB[0]:g}", check=f"{LOUDNESS_DB[1]:g}")))
    else:
        rows.append(_na(tr, "loudness_match", tr("r.loud.na")))

    extra = (ac["dubbed_silence_ratio"] - ac["original_silence_ratio"]) * 100
    level = _band_max(max(0.0, extra), SILENCE_PTS)
    before, after = f"{ac['original_silence_ratio']:.1%}", f"{ac['dubbed_silence_ratio']:.1%}"
    msg = (tr("r.silence.ok", orig=before, dub=after) if level == "good"
           else tr("r.silence.bad", pts=f"{extra:.0f}", orig=before, dub=after))
    rows.append(_metric(tr, "silence", level, msg, round(extra, 1), f"{before} → {after}",
                        tr("r.g.silence", good=f"{SILENCE_PTS[0]:g}", check=f"{SILENCE_PTS[1]:g}")))

    clip = ac.get("dubbed_clipping_pct")
    if clip is not None:
        level = _band_max(clip, CLIPPING_PCT)
        msg = tr("r.clip.ok") if level == "good" else tr("r.clip.bad", pct=f"{clip:.2f}")
        rows.append(_metric(tr, "clipping", level, msg, clip, f"{clip:.3f}%",
                            tr("r.g.clipping", good=f"{CLIPPING_PCT[0]:g}", check=f"{CLIPPING_PCT[1]:g}")))

    rows.append(_pace(tr, sr.get("dubbed_speech_rate"), lang, lang_name))
    return rows


def _pace(tr: Tr, rate: Optional[dict], lang: str, lang_name: str) -> dict:
    """Speaking pace of the dub, graded only for languages with a pace rule (SPEECH_RATE)."""
    if not rate:
        return _na(tr, "speech_rate", tr("r.no_speech"))
    unit = tr(f"unit.{rate['unit']}")
    shown = f"{rate['value']:.1f} {unit}"
    bands = SPEECH_RATE.get(base_lang(lang))
    if not bands:
        return _na(tr, "speech_rate", tr("r.pace.no_rule", lang=lang_name or lang or "?", rate=shown))
    level = _band_max(rate["value"], bands)
    return _metric(tr, "speech_rate", level, tr(f"r.pace.{level}", rate=shown), rate["value"], shown,
                   tr("r.g.pace", good=f"{bands[0]:g}", check=f"{bands[1]:g}", unit=unit))


def _voice(tr: Tr, vq: Optional[dict]) -> dict:
    """Voice quality of the dub against the original at the same moments (DNSMOS SIG)."""
    if not vq:
        return _na(tr, "voice_quality", tr("r.vq.old"))
    if not vq.get("measured"):
        return _na(tr, "voice_quality", tr(vq.get("reason_key") or "r.vq.error"))
    dub, orig, diff = vq["dub"], vq["original"], vq["difference"]
    if orig < VOICE_FLOOR:
        return _na(tr, "voice_quality", tr("r.vq.too_noisy", orig=f"{orig:.1f}"))
    levels = [voice_window_level(w) for w in vq["windows"]]
    level = "poor" if "poor" in levels else "check" if "check" in levels else "good"
    flagged = sum(1 for lv in levels if lv != "good")
    shown = f"{dub:.1f} / {orig:.1f}" + (f" · {flagged}/{len(levels)}" if flagged else "")
    msg = tr("r.vq.good", dub=f"{dub:.1f}", orig=f"{orig:.1f}") if level == "good" else \
        _pl(tr, f"r.vq.{level}", flagged, total=len(levels))
    return _metric(tr, "voice_quality", level, msg, diff, shown,
                   tr("r.g.vq", sig=f"{VOICE_SIG_DROP[0]:g}", ovr=f"{VOICE_OVRL_DROP[0]:g}",
                      sig_poor=f"{VOICE_SIG_DROP[1]:g}", ovr_poor=f"{VOICE_OVRL_DROP[1]:g}"))


def _similarity(tr: Tr, vs: Optional[dict]) -> dict:
    """How much the dub voice sounds like the original speaker, line by line (never Poor: a new voice may be chosen)."""
    if not vs:
        return _na(tr, "voice_similarity", tr("r.vq.old"))
    if not vs.get("measured"):
        return _na(tr, "voice_similarity", tr(vs.get("reason_key") or "r.vs.error"))
    med, n = vs["median"], len(vs["lines"])
    level = "good" if med >= VOICE_SIMILAR else "check"
    pct = f"{max(0.0, med) * 100:.0f}%"
    return _metric(tr, "voice_similarity", level, tr(f"r.vs.{level}", sim=pct, n=n), med,
                   tr("r.vs.display", sim=pct, n=n), tr("r.g.vs", good=f"{VOICE_SIMILAR * 100:.0f}%"))


def _speech(tr: Tr, sr: dict, lang: str, lang_name: str, vq: Optional[dict] = None,
            vs: Optional[dict] = None) -> list[dict]:
    """Right language, how clearly the voice is recognised, and script accuracy when a script exists."""
    rows = []
    expected = whisper_language(lang)
    detected, prob = sr.get("dubbed_language_detected"), sr.get("dubbed_language_probability")
    if not expected:
        rows.append(_na(tr, "language", tr("r.lang.unsupported", lang=lang_name)))
    elif detected is None:
        rows.append(_na(tr, "language", tr("r.no_speech")))
    else:
        sure = f"{prob:.0%}" if prob is not None else "?"
        if detected == expected:
            level = "good" if (prob or 0) >= LANGUAGE_PROB else "check"
            msg = tr(f"r.lang.{level}", lang=lang_name, prob=sure)
            shown = tr("r.lang.display", lang=lang_name, prob=sure)
        else:
            level, msg = "poor", tr("r.lang.poor", lang=lang_name, detected=detected)
            shown = tr("r.lang.display", lang=detected, prob=sure)
        rows.append(_metric(tr, "language", level, msg, detected, shown, tr("r.g.language", prob=f"{LANGUAGE_PROB:.0%}")))

    clarity = sr.get("clarity") or {}
    pct = clarity.get("confident_pct")
    if pct is None:
        rows.append(_na(tr, "clarity", tr("r.no_speech")))
    else:
        level = _band_min(pct, CLARITY_PCT)
        n = len(clarity.get("unclear_segments", []))
        msg = tr(f"r.clarity.{level}", pct=f"{pct:.0f}%", unclear=f"{100 - pct:.0f}%", n=n)
        rows.append(_metric(tr, "clarity", level, msg, pct, tr("r.clarity.display", pct=f"{pct:.0f}%"),
                            tr("r.g.clarity", good=f"{CLARITY_PCT[0]:g}", check=f"{CLARITY_PCT[1]:g}")))

    rows.append(_voice(tr, vq))
    rows.append(_similarity(tr, vs))
    if sr.get("accuracy_pct") is not None:
        acc = sr["accuracy_pct"]
        rows.append(_metric(tr, "script_accuracy", _band_min(acc, SCRIPT_PCT), tr("r.script", acc=f"{acc:.0f}%"),
                            acc, f"{acc:.0f}%", tr("r.g.script", good=f"{SCRIPT_PCT[0]:g}", check=f"{SCRIPT_PCT[1]:g}")))
    return rows


def _alignment(tr: Tr, ta: dict) -> list[dict]:
    """Whether the dub speaks at the same moments as the original."""
    ov = ta.get("overlap_pct")
    if ov is None:
        return [_na(tr, "speech_overlap", tr("r.align.na"))]
    level = _band_min(ov, OVERLAP_PCT)
    n = len(ta.get("mismatches", []))
    msg = tr(f"r.align.{level}", ov=f"{ov:.0f}%") + (" " + _pl(tr, "r.align.spots", n) if n else "")
    rows = [_metric(tr, "speech_overlap", level, msg, ov, tr("r.align.display", ov=f"{ov:.0f}%"),
                    tr("r.g.align", good=f"{OVERLAP_PCT[0]:g}", check=f"{OVERLAP_PCT[1]:g}"))]
    so, eo = ta.get("start_offset_sec"), ta.get("end_offset_sec")
    if so is not None and eo is not None:
        msg = tr("r.offsets", start=f"{abs(so):.1f}", start_way=tr("r.later" if so >= 0 else "r.earlier"),
                 end=f"{abs(eo):.1f}", end_way=tr("r.later" if eo >= 0 else "r.earlier"))
        rows.append(_metric(tr, "speech_offsets", "info", msg, so, f"{so:+.1f} s / {eo:+.1f} s"))
    return rows


def judge_reason(tr: Tr, tj: Optional[dict]) -> str:
    """Why the translation check didn't run, in the report language."""
    tj = tj or {}
    if tj.get("reason_key"):
        return tr(tj["reason_key"], **tj.get("reason_params", {}))
    return tj.get("reason") or tr("r.judge.off")


def _translation(tr: Tr, tj: Optional[dict], lang: str) -> list[dict]:
    """Meaning, completeness, names and numbers, and mistranslations, from the LLM judge."""
    if not tj or not tj.get("measured"):
        return [_na(tr, "translation_check", judge_reason(tr, tj))]
    score = tj["meaning_score"]
    level = _band_min(score, MEANING_SCORE)
    rows = [_metric(tr, "meaning", level, _local(tj["summary"], lang) + " " + tr(f"r.meaning.{level}"),
                    score, f"{score} / 5",
                    tr("r.g.meaning", good=MEANING_SCORE[0], check=MEANING_SCORE[1], model=tj["model"]))]
    for mid, kinds in (("completeness", ("missing", "added")), ("names_numbers", ("name_or_number",)),
                       ("mistranslations", ("mistranslation",))):
        found = [i for i in tj["issues"] if i["type"] in kinds]
        if mid == "mistranslations" and not found:
            continue
        # Issues the judge thinks may be speech-recognition errors are listed but don't change the level.
        real = [i for i in found if not i.get("may_be_recognition_error")]
        maybe = len(found) - len(real)
        major = sum(1 for i in real if i["severity"] == "major")
        level = "good" if not real else "poor" if major else "check"
        if not found:
            msg = tr(f"r.issues.none_{mid}")
        elif not real:
            msg = _pl(tr, "r.issues.maybe_only", maybe)
        else:
            msg = _pl(tr, "r.issues.found", len(real), major=major) + (
                " " + _pl(tr, "r.issues.plus_maybe", maybe) if maybe else "")
        shown = _pl(tr, "r.issues.count", len(real)) + (" · " + _pl(tr, "r.issues.maybe_count", maybe) if maybe else "")
        rows.append(_metric(tr, mid, level, msg, len(real), shown, tr("r.g.issues")))
    return rows


def _integrity(tr: Tr, vi: Optional[dict]) -> list[dict]:
    """The dub should keep the original picture: same resolution and frame rate, with an audio track."""
    if not vi:
        return [_na(tr, "file_check", tr("r.file.na"))]
    o, d = vi["original"], vi["dubbed"]
    problems, notes = [], []
    if not d["readable"]:
        problems.append(tr("r.file.unreadable"))
    if not d["has_audio"]:
        problems.append(tr("r.file.no_audio"))
    if not vi["same_resolution"]:
        notes.append(tr("r.file.resolution", orig=f"{o['width']}×{o['height']}", dub=f"{d['width']}×{d['height']}"))
    if not vi["same_fps"]:
        notes.append(tr("r.file.fps", orig=o["fps"], dub=d["fps"]))
    level = "poor" if problems else "check" if notes else "good"
    msg = (tr("r.file.ok", res=f"{d['width']}×{d['height']}", fps=d["fps"]) if level == "good"
           else " ".join(problems + notes))
    disp = f"{d['width']}×{d['height']} · {d['fps']} fps · {tr('r.file.audio_yes' if d['has_audio'] else 'r.file.audio_no')}"
    return [_metric(tr, "file_check", level, msg, level == "good", disp, tr("r.g.file"))]


def _lipsync(tr: Tr, ls: dict, is_lipsync: Optional[bool]) -> list[dict]:
    """Experimental lip movement: informational only, never part of the verdict."""
    if not ls.get("measured", True) or ls.get("reason_key") == "r.lips.skipped":
        return [_na(tr, "lip_movement", tr("r.lips.not_lipsynced") if is_lipsync is False else tr("r.lips.skipped"))]
    if not ls.get("valid"):
        why = tr(ls["reason_key"], **ls.get("reason_params", {})) if ls.get("reason_key") else ls.get("reason", "")
        return [_na(tr, "lip_movement", tr("r.lips.failed", reason=why))]
    r, orig = ls["pearson_correlation"], ls.get("original_pearson")
    msg = tr("r.lips.info", r=f"{r:+.2f}", orig=f"{orig:+.2f}" if orig is not None else "—")
    return [_metric(tr, "lip_movement", "info", msg, r, tr("r.lips.display", r=f"{r:+.2f}"))]


# ---------------- things to check ----------------
def _things_to_check(tr: Tr, r: dict, found: dict) -> list[dict]:
    """Timestamped places a person should look at, in time order: problem intervals, probable recognition
    errors (listed, never counted) and general warnings without a time."""
    items = [{"start": i["start"], "end": i["end"], "category": i["category_label"], "severity": i["severity"],
              "message": i["description"]} for i in found["intervals"] + found["possible_asr_errors"]]
    for w in r.get("warnings", []):
        text = tr(w["key"], **w.get("params", {})) if isinstance(w, dict) else str(w)
        items.append({"start": None, "end": None, "category": tr("r.cat.general"), "severity": "check", "message": text})
    return sorted(items, key=lambda x: (x["start"] is None, x["start"] or 0.0))


# ---------------- report ----------------
def _project(r: dict) -> dict:
    """What was evaluated, for the report header."""
    p, meta = r.get("pipeline", {}), r.get("metadata", {})
    share = p.get("share") or {}
    return {
        "title": share.get("title") or Path(p.get("input_video_path") or "").name,
        "perso_seq": share.get("seq"),
        "share_url": share.get("share_url"),
        "source_language": share.get("source_language_name") or meta.get("detected_source_language"),
        "target_language": p.get("target_language_name") or meta.get("target_language"),
        "target_language_code": p.get("target_language_code") or meta.get("target_language"),
        "is_lipsync": share.get("is_lipsync"),
        "evaluated_video": share.get("evaluated_video"),
        "duration_sec": r.get("acoustic_metrics", {}).get("original_duration_sec"),
        "timestamp": p.get("timestamp"),
        "whisper_model": meta.get("whisper_model"),
    }


def _headline(tr: Tr, level: str, counts: dict) -> str:
    """One or two sentences summing up the verdict."""
    if level == "good":
        return tr("r.headline.good")
    if level == "check":
        return _pl(tr, "r.headline.check", counts["check"])
    return _pl(tr, "r.headline.poor", counts["poor"]) + (
        " " + _pl(tr, "r.headline.plus_check", counts["check"]) if counts["check"] else "")


def build_report(r: dict, lang: str = DEFAULT_UI_LANGUAGE, dub: Optional[str] = None) -> dict:
    """The full report for a results dict, in lang: overall verdict, sections of measures, problem intervals and
    things to check. dub labels the intervals ("A" / "B") when two dubs are compared."""
    tr: Tr = lambda key, **p: i18n_t(key, lang, **p)
    ac, sr = r["acoustic_metrics"], r["speech_recognition"]
    project = _project(r)
    code = project["target_language_code"] or ""
    lang_name = project["target_language"] or code
    tj = r.get("translation_judge")
    if project["evaluated_video"]:
        project["evaluated_video"] = tr("r.evaluated." + ("lipsync" if project["is_lipsync"] else "dub"))
    sections = [
        {"id": "timing_audio", "metrics": _timing_audio(tr, ac, sr, code, lang_name)},
        {"id": "speech", "metrics": _speech(tr, sr, code, lang_name, r.get("voice_quality"), r.get("voice_similarity"))},
        {"id": "alignment", "metrics": _alignment(tr, r.get("timing_alignment") or {})},
        {"id": "translation", "metrics": _translation(tr, tj, lang), "note": tr("r.note.translation")},
        {"id": "integrity", "metrics": _integrity(tr, r.get("video_integrity"))},
        {"id": "lipsync", "metrics": _lipsync(tr, r.get("lipsync_metrics") or {}, project["is_lipsync"]),
         "note": tr("r.note.lipsync")},
    ]
    for s in sections:
        s["title"] = tr(f"rsec.{s['id']}")
    metrics = [m for s in sections for m in s["metrics"]]
    counts = {lv: sum(1 for m in metrics if m["level"] == lv) for lv in (*LEVELS, "not_measured")}
    level = "poor" if counts["poor"] else "check" if counts["check"] else "good"
    clipping_poor = any(m["id"] == "clipping" and m["level"] == "poor" for m in metrics)
    found = build_intervals(r, tr, lang, clipping_poor=clipping_poor, dub=dub)
    return {
        "report_version": 2,
        "lang": lang,
        "project": project,
        "overall": {"level": level, "label": tr(f"verdict.{level}"), "headline": _headline(tr, level, counts),
                    "counts": counts},
        "sections": sections,
        "problem_intervals": found["intervals"],
        "possible_asr_errors": found["possible_asr_errors"],
        "problem_seconds": found["problem_seconds"],
        "things_to_check": _things_to_check(tr, r, found),
        "not_measured": [{"id": m["id"], "label": m["label"], "reason": m["message"]} for m in metrics
                         if m["level"] == "not_measured"],
        "method": {
            "speech_recognition": f"OpenAI Whisper ({project['whisper_model']})",
            "translation_judge": (tj or {}).get("model") if (tj or {}).get("measured") else None,
            "verdict_rule": tr("verdict.rule"),
        },
        "labels": {k: tr(f"r.label.{k}") for k in ("title", "overall", "things", "nothing", "not_measured", "method",
                                                   "judged_by", "project", "languages", "length", "evaluated",
                                                   "source", "original", "dub", "evidence", "note", "generated")},
        "badges": {lv: tr("badge." + ("na" if lv == "not_measured" else lv)) for lv in (*LEVELS, "info", "not_measured")},
        "counts_text": tr("verdict.counts", good=counts["good"], check=counts["check"], poor=counts["poor"],
                          na=counts["not_measured"]),
    }


# ---------------- renderers ----------------
def render_text(rep: dict, width: int = 78) -> str:
    """The report as plain text for the terminal, in the report's language."""
    p, o, lb = rep["project"], rep["overall"], rep["labels"]
    bar, thin = "═" * width, "─" * width
    wrap = lambda text, first, rest: textwrap.wrap(text, width, initial_indent=first, subsequent_indent=rest)
    lines = [bar, f" {lb['title'].upper()}" + (p.get("timestamp") or "").rjust(max(0, width - len(lb["title"]) - 1)),
             bar, f" {lb['project']}: {p['title']}" + (f"   (Perso #{p['perso_seq']})" if p.get("perso_seq") else ""),
             f" {lb['languages']}: {p.get('source_language') or '?'} → {p.get('target_language') or '?'}"
             + (f"   {lb['length']}: {p['duration_sec']:.1f} s" if p.get("duration_sec") else "")]
    if p.get("evaluated_video"):
        lines.append(f" {lb['evaluated']}: {p['evaluated_video']}")
    if p.get("share_url"):
        lines.append(f" {lb['source']}: {p['share_url']}")
    lines += [thin, f" {lb['overall'].upper()}:  {ICONS[o['level']]}  {o['label'].upper()}     {rep['counts_text']}"]
    lines += wrap(o["headline"], " ", " ") + [thin]
    for i, s in enumerate(rep["sections"], 1):
        lines.append(f"\n {i}. {s['title'].upper()}")
        for m in s["metrics"]:
            lines.append(f"   {ICONS[m['level']]} {m['label']:<30} {m['display']}")
            lines += wrap(m["message"], "        ", "        ")
            if m.get("thresholds"):
                lines += wrap(m["thresholds"], "        · ", "          ")
        if s.get("note"):
            lines += wrap(f"{lb['note']}: {s['note']}", "      ", "      ")
    lines.append("\n" + thin + f"\n {lb['things'].upper()}")
    if rep["things_to_check"]:
        for n, item in enumerate(rep["things_to_check"], 1):
            when = fmt_time(item["start"]) + (f"–{fmt_time(item['end'])}" if item.get("end") is not None else "")
            lines += wrap(f"{n:>2}. {when or '—':<15} [{item['category']}] {item['message']}", "  ", " " * 22)
    else:
        lines.append(f"   {lb['nothing']}")
    if rep["not_measured"]:
        lines.append(thin + f"\n {lb['not_measured'].upper()}")
        for x in rep["not_measured"]:
            lines += wrap(f"· {x['label']}: {x['reason']}", "   ", "     ")
    m = rep["method"]
    lines += [thin, f" {lb['method']}: {m['speech_recognition']}"
              + (f" · {lb['judged_by']} {m['translation_judge']}" if m.get("translation_judge") else ""),
              *wrap(m["verdict_rule"], " ", " "), bar]
    return "\n".join(lines)


_CSS = """
:root{--bg:#f7f7f8;--card:#fff;--ink:#1d1d1f;--muted:#6b6b76;--line:#e4e4e8;--good:#1f8a4c;--check:#b86e00;
--poor:#c62828;--info:#5b5bd6;--na:#8a8a94;--good-bg:#e7f5ec;--check-bg:#fdf1de;--poor-bg:#fde8e8}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#111114;--card:#1b1b20;--ink:#ececf1;
--muted:#9a9aa6;--line:#2c2c33;--good:#4cc27d;--check:#f0a73a;--poor:#ef6b6b;--info:#9d9dff;--na:#77777f;
--good-bg:#15291d;--check-bg:#2e2410;--poor-bg:#321616}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,
"Segoe UI","Apple SD Gothic Neo","Malgun Gothic",sans-serif}
main{max-width:1040px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:0 0 12px}.muted{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0}
.verdict{display:flex;gap:16px;align-items:center;border-width:2px}
.verdict.good{border-color:var(--good);background:var(--good-bg)}.verdict.check{border-color:var(--check);
background:var(--check-bg)}.verdict.poor{border-color:var(--poor);background:var(--poor-bg)}
.big{font-size:24px;font-weight:700;white-space:nowrap}.meta{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:14px}
.badge{display:inline-block;padding:1px 9px;border-radius:99px;font-size:12px;font-weight:600;white-space:nowrap}
.b-good{background:var(--good-bg);color:var(--good)}.b-check{background:var(--check-bg);color:var(--check)}
.b-poor{background:var(--poor-bg);color:var(--poor)}.b-info{color:var(--info);border:1px solid var(--info)}
.b-not_measured{color:var(--na);border:1px solid var(--line)}
table{width:100%;border-collapse:collapse}td{padding:8px 6px;border-top:1px solid var(--line);vertical-align:top}
td.l{width:22%;font-weight:600}td.v{width:18%;white-space:nowrap;font-variant-numeric:tabular-nums}
.th{font-size:12px;color:var(--muted);margin-top:2px}.videos{display:grid;grid-template-columns:1fr 1fr;gap:12px}
video{width:100%;border-radius:8px;background:#000}.t{font-variant-numeric:tabular-nums;white-space:nowrap}
.note{font-size:13px;color:var(--muted);margin-top:8px}details summary{cursor:pointer;font-weight:600}
pre{white-space:pre-wrap;font:13px/1.5 ui-monospace,Menlo,monospace;margin:8px 0}
svg text{fill:var(--muted);font-size:11px}@media (max-width:640px){.videos{grid-template-columns:1fr}
td.l,td.v{width:auto}}
"""


def timeline_svg(ta: dict, duration: float, labels: tuple[str, str] = ("Original", "Dub")) -> str:
    """Two bars showing when each track speaks, with mismatches in red."""
    if not duration or not (ta.get("original_speech") or ta.get("dubbed_speech")):
        return ""
    w, x0 = 900, 70
    sx = lambda t: x0 + (w - x0 - 10) * min(max(t, 0), duration) / duration
    parts = [f'<svg viewBox="0 0 {w} 96" width="100%" role="img" aria-label="Speech timeline" '
             f'fill="currentColor" font-size="11">']
    for row, (label, key, color) in enumerate(((labels[0], "original_speech", "var(--info,#5b5bd6)"),
                                               (labels[1], "dubbed_speech", "var(--good,#1f8a4c)"))):
        y = 10 + row * 32
        parts.append(f'<text x="0" y="{y + 15}">{html.escape(label)}</text>')
        parts.append(f'<rect x="{x0}" y="{y}" width="{w - x0 - 10}" height="22" rx="4" fill="var(--line,#8884)"/>')
        for s, e in ta.get(key, []):
            parts.append(f'<rect x="{sx(s):.1f}" y="{y}" width="{max(1.0, sx(e) - sx(s)):.1f}" height="22" fill="{color}"/>')
    for m in ta.get("mismatches", []):
        parts.append(f'<rect x="{sx(m["start"]):.1f}" y="6" width="{max(1.0, sx(m["end"]) - sx(m["start"])):.1f}" '
                     f'height="62" fill="none" stroke="var(--poor,#d63b3b)" stroke-width="2" rx="3"/>')
    for i in range(0, int(duration) + 1, max(1, int(duration // 8) or 1)):
        parts.append(f'<text x="{sx(i):.1f}" y="90" text-anchor="middle">{fmt_time(i)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def render_html(rep: dict, results: Optional[dict] = None, original_src: str = "", dubbed_src: str = "") -> str:
    """A self-contained HTML report (light and dark) in the report's language; embeds the videos when given."""
    e = lambda x: html.escape(str(x)) if x is not None else ""
    p, o, lb = rep["project"], rep["overall"], rep["labels"]
    out = [f"<!doctype html><html lang={e(rep.get('lang', 'en'))}><head><meta charset=utf-8><meta name=viewport "
           f"content='width=device-width,initial-scale=1'><title>{e(lb['title'])}</title><style>{_CSS}</style>"
           f"</head><body><main>",
           f"<h1>{e(lb['title'])}</h1><div class='meta muted'><span>{e(p['title'])}</span>"
           + (f"<span>Perso #{e(p['perso_seq'])}</span>" if p.get("perso_seq") else "")
           + f"<span>{e(p.get('source_language') or '?')} → {e(p.get('target_language') or '?')}</span>"
           + (f"<span>{p['duration_sec']:.1f} s</span>" if p.get("duration_sec") else "")
           + (f"<span>{e(lb['evaluated'])}: {e(p['evaluated_video'])}</span>" if p.get("evaluated_video") else "")
           + f"<span>{e(p.get('timestamp'))}</span></div>",
           f"<div class='card verdict {o['level']}'><div class=big>{ICONS[o['level']]} {e(o['label'])}</div><div>"
           f"<div>{e(o['headline'])}</div><div class=muted>{e(rep['counts_text'])}</div></div></div>"]
    if original_src and dubbed_src:
        out.append(f"<div class='card videos'><div><b>{e(lb['original'])}</b><video controls preload=metadata "
                   f"src='{e(original_src)}'></video></div><div><b>{e(lb['dub'])}</b><video controls preload=metadata "
                   f"src='{e(dubbed_src)}'></video></div></div>")
    for i, s in enumerate(rep["sections"], 1):
        out.append(f"<div class=card><h2>{i}. {e(s['title'])}</h2><table>")
        for m in s["metrics"]:
            out.append(f"<tr><td class=l>{e(m['label'])}</td><td class=v>{e(m['display'])}</td><td>"
                       f"<span class='badge b-{m['level']}'>{e(rep['badges'][m['level']])}</span> {e(m['message'])}"
                       + (f"<div class=th>{e(m['thresholds'])}</div>" if m.get("thresholds") else "") + "</td></tr>")
        out.append("</table>" + (f"<div class=note>{e(s['note'])}</div>" if s.get("note") else ""))
        if s["id"] == "alignment" and results:
            out.append(timeline_svg(results.get("timing_alignment") or {}, p.get("duration_sec") or 0,
                                    (lb["original"], lb["dub"])))
        out.append("</div>")
    out.append(f"<div class=card><h2>{e(lb['things'])}</h2>")
    if rep["things_to_check"]:
        out.append("<table>")
        for item in rep["things_to_check"]:
            when = fmt_time(item["start"]) + (f"–{fmt_time(item['end'])}" if item.get("end") is not None else "")
            out.append(f"<tr><td class='v t'>{e(when) or '—'}</td><td><span class='badge b-{item['severity']}'>"
                       f"{e(item['category'])}</span> {e(item['message'])}</td></tr>")
        out.append("</table>")
    else:
        out.append(f"<p class=muted>{e(lb['nothing'])}</p>")
    out.append("</div>")
    if rep["not_measured"]:
        out.append(f"<div class=card><h2>{e(lb['not_measured'])}</h2><ul>" + "".join(
            f"<li><b>{e(x['label'])}</b>: {e(x['reason'])}</li>" for x in rep["not_measured"]) + "</ul></div>")
    if results:
        sr = results.get("speech_recognition", {})
        out.append(f"<div class=card><details><summary>{e(lb['evidence'])}</summary>"
                   f"<h2 style='margin-top:12px'>{e(lb['original'])}</h2>"
                   f"<pre>{e(_lines(sr.get('original_segments')) or sr.get('original_transcript'))}</pre>"
                   f"<h2>{e(lb['dub'])}</h2><pre>{e(_lines(sr.get('dubbed_segments')) or sr.get('dubbed_transcript'))}</pre>"
                   "</details></div>")
    m = rep["method"]
    out.append(f"<p class=note>{e(lb['method'])}: {e(m['speech_recognition'])}"
               + (f" · {e(lb['judged_by'])} {e(m['translation_judge'])}" if m.get("translation_judge") else "")
               + f". {e(m['verdict_rule'])} {e(lb['generated'])}</p></main></body></html>")
    return "".join(out)


def _lines(segments: Optional[list[dict]]) -> str:
    """Timestamped transcript lines for the evidence section."""
    return "\n".join(f"[{fmt_time(s['start'])}] {s['text']}" for s in segments or [] if s.get("text"))

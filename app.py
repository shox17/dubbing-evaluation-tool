"""Dubbing QA Studio: the Streamlit UI.

Three pages, picked by the router at the bottom: setup (paste a Perso share link), progress (a background job is
running) and results (the report). All fetching, measuring and report building happens in src/; this file only
shows it.
"""
import os
import html
import json
import math
import difflib
import logging
from typing import Optional

import pandas as pd
import streamlit as st

from src.evaluate import CER_LANGS, SCHEMA_VERSION, base_lang
from src.i18n import UI_LANGUAGES, pick_ui_language, translate_message
from src import i18n, perso_api
from src.jobs import get_job, start_job
from src.perso_api import PersoError, media_url, parse_share_url
from src.pipeline import load_results, run_share_evaluation, share_stages
from src.report import build_report, fmt_time, render_html
from src.translation_judge import judge_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

st.set_page_config(page_title="Dubbing QA Studio", page_icon=":material/movie:", layout="wide")

RESULTS_SCHEMA_VERSION = 6
assert RESULTS_SCHEMA_VERSION == SCHEMA_VERSION, "bump RESULTS_SCHEMA_VERSION together with evaluate.SCHEMA_VERSION"
# Widget values that must survive while the setup form is hidden (progress/results views).
FORM_KEYS = ["ui_lang", "share_url"]

for k in FORM_KEYS:
    if k in st.session_state:
        st.session_state[k] = st.session_state[k]
for k, v in {"share_url": "",
             "seek": 0}.items():
    st.session_state.setdefault(k, v)
st.session_state.setdefault("ui_lang", pick_ui_language(st.context.locale))


# ---------------- helpers ----------------
def t(key: str, /, **values) -> str:
    """Interface text for key in the language the user picked in the sidebar."""
    return i18n.t(key, st.session_state.ui_lang, **values)


@st.cache_data(ttl=300, show_spinner=False)
def shared_project(token: str) -> dict:
    """The project behind a share token (cached 5 min), or {"error": message}."""
    try:
        return perso_api.get_shared_project(token)
    except PersoError as e:
        return {"error": str(e)}


def project_info(project: dict) -> str:
    """What the share link contains, as a short markdown list: languages, length, lip-sync, videos, date, owner."""
    src, tgt = project.get("sourceLanguage") or {}, project.get("targetLanguage") or {}
    lip = bool(project.get("isLipSync") and project.get("lipSyncFileUrl"))
    videos = [t("share.video_original")] if project.get("originalFileUrl") else []
    videos += [t("share.video_dubbed")] if project.get("translatedFileUrl") else []
    videos += [t("share.video_lipsync")] if project.get("lipSyncFileUrl") else []
    rows = [(t("share.info_languages"), f"{src.get('name', '?')} → {tgt.get('name', '?')}"),
            (t("share.info_length"), f"{(project.get('durationMs') or 0) / 1000:.1f} s"),
            (t("share.info_lipsync"), t("share.yes") if lip else t("share.no")),
            (t("share.info_videos"), ", ".join(videos))]
    if project.get("createDate"):
        rows.append((t("share.info_created"), project["createDate"][:16].replace("T", " ")))
    if project.get("userName"):
        rows.append((t("share.info_owner"), project["userName"]))
    if project.get("seq"):
        rows.append((t("share.info_project"), f"#{project['seq']}"))
    return "\n".join(f"- **{label}:** {html.escape(str(value))}" for label, value in rows)


def fmt(value, pattern: str, na: str = "—") -> str:
    """Formats a number with pattern, or returns na when it wasn't measured (None)."""
    return na if value is None else pattern.format(value)


def fmt_minutes(sec: float) -> str:
    """Seconds as '2 min 05 s' (or '45 s' under a minute)."""
    m, s = divmod(int(sec), 60)
    return t("time.min_sec", m=m, s=f"{s:02d}") if m else t("time.sec", s=s)


def to_db(rms: Optional[float]) -> Optional[float]:
    """Loudness ratio or level in decibels, or None when there's nothing to convert."""
    return round(20 * math.log10(rms), 1) if rms and rms > 0 else None


def badge(level: str) -> str:
    """Coloured Good / Check / Poor / Experimental / Not scored badge for a score card."""
    level = "na" if level == "not_measured" else level
    style = {"good": "green-badge[:material/check_circle: ", "check": "orange-badge[:material/error: ",
             "poor": "red-badge[:material/cancel: ", "info": "violet-badge[:material/info: ", "na": "gray-badge["}
    return f":{style[level]}{t('badge.' + level)}]"


def open_results(results: Optional[dict] = None):
    """Switches to the results page, optionally with a given results dict (button callback)."""
    st.query_params.clear()
    st.session_state.view = "results"
    if results is not None:
        st.session_state.results = results


def new_evaluation():
    """Clears the current job and goes back to the setup page (button callback)."""
    st.query_params.clear()
    st.session_state.view = "setup"


def diff_html(reference: str, spoken: str, by_char: bool) -> str:
    """Highlights what the dub left out (red, struck) and added (green) compared with the script."""
    ref = list(reference) if by_char else reference.split()
    hyp = list(spoken) if by_char else spoken.split()
    sep = "" if by_char else " "
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_opcodes():
        a, b = html.escape(sep.join(ref[i1:i2])), html.escape(sep.join(hyp[j1:j2]))
        if op == "equal":
            out.append(a)
        if op in ("delete", "replace"):
            out.append(f"<span style='background:rgba(239,68,68,.22);text-decoration:line-through'>{a}</span>")
        if op in ("insert", "replace"):
            out.append(f"<span style='background:rgba(34,197,94,.25)'>{b}</span>")
    return f"<div style='line-height:1.9'>{sep.join(out)}</div>"


# ---------------- sidebar ----------------
with st.sidebar:
    st.header("Dubbing QA Studio", icon=":material/movie:")
    st.selectbox(f":material/language: {t('ui_language')}", list(UI_LANGUAGES), key="ui_lang",
                 format_func=UI_LANGUAGES.get)
    st.caption(t("app.tagline"))

    with st.expander(t("how.title"), icon=":material/help:"):
        st.markdown(t("how.body"))

    saved = load_results()
    if saved and saved.get("schema_version") == RESULTS_SCHEMA_VERSION and st.session_state.get("view") != "results":
        st.button(t("sidebar.last_result"), icon=":material/history:", width="stretch", on_click=open_results, args=(saved,))


# ---------------- progress view ----------------
def render_progress(job):
    """Progress page for a running job: overall %, elapsed time and a live stage checklist."""
    st.title(t("progress.title"), icon=":material/hourglass_top:")
    st.caption(html.escape(job.params.get("title") or job.params["share_url"]))

    @st.fragment(run_every=2)
    def live():
        """Redraws the progress every 2 s, and reruns the page once the job has finished."""
        if job.status != "running":
            st.rerun()
        pct = job.overall_fraction
        with st.container(horizontal=True):
            st.metric(t("progress.overall"), f"{pct * 100:.0f}%", border=True)
            st.metric(t("progress.elapsed"), fmt_minutes(job.elapsed_sec), border=True)
        st.progress(pct)

        with st.container(border=True, gap="small"):
            for key in job.stages:
                state = job.stage_state(key)
                icon = {"done": ":green[:material/check_circle:]", "active": ":violet[:material/progress_activity:]",
                        "pending": ":gray[:material/radio_button_unchecked:]", "failed": ":red[:material/cancel:]"}[state]
                title = t(f"stage.{key}")
                if state == "active":
                    detail = translate_message(job.message, st.session_state.ui_lang)
                    st.markdown(f"{icon} **{title}**  \n:gray[{html.escape(detail)}]")
                else:
                    st.markdown(f"{icon} {title}" if state != "pending" else f"{icon} :gray[{title}]")

    live()
    if st.button(t("progress.stop"), icon=":material/stop_circle:", help=t("progress.stop_help")):
        job.cancel_event.set()
        st.toast(t("progress.stopping"))


# ---------------- results view ----------------
def seek_to(sec: Optional[float]):
    """Starts both videos from sec (button callback for a thing to check)."""
    st.session_state.seek = max(0, int(sec or 0))


def speech_timeline(ta: dict):
    """Chart of when the original and the dub speak, with mismatches outlined in red."""
    rows = [{"track": t("results.original"), "start": a, "end": b} for a, b in ta.get("original_speech", [])]
    rows += [{"track": t("results.dubbed"), "start": a, "end": b} for a, b in ta.get("dubbed_speech", [])]
    if not rows:
        return
    marks = [{"start": m["start"], "end": m["end"]} for m in ta.get("mismatches", [])]
    order = [t("results.original"), t("results.dubbed")]
    st.markdown(f"**:material/timeline: {t('report.timeline_title')}**")
    marks_layer = {"data": {"values": marks},
                   "mark": {"type": "rect", "filled": False, "stroke": "#e5484d", "strokeWidth": 2},
                   "encoding": {"x": {"field": "start", "type": "quantitative"}, "x2": {"field": "end"},
                                "y": {"value": 0}, "y2": {"value": {"expr": "height"}}}}
    st.vega_lite_chart({
        "layer": [
            {"data": {"values": rows}, "mark": {"type": "bar", "cornerRadius": 2},
             "encoding": {"y": {"field": "track", "type": "nominal", "sort": order, "title": None,
                                "scale": {"paddingInner": 0.35}},
                          "x": {"field": "start", "type": "quantitative", "title": t("chart.seconds")},
                          "x2": {"field": "end"},
                          "color": {"field": "track", "type": "nominal", "sort": order, "legend": None},
                          "tooltip": [{"field": "track"}, {"field": "start", "title": "from (s)"},
                                      {"field": "end", "title": "to (s)"}]}},
        ] + ([marks_layer] if marks else []),
    }, width="stretch", height=120)
    st.caption(t("report.timeline_caption"))


def render_report(rep: dict, r: dict):
    """The verdict, every report section with its badges, and the timestamped things to check."""
    o = rep["overall"]
    c = o["counts"]
    with st.container(border=True):
        icon = {"good": ":green[:material/verified:]", "check": ":orange[:material/rule:]",
                "poor": ":red[:material/report:]"}[o["level"]]
        st.markdown(f"### {icon} {t('verdict.' + o['level'])}")
        st.markdown(o["headline"])
        st.caption(t("verdict.counts", good=c["good"], check=c["check"], poor=c["poor"], na=c["not_measured"])
                   + " · " + t("verdict.rule"))

    for i, sec in enumerate(rep["sections"], 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {sec['title']}**")
            for m in sec["metrics"]:
                c1, c2, c3 = st.columns([2, 2.2, 5.8], vertical_alignment="top")
                c1.markdown(f"**{m['label']}**")
                c2.markdown(badge(m["level"]) + ("" if m["value"] is None else f"  \n`{m['display']}`"))
                c3.markdown(html.escape(m["message"]))
                if m.get("thresholds"):
                    c3.caption(m["thresholds"])
            if sec["id"] == "alignment":
                speech_timeline(r.get("timing_alignment") or {})
            if sec.get("note"):
                st.caption(f":material/info: {sec['note']}")

    st.subheader(t("results.things_to_check"), icon=":material/checklist:")
    with st.container(border=True):
        if not rep["things_to_check"]:
            st.caption(t("report.no_things"))
        for n, item in enumerate(rep["things_to_check"]):
            c1, c2 = st.columns([2, 8], vertical_alignment="center")
            if item["start"] is not None:
                c1.button(fmt_time(item["start"]), key=f"seek_{n}", icon=":material/play_arrow:", type="tertiary",
                          help=t("report.jump_help"), on_click=seek_to, args=(item["start"],))
            until = f" :gray[(→ {fmt_time(item['end'])})]" if item.get("end") is not None else ""
            color = "red" if item["severity"] == "poor" else "orange"
            c2.markdown(f":{color}-badge[{html.escape(item['category'])}] {html.escape(item['message'])}{until}")
    if rep["not_measured"]:
        st.caption(f"**{t('report.not_measured')}:** " + " · ".join(
            f"{html.escape(x['label'])}: {html.escape(x['reason'])}" for x in rep["not_measured"]))


def render_results(r: dict):
    """Results page: the report (verdict, sections, things to check), both videos, then detailed measurements."""
    p, ac, sr, ls = r.get("pipeline", {}), r["acoustic_metrics"], r["speech_recognition"], r["lipsync_metrics"]
    # Rebuilt on every run so the page follows the interface language and the current report rules.
    rep = build_report(r, st.session_state.ui_lang)
    proj = rep["project"]
    lang = p.get("target_language_code", "ko")
    by_char = base_lang(lang) in CER_LANGS

    st.title(t("results.title"), icon=":material/analytics:")
    langs = f"{proj.get('source_language') or '?'} :material/arrow_forward: {proj.get('target_language') or '?'}"
    st.markdown(f":gray[{html.escape(proj.get('title') or '')}] :blue-badge[:material/translate: {langs}] "
                f":gray-badge[{p.get('execution_mode')}] :gray[{p.get('timestamp', '')}]"
                + (f" [{t('report.open_perso')}]({proj['share_url']})" if proj.get("share_url") else ""))
    with st.container(horizontal=True):
        st.download_button(t("report.download_html"), render_html(rep, r), file_name=f"dubbing_qa_{p.get('run_id', 'report')}.html",
                           mime="text/html", icon=":material/description:", help=t("report.download_html_help"))
        st.download_button(t("results.download"), json.dumps(r, ensure_ascii=False, indent=2),
                           file_name=f"dubbing_qa_{p.get('run_id', 'result')}.json", mime="application/json",
                           icon=":material/download:", help=t("results.download_help"))
        st.button(t("results.new"), type="primary", icon=":material/add:", on_click=new_evaluation)

    v1, v2 = st.columns(2)
    start = st.session_state.get("seek", 0)
    with v1.container(border=True):
        st.markdown(f"**{t('results.original')}**")
        if os.path.exists(p.get("input_video_path", "")):
            st.video(p["input_video_path"], start_time=start)
    with v2.container(border=True):
        st.markdown(f"**{t('results.dubbed')}** :blue-badge[{p.get('target_language_name')}]")
        if os.path.exists(p.get("dubbed_video_path", "")):
            st.video(p["dubbed_video_path"], start_time=start)
        else:
            st.warning(t("results.video_gone"), icon=":material/videocam_off:")

    render_report(rep, r)

    # ----- detailed measurements -----
    st.subheader(t("report.details"), icon=":material/table_chart:")
    st.markdown(f"**:material/compare: {t('table.title')}**")
    od, dd = ac["original_duration_sec"], ac["dubbed_duration_sec"]
    acc = sr.get("accuracy_pct")
    osr, dsr = sr.get("original_speech_rate"), sr.get("dubbed_speech_rate")
    rate = lambda x: fmt(x and x["value"], "{:.2f}") + (f" {t('unit.' + x['unit'])}" if x else "")
    pts = t("unit.pts")
    rows = [
        (t("row.duration"), f"{od:.2f} s", f"{dd:.2f} s", f"{ac['duration_diff_sec']:+.2f} s",
         t("row.duration_help")),
        (t("row.speaking"), fmt(ac.get("original_speaking_sec"), "{:.1f} s"), fmt(ac.get("dubbed_speaking_sec"), "{:.1f} s"),
         fmt(None if ac.get("original_speaking_sec") is None else ac["dubbed_speaking_sec"] - ac["original_speaking_sec"], "{:+.1f} s"),
         t("row.speaking_help")),
        (t("row.loudness"), fmt(to_db(ac["original_rms"]), "{:.1f} dBFS"), fmt(to_db(ac["dubbed_rms"]), "{:.1f} dBFS"),
         fmt(to_db(ac.get("rms_ratio")), "{:+.1f} dB"), t("row.loudness_help")),
        (t("row.steadiness"), fmt(ac.get("original_volume_stability_pct"), "{:.0f}%"),
         fmt(ac.get("dubbed_volume_stability_pct"), "{:.0f}%"),
         fmt(None if ac.get("original_volume_stability_pct") is None else ac["dubbed_volume_stability_pct"] - ac["original_volume_stability_pct"], "{:+.0f} " + pts),
         t("row.steadiness_help")),
        (t("row.silence"), f"{ac['original_silence_ratio']:.1%}", f"{ac['dubbed_silence_ratio']:.1%}",
         f"{ac['silence_diff'] * 100:+.1f} {pts}", t("row.silence_help")),
        (t("row.rate"), rate(osr), rate(dsr), "—", t("row.rate_help")),
        (t("row.lipsync"), fmt(ls.get("original_pearson"), "{:+.2f}"), fmt(ls.get("pearson_correlation"), "{:+.2f}"),
         fmt(None if ls.get("pearson_correlation") is None or ls.get("original_pearson") is None
             else ls["pearson_correlation"] - ls["original_pearson"], "{:+.2f}"),
         t("row.lipsync_help")),
        (t("row.face"), fmt(ls.get("original_face_coverage_pct"), "{:.0f}%"), fmt(ls.get("face_coverage_pct"), "{:.0f}%"),
         "—", t("row.face_help")),
    ]
    columns = [t("table.measure"), t("results.original"), t("results.dubbed"), t("table.difference"), t("table.meaning")]
    st.dataframe(pd.DataFrame(rows, columns=columns), hide_index=True, width="stretch", column_config={
        columns[0]: st.column_config.TextColumn(pinned=True),
        columns[4]: st.column_config.TextColumn(width="large"),
    })

    env = ac.get("loudness_envelope") or {}
    if env.get("original_db") and env.get("dubbed_db"):
        st.markdown(f"**:material/graphic_eq: {t('chart.loudness_title')}**")
        n = max(len(env["original_db"]), len(env["dubbed_db"]))
        pad = lambda xs: xs + [None] * (n - len(xs))
        df = pd.DataFrame({t("results.original"): pad(env["original_db"]), t("results.dubbed"): pad(env["dubbed_db"])},
                          index=pd.Index([round(i * env["step_sec"], 2) for i in range(n)], name=t("chart.seconds")))
        st.line_chart(df, y_label="dBFS", x_label=t("chart.seconds"))
        st.caption(t("chart.loudness_caption"))

    # ----- scripts -----
    st.markdown(f"**:material/record_voice_over: {t('said.title')}**")
    # A script only exists when the run came from the CLI with --script; then the diff tab is added.
    has_script = bool(sr.get("ground_truth"))
    names = [f":material/record_voice_over: {t('said.tab_dub')}", f":material/mic: {t('said.tab_original')}"]
    tabs = st.tabs(names + ([f":material/difference: {t('said.tab_script')}"] if has_script else []))
    with tabs[0]:
        st.write(sr.get("dubbed_transcript") or "—")
    with tabs[1]:
        st.caption(t("said.detected", lang=r.get("metadata", {}).get("detected_source_language", "?")))
        st.write(sr.get("original_transcript") or "—")
    if has_script:
        with tabs[2]:
            metric = (sr.get("primary_metric") or "wer").upper()
            st.caption(t("said.legend", acc=fmt(acc, "{:.0f}%"), metric=metric, err=fmt(sr.get("error_rate"), "{:.3f}")))
            st.markdown(diff_html(sr["ground_truth"], sr["dubbed_transcript"], by_char), unsafe_allow_html=True)
            st.caption(t("said.diff_note"))

    wave = ls.get("waveform_data") or {}
    if ls.get("valid") and wave.get("timestamps"):
        with st.expander(t("lips.expander"), icon=":material/science:"):
            df = pd.DataFrame({t("lips.mouth"): wave["mar_norm"], t("lips.voice"): wave["rms_norm"]},
                              index=pd.Index(wave["timestamps"], name=t("chart.seconds")))
            st.line_chart(df)
            st.caption(t("lips.caption"))


# ---------------- setup view ----------------
def render_setup():
    """Setup page: paste the link, preview the project, choose options, evaluate."""
    st.title(t("setup.title"), icon=":material/movie_edit:")
    st.markdown(f":gray[{t('setup.intro')}]")
    project, token = None, None
    with st.container(border=True):
        st.subheader(t("share.title"), icon=":material/link:")
        st.caption(t("share.caption"))
        st.text_input(t("share.label"), key="share_url", placeholder=t("share.placeholder"), label_visibility="collapsed")
        if st.session_state.share_url.strip():
            try:
                token = parse_share_url(st.session_state.share_url)
            except ValueError as e:
                st.error(translate_message(str(e), st.session_state.ui_lang), icon=":material/link_off:")
        if token:
            with st.spinner():
                project = shared_project(token)
            if "error" in project:
                st.error(translate_message(project["error"], st.session_state.ui_lang), icon=":material/error:")
                project = None
        if project:
            c1, c2 = st.columns([2, 3])
            if project.get("thumbnailUrl"):
                c1.image(media_url(project["thumbnailUrl"]))
            c2.markdown(f"**{html.escape(project.get('title') or '')}**")
            c2.markdown(project_info(project))
            if not judge_provider():
                c2.caption(f":orange[:material/key_off:] {t('share.judge_missing')}")

    if not project:
        st.warning(t("problem.share"), icon=":material/info:")
    if st.button(t("share.start"), key="start", type="primary", icon=":material/play_arrow:",
                 disabled=project is None, width="stretch"):
        params = dict(
            share_url=st.session_state.share_url.strip(),
            report_lang=st.session_state.ui_lang,
        )
        job = start_job(lambda report, cancel: run_share_evaluation(**params, report=report, cancel_event=cancel),
                        {**params, "title": project.get("title")}, share_stages())
        st.query_params["job"] = job.id
        st.rerun()


# ---------------- router ----------------
job = get_job(st.query_params.get("job"))
if job is not None and job.status == "running":
    render_progress(job)
elif job is not None and job.status == "done":
    open_results(job.result)
    st.rerun()
elif job is not None:
    cancelled = job.status == "cancelled"
    st.title(t("stopped.title") if cancelled else t("failed.title"),
             icon=":material/stop_circle:" if cancelled else ":material/error:")
    (st.info if cancelled else st.error)(translate_message(job.error or "", st.session_state.ui_lang))
    st.caption(t("stopped.during", stage=t(f"stage.{job.stage}") if f"stage.{job.stage}" in i18n.TEXT else job.stage,
                 time=fmt_minutes(job.elapsed_sec)))
    st.button(t("back"), type="primary", icon=":material/arrow_back:", on_click=new_evaluation)
elif st.query_params.get("job"):
    st.warning(t("untracked"), icon=":material/sync_problem:")
    st.button(t("back"), icon=":material/arrow_back:", on_click=new_evaluation)
elif st.session_state.get("view") == "results" and st.session_state.get("results"):
    render_results(st.session_state.results)
else:
    render_setup()

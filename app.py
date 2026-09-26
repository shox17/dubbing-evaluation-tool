"""Dubbing QA Studio: the Streamlit UI.

Three pages, picked by the router at the bottom: setup (choose video and options), progress (a background
job is running) and results. All dubbing and measuring happens in src/; this file only shows it.
"""
import os
import re
import html
import json
import math
import difflib
import logging
from typing import Optional

import pandas as pd
import streamlit as st

from src.evaluate import CER_LANGS, DEFAULT_WHISPER_MODEL, whisper_language
from src.i18n import UI_LANGUAGES, pick_ui_language, translate_message
from src import i18n
from src.jobs import get_job, start_job
from src.languages import FALLBACK_LANGUAGES
from src.perso_api import PersoClient, PersoError
from src.pipeline import (
    INPUT_DIR, SAMPLE_ORIGINAL, get_default_ground_truth, is_sample_input, load_results,
    pipeline_stages, probe_video, run_pipeline,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

st.set_page_config(page_title="Dubbing QA Studio", page_icon=":material/movie:", layout="wide")

UPLOAD_DIR = os.path.join(INPUT_DIR, "uploads")
RESULTS_SCHEMA_VERSION = 3
WHISPER_MODELS = list(dict.fromkeys(["tiny", "base", "small", "medium", DEFAULT_WHISPER_MODEL]))
# Widget values that must survive while the setup form is hidden (progress/results views).
FORM_KEYS = ["ui_lang", "video_source", "target_language", "lip_dubbing", "use_demo", "target_script", "whisper_model",
             "space_seq"]

for k in FORM_KEYS:
    if k in st.session_state:
        st.session_state[k] = st.session_state[k]
if st.session_state.get("video_source") not in (None, "sample", "upload"):
    st.session_state.video_source = "sample"  # older sessions stored the English label
for k, v in {"video_source": "sample", "target_language": "ko", "lip_dubbing": True,
             "use_demo": False, "target_script": "", "whisper_model": DEFAULT_WHISPER_MODEL}.items():
    st.session_state.setdefault(k, v)
st.session_state.setdefault("ui_lang", pick_ui_language(st.context.locale))
st.session_state.setdefault("uploaded_path", None)
st.session_state.setdefault("uploaded_id", None)


# ---------------- helpers ----------------
def t(key: str, /, **values) -> str:
    """Interface text for key in the language the user picked in the sidebar."""
    return i18n.t(key, st.session_state.ui_lang, **values)


@st.cache_data(ttl=60, show_spinner=False)
def perso_account() -> dict:
    """Workspaces with plan and credits, or an error message."""
    try:
        client = PersoClient()
        spaces = []
        for s in client.list_spaces():
            seq = s["spaceSeq"]
            try:
                status = client.plan_status(seq)
            except PersoError:
                status = {}
            spaces.append({
                "seq": seq,
                "name": s.get("spaceName") or f"Workspace {seq}",
                "plan": s.get("planName") or status.get("planTier") or "?",
                "tier": (status.get("planTier") or s.get("tier") or "").lower(),
                "credits": (status.get("remainingQuota") or {}).get("remainingQuota"),
                "default": bool(s.get("isDefaultSpaceOwned")),
            })
        if not spaces:
            return {"error_key": "account.no_workspace"}
        return {"spaces": spaces}
    except PersoError as e:
        return {"error": str(e)}


@st.cache_data(ttl=86400, show_spinner=False)
def perso_languages() -> list[dict]:
    """Every language Perso can dub into, by name. Falls back to the bundled list when Perso can't be reached."""
    try:
        languages = PersoClient().list_languages()
    except PersoError:
        languages = []
    return sorted(languages or FALLBACK_LANGUAGES, key=lambda l: l["name"])


def language_name(lang_id: str) -> str:
    """Display name for a language id (en-GB -> English (UK)); the id itself if unknown."""
    return next((l["name"] for l in perso_languages() if l["id"] == lang_id), lang_id)


@st.cache_data(ttl=300, show_spinner=False)
def credit_estimate(space_seq: int, duration_ms: int, width: int, height: int, lip_sync: bool) -> Optional[float]:
    """Perso's credit estimate for a video, cached for 5 minutes; None if Perso can't say."""
    try:
        return PersoClient().estimate_credits(space_seq, duration_ms, width, height, lip_sync)
    except PersoError:
        return None


@st.cache_data(show_spinner=False)
def video_info(path: str, mtime: float) -> Optional[dict]:
    """Duration, size and resolution of a video, or None if it can't be read. mtime busts the cache."""
    try:
        return probe_video(path)
    except ValueError:
        return None


def persist_upload(uploaded) -> str:
    """Saves an upload once per file (Streamlit reruns the script on every interaction)."""
    if st.session_state.uploaded_id != uploaded.file_id:
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(uploaded.name)) or "video.mp4"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        path = os.path.join(UPLOAD_DIR, f"{uploaded.file_id[:8]}_{safe_name}")
        with open(path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.session_state.uploaded_path = path
        st.session_state.uploaded_id = uploaded.file_id
    return st.session_state.uploaded_path


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
    style = {"good": "green-badge[:material/check_circle: ", "check": "orange-badge[:material/error: ",
             "poor": "red-badge[:material/cancel: ", "info": "violet-badge[:material/science: ", "na": "gray-badge["}
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

    st.subheader(t("account.title"), icon=":material/account_circle:")
    account = perso_account()
    selected_space = None
    if "error" in account or "error_key" in account:
        st.error(t(account["error_key"]) if "error_key" in account else account["error"], icon=":material/link_off:")
        st.caption(t("account.demo_hint"))
    else:
        spaces = account["spaces"]
        if len(spaces) > 1:
            if st.session_state.get("space_seq") not in [s["seq"] for s in spaces]:
                st.session_state.space_seq = next((s["seq"] for s in spaces if s["default"]), spaces[0]["seq"])
            st.selectbox(t("account.workspace"), options=[s["seq"] for s in spaces], key="space_seq",
                         format_func=lambda seq: next(s["name"] for s in spaces if s["seq"] == seq))
            selected_space = next(s for s in spaces if s["seq"] == st.session_state.space_seq)
        else:
            selected_space = spaces[0]
        st.markdown(f":green-badge[:material/check_circle: {t('account.connected')}] **{selected_space['name']}**")
        with st.container(horizontal=True):
            st.metric(t("account.plan"), str(selected_space["plan"]).title(), border=True)
            st.metric(t("account.credits_left"), fmt(selected_space["credits"], "{:,.0f}"), border=True,
                      help=t("account.credits_help"))
        st.button(t("account.refresh"), icon=":material/refresh:", type="tertiary", on_click=perso_account.clear)
        if selected_space["tier"] == "free":
            st.warning(t("account.free_plan"), icon=":material/warning:")

    with st.expander(t("settings.title"), icon=":material/tune:"):
        st.selectbox(t("settings.whisper"), WHISPER_MODELS, key="whisper_model", help=t("settings.whisper_help"))

    with st.expander(t("how.title"), icon=":material/help:"):
        st.markdown(t("how.body"))

    saved = load_results()
    if saved and saved.get("schema_version") == RESULTS_SCHEMA_VERSION and st.session_state.get("view") != "results":
        st.button(t("sidebar.last_result"), icon=":material/history:", width="stretch", on_click=open_results, args=(saved,))


# ---------------- progress view ----------------
def render_progress(job):
    """Progress page for a running job: overall %, time left and a live stage checklist."""
    st.title(t("progress.title"), icon=":material/hourglass_top:")
    p = job.params
    st.caption(f"{os.path.basename(p['input_video_path'])} → **{language_name(p['target_language'])}**"
               + (t("progress.with_lipsync") if p["lip_dubbing"] and not p["use_demo_mode"] else ""))

    @st.fragment(run_every=2)
    def live():
        """Redraws the progress every 2 s, and reruns the page once the job has finished."""
        if job.status != "running":
            st.rerun()
        pct = job.overall_fraction
        with st.container(horizontal=True):
            st.metric(t("progress.overall"), f"{pct * 100:.0f}%", border=True)
            st.metric(t("progress.elapsed"), fmt_minutes(job.elapsed_sec), border=True)
            st.metric(t("progress.time_left"), t("progress.about_min", n=f"{job.eta_minutes:.0f}")
                      if job.eta_minutes else "—", border=True)
        st.progress(pct)

        with st.container(border=True, gap="small"):
            for key in job.stages:
                state = job.stage_state(key)
                icon = {"done": ":green[:material/check_circle:]", "active": ":violet[:material/progress_activity:]",
                        "pending": ":gray[:material/radio_button_unchecked:]", "failed": ":red[:material/cancel:]"}[state]
                title = t(f"stage.{key}")
                if state == "active":
                    detail = translate_message(job.message, st.session_state.ui_lang)
                    if key in ("dubbing", "lipsync"):
                        detail += f" · {job.stage_fraction * 100:.0f}%"
                    if job.eta_minutes:
                        detail += " · " + t("progress.about_min_left", n=f"{job.eta_minutes:.0f}")
                    st.markdown(f"{icon} **{title}**  \n:gray[{html.escape(detail)}]")
                else:
                    st.markdown(f"{icon} {title}" if state != "pending" else f"{icon} :gray[{title}]")

        if job.stage == "lipsync":
            st.info(t("progress.lipsync_info"), icon=":material/face_retouching_natural:")

    live()
    st.caption(t("progress.leave_hint"))
    if st.button(t("progress.stop"), icon=":material/stop_circle:", help=t("progress.stop_help")):
        job.cancel_event.set()
        st.toast(t("progress.stopping"))


# ---------------- results view ----------------
def render_results(r: dict):
    """Results page: both videos, headline scores, comparison table, loudness chart and script diff."""
    p, ac, sr, ls = r.get("pipeline", {}), r["acoustic_metrics"], r["speech_recognition"], r["lipsync_metrics"]
    lang = p.get("target_language_code", "ko")
    by_char = lang in CER_LANGS

    with st.container(horizontal=True, vertical_alignment="bottom"):
        with st.container(gap="xsmall"):
            st.title(t("results.title"), icon=":material/analytics:")
            st.markdown(f":gray[{html.escape(os.path.basename(p.get('input_video_path', '')))}] "
                        f":material/arrow_forward: :blue-badge[:material/translate: {p.get('target_language_name')}] "
                        f":gray-badge[{p.get('execution_mode')}] :gray[{p.get('timestamp', '')}]")
        st.download_button(t("results.download"), json.dumps(r, ensure_ascii=False, indent=2),
                           file_name=f"dubbing_qa_{p.get('run_id', 'result')}.json", mime="application/json",
                           icon=":material/download:", help=t("results.download_help"))
        st.button(t("results.new"), type="primary", icon=":material/add:", on_click=new_evaluation)

    if r.get("warnings"):
        st.warning(f"**{t('results.things_to_check')}**\n\n" + "\n".join(f"- {w}" for w in r["warnings"]), icon=":material/warning:")

    v1, v2 = st.columns(2)
    with v1.container(border=True):
        st.markdown(f"**{t('results.original')}**")
        if os.path.exists(p.get("input_video_path", "")):
            st.video(p["input_video_path"])
    with v2.container(border=True):
        st.markdown(f"**{t('results.dubbed')}** :blue-badge[{p.get('target_language_name')}]")
        if os.path.exists(p.get("dubbed_video_path", "")):
            st.video(p["dubbed_video_path"])
        else:
            st.warning(t("results.video_gone"), icon=":material/videocam_off:")

    # ----- headline scores -----
    st.subheader(t("results.at_a_glance"), icon=":material/speed:")
    k1, k2, k3, k4 = st.columns(4)

    od, dd = ac["original_duration_sec"], ac["dubbed_duration_sec"]
    rel = abs(dd - od) / od if od else 1
    with k1.container(border=True, height="stretch"):
        st.markdown(f"**{t('card.timing')}** {badge('good' if rel <= .05 else 'check' if rel <= .15 else 'poor')}")
        st.metric(t("card.timing"), f"{ac['duration_diff_sec']:+.2f} s", label_visibility="collapsed")
        st.caption(t("card.timing_caption", dub=f"{dd:.1f}", orig=f"{od:.1f}"))

    acc = sr.get("accuracy_pct")
    with k2.container(border=True, height="stretch"):
        # Wording differences between translations count as errors here, so the bands are lenient.
        level = "na" if acc is None else "good" if acc >= 80 else "check" if acc >= 50 else "poor"
        st.markdown(f"**{t('card.script')}** {badge(level)}")
        st.metric(t("card.script"), fmt(acc, "{:.0f}%"), label_visibility="collapsed")
        st.caption(t("card.script_caption") if acc is not None else t("card.script_none"))

    vp = sr.get("vs_perso_script")
    with k3.container(border=True, height="stretch"):
        if vp:
            a = vp["accuracy_pct"]
            st.markdown(f"**{t('card.clarity')}** {badge('good' if a >= 80 else 'check' if a >= 50 else 'poor')}")
            st.metric(t("card.clarity"), f"{a:.0f}%", label_visibility="collapsed")
            st.caption(t("card.clarity_caption"))
        else:
            db = to_db(ac.get("rms_ratio"))
            level = "na" if db is None else "good" if abs(db) <= 2 else "check" if abs(db) <= 4 else "poor"
            st.markdown(f"**{t('card.loudness')}** {badge(level)}")
            st.metric(t("card.loudness"), fmt(db, "{:+.1f} dB"), label_visibility="collapsed")
            st.caption(t("card.loudness_caption"))

    with k4.container(border=True, height="stretch"):
        st.markdown(f"**{t('card.lips')}** {badge('info')}")
        if ls.get("valid"):
            st.metric(t("card.lips"), f"{ls['pearson_correlation']:+.2f}", label_visibility="collapsed")
            st.caption(t("card.lips_caption", r=fmt(ls.get("original_pearson"), "{:+.2f}")))
        else:
            st.metric(t("card.lips"), "—", label_visibility="collapsed")
            st.caption(ls.get("reason") or t("card.lips_na"))

    # ----- comparison table -----
    st.subheader(t("table.title"), icon=":material/compare:")
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
    st.subheader(t("said.title"), icon=":material/record_voice_over:")
    tabs = st.tabs([f":material/difference: {t('said.tab_script')}", f":material/translate: {t('said.tab_perso')}",
                    f":material/mic: {t('said.tab_original')}"])
    with tabs[0]:
        if sr.get("ground_truth"):
            metric = (sr.get("primary_metric") or "wer").upper()
            st.caption(t("said.legend", acc=fmt(acc, "{:.0f}%"), metric=metric, err=fmt(sr.get("error_rate"), "{:.3f}")))
            st.markdown(diff_html(sr["ground_truth"], sr["dubbed_transcript"], by_char), unsafe_allow_html=True)
            st.caption(t("said.diff_note"))
        else:
            st.caption(t("said.no_script"))
            st.markdown(f"**{t('said.heard')}** {sr.get('dubbed_transcript') or '—'}")
    with tabs[1]:
        if sr.get("perso_translation"):
            st.write(sr["perso_translation"])
            tvt = sr.get("perso_translation_vs_target")
            if tvt:
                st.caption(t("said.perso_match", pct=f"{tvt['accuracy_pct']:.0f}"))
        else:
            st.caption(t("said.perso_live_only"))
    with tabs[2]:
        st.caption(t("said.detected", lang=r.get("metadata", {}).get("detected_source_language", "?")))
        st.write(sr.get("original_transcript") or "—")

    wave = ls.get("waveform_data") or {}
    if ls.get("valid") and wave.get("timestamps"):
        with st.expander(t("lips.expander"), icon=":material/science:"):
            df = pd.DataFrame({t("lips.mouth"): wave["mar_norm"], t("lips.voice"): wave["rms_norm"]},
                              index=pd.Index(wave["timestamps"], name=t("chart.seconds")))
            st.line_chart(df)
            st.caption(t("lips.caption"))


# ---------------- setup view ----------------
def render_setup():
    """Setup page: choose a video, language and options, paste the script, then start a run."""
    st.title(t("setup.title"), icon=":material/movie_edit:")
    st.markdown(f":gray[{t('setup.intro')}]")

    # Step 1
    with st.container(border=True):
        st.subheader(t("step1.title"), icon=":material/video_library:")
        source = st.segmented_control(
            t("upload.label"), ["sample", "upload"], key="video_source", required=True, label_visibility="collapsed",
            format_func=lambda o: {"sample": ":material/smart_display: ", "upload": ":material/upload: "}[o]
            + t(f"source.{o}"))
        video_path = None
        if source == "upload":
            up = st.file_uploader(t("upload.label"), type=["mp4", "mov", "webm"], help=t("upload.help"))
            if up is not None:
                video_path = persist_upload(up)
            elif st.session_state.uploaded_path and os.path.exists(st.session_state.uploaded_path):
                video_path = st.session_state.uploaded_path
                st.caption(t("upload.earlier", name=os.path.basename(video_path)))
        else:
            video_path = SAMPLE_ORIGINAL

        info = video_info(video_path, os.path.getmtime(video_path)) if video_path and os.path.exists(video_path) else None
        if video_path and info:
            c1, c2 = st.columns([2, 3])
            c1.video(video_path)
            c2.markdown(f"**{html.escape(os.path.basename(video_path))}**")
            c2.markdown(f":gray-badge[:material/schedule: {info['duration_ms'] / 1000:.1f} s] "
                        f":gray-badge[:material/aspect_ratio: {info['width']}×{info['height']}] "
                        f":gray-badge[:material/folder: {info['size'] / 1e6:.1f} MB]")
            if source == "sample":
                c2.caption(t("sample.caption"))
        elif video_path:
            st.error(t("video.unreadable"), icon=":material/error:")

    # Step 2
    with st.container(border=True):
        st.subheader(t("step2.title"), icon=":material/tune:")
        c1, c2 = st.columns(2)
        languages = perso_languages()
        if st.session_state.target_language not in [l["id"] for l in languages]:
            st.session_state.target_language = "ko"
        c1.selectbox(t("dub_into"), [l["id"] for l in languages], key="target_language",
                     format_func=lambda i: next(l["name"] + (t("experimental_suffix") if l["experimental"] else "")
                                                for l in languages if l["id"] == i),
                     help=t("dub_into_help", n=len(languages)))
        target = next(l for l in languages if l["id"] == st.session_state.target_language)
        if not whisper_language(target["code"]):
            c1.caption(f":orange[:material/warning:] {t('no_whisper', lang=target['name'])}")
        c2.toggle(t("lipsync.toggle"), key="lip_dubbing", help=t("lipsync.help"))
        demo_ok = bool(video_path) and is_sample_input(video_path) and st.session_state.target_language == "ko"
        if demo_ok:
            st.toggle(t("demo.toggle"), key="use_demo", help=t("demo.help"))
        use_demo = demo_ok and st.session_state.get("use_demo", False)

        estimate = None
        if use_demo:
            st.success(t("cost.free"), icon=":material/redeem:")
        elif selected_space and info:
            estimate = credit_estimate(selected_space["seq"], info["duration_ms"], info["width"], info["height"],
                                       st.session_state.lip_dubbing)
            credits = selected_space["credits"]
            if estimate is not None:
                enough = credits is None or credits >= estimate
                (st.info if enough else st.error)(
                    t("cost.estimate", est=f"{estimate:,.0f}", have=fmt(credits, "{:,.0f}"))
                    + ("" if enough else t("cost.not_enough")),
                    icon=":material/toll:")

    # Step 3
    with st.container(border=True):
        lang_name = target["name"]
        st.subheader(t("step3.title"), icon=":material/description:")
        st.caption(t("step3.caption", lang=lang_name))
        if use_demo:
            st.button(t("script.paste_sample"), icon=":material/content_paste:", on_click=lambda: st.session_state.update(
                target_script=get_default_ground_truth("ko")))
        st.text_area(t("step3.title"), key="target_script", height=160, label_visibility="collapsed",
                     placeholder=t("script.placeholder", lang=lang_name))

    # Start
    problems = []
    if not video_path or not info:
        problems.append(t("problem.video"))
    if not use_demo:
        if selected_space is None:
            problems.append(t("problem.account"))
        elif selected_space["tier"] == "free":
            problems.append(t("problem.free"))
        elif estimate is not None and selected_space["credits"] is not None and selected_space["credits"] < estimate:
            problems.append(t("problem.credits"))
    for msg in problems:
        st.warning(msg, icon=":material/info:")

    label = (t("start.demo") if use_demo else
             t("start.dub_cost", est=f"{estimate:,.0f}") if estimate is not None else t("start.dub"))
    if st.button(label, key="start", type="primary", icon=":material/play_arrow:", disabled=bool(problems),
                 width="stretch"):
        params = dict(
            input_video_path=video_path,
            target_language=st.session_state.target_language,
            lip_dubbing=st.session_state.lip_dubbing,
            use_demo_mode=use_demo,
            ground_truth_text=st.session_state.get("target_script", ""),
            space_seq=selected_space["seq"] if selected_space else None,
            whisper_model_name=st.session_state.get("whisper_model", DEFAULT_WHISPER_MODEL),
        )
        job = start_job(lambda report, cancel: run_pipeline(**params, report=report, cancel_event=cancel),
                        params, pipeline_stages(use_demo, params["lip_dubbing"]))
        st.query_params["job"] = job.id
        st.rerun()


# ---------------- router ----------------
job = get_job(st.query_params.get("job"))
if job is not None and job.status == "running":
    render_progress(job)
elif job is not None and job.status == "done":
    perso_account.clear()  # the run spent credits
    open_results(job.result)
    st.rerun()
elif job is not None:
    cancelled = job.status == "cancelled"
    st.title(t("stopped.title") if cancelled else t("failed.title"),
             icon=":material/stop_circle:" if cancelled else ":material/error:")
    (st.info if cancelled else st.error)(job.error)
    st.caption(t("stopped.during", stage=t(f"stage.{job.stage}") if f"stage.{job.stage}" in i18n.TEXT else job.stage,
                 time=fmt_minutes(job.elapsed_sec)))
    if job.perso_projects:
        st.caption(t("stopped.projects") + ", ".join(
            f"[{seq}](https://perso.ai/en/workspace/vt/detail/{seq})" for seq in job.perso_projects))
    st.button(t("back"), type="primary", icon=":material/arrow_back:", on_click=new_evaluation)
elif st.query_params.get("job"):
    st.warning(t("untracked"), icon=":material/sync_problem:")
    st.button(t("back"), icon=":material/arrow_back:", on_click=new_evaluation)
elif st.session_state.get("view") == "results" and st.session_state.get("results"):
    render_results(st.session_state.results)
else:
    render_setup()

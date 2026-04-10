import threading
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src import ui_strings as ui
from src.models import TaskGradingResult
from src.pipelines import grade_exam

st.set_page_config(
    page_title=ui.APP_TITLE,
    page_icon="📐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── Shared state that survives Streamlit reruns AND module hot-reloads ────────
# We store everything in session_state so it persists across script re-executions.


def _get_executor() -> ThreadPoolExecutor:
    if "_executor" not in st.session_state:
        st.session_state._executor = ThreadPoolExecutor(max_workers=3)
    return st.session_state._executor


def _get_jobs() -> dict:
    if "_jobs" not in st.session_state:
        st.session_state._jobs = {}
    return st.session_state._jobs


def _get_lock() -> threading.Lock:
    if "_lock" not in st.session_state:
        st.session_state._lock = threading.Lock()
    return st.session_state._lock


def _grade_worker(filename: str, pdf_bytes: bytes, jobs: dict, lock: threading.Lock) -> None:
    """Run grading for a single file in a background thread."""
    with lock:
        jobs[filename] = {
            "status": "processing",
            "step": "Nahravam PDF na server... (krok 1/3)",
            "triage": None,
            "result": None,
            "error": None,
        }

    def on_progress(msg: str) -> None:
        with lock:
            if filename in jobs:
                jobs[filename]["step"] = msg

    def on_status(msg: str, remaining: float) -> None:
        with lock:
            if filename in jobs:
                jobs[filename]["step"] = f"API limit — cakam {remaining:.0f}s"

    try:
        triage, result = grade_exam(
            pdf_bytes=(pdf_bytes, filename),
            on_status=on_status,
            on_progress=on_progress,
        )
        with lock:
            if filename in jobs:
                jobs[filename]["triage"] = triage
                jobs[filename]["result"] = result
                jobs[filename]["status"] = "done"
                jobs[filename]["step"] = None
    except Exception as e:
        with lock:
            if filename in jobs:
                jobs[filename]["status"] = "error"
                jobs[filename]["error"] = str(e)[:200]
                jobs[filename]["step"] = None


def _sync_jobs() -> None:
    """Copy latest thread state from jobs dict into session_state.files."""
    jobs = _get_jobs()
    lock = _get_lock()
    with lock:
        for fname, job in jobs.items():
            if fname in st.session_state.files:
                st.session_state.files[fname].update(
                    {
                        "status": job["status"],
                        "step": job.get("step"),
                        "triage": job.get("triage"),
                        "result": job.get("result"),
                        "error": job.get("error"),
                    }
                )


# --- Custom CSS ---
st.markdown(
    """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    .stApp {
        background: linear-gradient(135deg, #F0F4FF 0%, #FAFBFF 50%, #F5F0FF 100%);
    }

    .header-card {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .header-card h1 {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        color: white !important;
    }
    .header-card p {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0;
        color: #E0E7FF;
    }

    .score-grid {
        display: grid;
        gap: 1rem;
        margin: 1.5rem 0;
    }
    .score-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .score-card.total {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border: none;
    }
    .score-card .label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    .score-card.total .label { color: #C7D2FE; }
    .score-card .value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E293B;
    }
    .score-card.total .value { color: white; }

    .triage-ok {
        background: #ECFDF5;
        border-radius: 10px;
        padding: 0.75rem 1.25rem;
        color: #065F46;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .triage-fail {
        background: #FEE2E2;
        border-radius: 10px;
        padding: 0.75rem 1.25rem;
        color: #991B1B;
        font-weight: 500;
        margin-bottom: 1rem;
    }

    .feedback-card {
        background: #F0F4FF;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        border: 1px solid #C7D2FE;
        margin-top: 1.5rem;
        font-size: 0.95rem;
        color: #3730A3;
        line-height: 1.6;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.65rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton > button[kind="primary"]:hover { opacity: 0.9; }

    [data-testid="stMetric"] { display: none; }

    .file-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: white;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .file-row.selected {
        border-color: #4F46E5;
        box-shadow: 0 2px 8px rgba(79,70,229,0.15);
    }
    .file-row .file-name {
        font-weight: 600;
        color: #1E293B;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .file-row .file-name .icon { font-size: 1.2rem; }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.25rem 0.75rem;
        border-radius: 99px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge.waiting { background: #F1F5F9; color: #64748B; }
    .badge.processing { background: #FEF3C7; color: #92400E; }
    .badge.done { background: #ECFDF5; color: #065F46; }
    .badge.error { background: #FEE2E2; color: #991B1B; }
    .badge .dot {
        width: 6px; height: 6px; border-radius: 50%;
    }
    .badge.waiting .dot { background: #94A3B8; }
    .badge.processing .dot { background: #D97706; animation: pulse 1.5s infinite; }
    .badge.done .dot { background: #059669; }
    .badge.error .dot { background: #DC2626; }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    .score-inline {
        font-weight: 700;
        font-size: 0.95rem;
        margin-left: 0.75rem;
    }
    .score-inline.green { color: #059669; }
    .score-inline.orange { color: #D97706; }
    .score-inline.red { color: #DC2626; }
</style>
""",
    unsafe_allow_html=True,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _score_color(score: float, max_score: float) -> str:
    ratio = score / max_score if max_score else 0
    if ratio >= 1.0:
        return "green"
    elif ratio >= 0.6:
        return "orange"
    return "red"


def _display_task(task: TaskGradingResult) -> None:
    color = _score_color(task.total_score, task.max_possible_score)
    with st.expander(
        f"{task.task_name} — :{color}[{task.total_score} / {task.max_possible_score}]",
        expanded=True,
    ):
        for comp in task.component_scores:
            c1, c2, c3 = st.columns([3, 1, 2])
            with c1:
                st.write(f"**{comp.component_name}**")
            with c2:
                comp_color = _score_color(comp.awarded_points, comp.max_points)
                st.write(f":{comp_color}[{comp.awarded_points} / {comp.max_points}]")
            with c3:
                if comp.note:
                    st.caption(comp.note)
            st.divider()

        if task.mistakes:
            st.subheader(ui.RESULT_MISTAKES)
            for m in task.mistakes:
                st.warning(
                    f"**{m.question_number_or_topic}**: {m.correction} (**-{m.points_deducted}b**)"
                )
        else:
            st.success(ui.RESULT_NO_MISTAKES)

        with st.expander(ui.RESULT_RECOGNIZED):
            st.text(task.recognized_data)
        with st.expander(ui.RESULT_VERIFICATION):
            st.text(task.verification_notes)


def _display_result(filename: str) -> None:
    """Display full grading result for a file — identical to original single-file output."""
    entry = st.session_state.files.get(filename, {})
    triage = entry.get("triage")
    result = entry.get("result")

    if not triage:
        return

    if triage.is_readable:
        st.markdown(
            f'<div class="triage-ok">Dokument je citatelny — {triage.reason}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
        <div class="triage-fail">
            <strong>Dokument NIE je citatelny</strong> — vyzaduje manualnu kontrolu<br>
            <span style="font-weight:400;">{triage.reason}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    if result is None:
        return

    n_tasks = len(result.tasks)
    score_cards = ""
    grid_cols = f"repeat({n_tasks + 1}, 1fr)"
    for task in result.tasks:
        score_cards += f"""
        <div class="score-card">
            <div class="label">{task.task_name}</div>
            <div class="value">{task.total_score} / {task.max_possible_score}</div>
        </div>"""
    score_cards += f"""
    <div class="score-card total">
        <div class="label">Celkove skore</div>
        <div class="value">{result.total_score} / {result.max_possible_score}</div>
    </div>"""

    st.markdown(
        f'<div class="score-grid" style="grid-template-columns:{grid_cols};">{score_cards}</div>',
        unsafe_allow_html=True,
    )

    for task in result.tasks:
        _display_task(task)

    if result.feedback_summary:
        st.markdown(
            f"""
        <div class="feedback-card">
            <div style="font-weight:600;margin-bottom:0.5rem;">Spatna vazba</div>
            {result.feedback_summary}
        </div>
        """,
            unsafe_allow_html=True,
        )


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    if "files" not in st.session_state:
        st.session_state.files = {}
    if "selected_file" not in st.session_state:
        st.session_state.selected_file = None

    # Sync thread results into session_state on every rerun
    _sync_jobs()

    # --- Header ---
    st.markdown(
        """
    <div class="header-card">
        <h1>Automaticke hodnotenie matematickych skusok</h1>
        <p>Nahrajte naskenovane skusky pre automaticke hodnotenie</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # --- Multi-file upload ---
    uploaded_files = st.file_uploader(
        ui.UPLOAD_LABEL,
        type=ui.UPLOAD_TYPES,
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if not uploaded_files:
        st.markdown(
            """
        <div style="text-align:center;padding:2rem 0;color:#94A3B8;">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">📄</div>
            <div>Nahrajte PDF subory so skuskami pre zacatie hodnotenia</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.session_state.files = {}
        st.session_state.selected_file = None
        jobs = _get_jobs()
        lock = _get_lock()
        with lock:
            jobs.clear()
        return

    # Sync uploaded files → session_state
    current_names = {f.name for f in uploaded_files}
    for name in list(st.session_state.files.keys()):
        if name not in current_names:
            del st.session_state.files[name]
            jobs = _get_jobs()
            lock = _get_lock()
            with lock:
                jobs.pop(name, None)
    if st.session_state.selected_file not in current_names:
        st.session_state.selected_file = None
    for f in uploaded_files:
        if f.name not in st.session_state.files:
            st.session_state.files[f.name] = {
                "bytes": f.read(),
                "status": "waiting",
                "step": None,
                "triage": None,
                "result": None,
                "error": None,
            }

    # --- Grade button ---
    any_waiting = any(e["status"] == "waiting" for e in st.session_state.files.values())

    if any_waiting and st.button(ui.BUTTON_GRADE, type="primary"):
        jobs = _get_jobs()
        lock = _get_lock()
        for name, entry in st.session_state.files.items():
            if entry["status"] == "waiting":
                entry["status"] = "processing"
                entry["step"] = "Nahravam PDF na server... (krok 1/3)"
                _get_executor().submit(_grade_worker, name, entry["bytes"], jobs, lock)
        st.rerun()

    # --- File list ---
    if st.session_state.files:
        st.markdown(
            f"<div style='margin:0.5rem 0 0.25rem;font-weight:600;color:#475569;"
            f"font-size:0.9rem;'>Nahranych suborov: {len(st.session_state.files)}</div>",
            unsafe_allow_html=True,
        )

    for filename, entry in st.session_state.files.items():
        status = entry["status"]
        step = entry.get("step")
        is_selected = st.session_state.selected_file == filename

        badge_cls = status
        if status == "waiting":
            badge_text = "Caka"
        elif status == "processing":
            badge_text = step or "Spracovava sa..."
        elif status == "done":
            badge_text = "Hotovo"
        else:
            badge_text = "Chyba"

        badge_html = (
            f'<span class="badge {badge_cls}"><span class="dot"></span>{badge_text}</span>'
        )

        score_html = ""
        if status == "done" and entry.get("result"):
            r = entry["result"]
            clr = _score_color(r.total_score, r.max_possible_score)
            score_html = (
                f'<span class="score-inline {clr}">{r.total_score} / {r.max_possible_score}</span>'
            )
        elif status == "done" and entry.get("triage") and not entry["triage"].is_readable:
            score_html = '<span class="score-inline red">Necitatelny</span>'

        sel_cls = " selected" if is_selected else ""

        st.markdown(
            f'<div class="file-row{sel_cls}">'
            f'  <div class="file-name"><span class="icon">📄</span> {filename}</div>'
            f"  <div>{badge_html}{score_html}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        if status in ("done", "error"):
            label = "Skryt vysledky" if is_selected else "Zobrazit vysledky"
            if st.button(label, key=f"btn_{filename}", use_container_width=True):
                st.session_state.selected_file = None if is_selected else filename
                st.rerun()

    # --- Detail view ---
    selected = st.session_state.selected_file
    if selected and selected in st.session_state.files:
        entry = st.session_state.files[selected]
        st.markdown("---")
        st.markdown(
            f"<h3 style='color:#1E293B;'>Vysledky: {selected}</h3>",
            unsafe_allow_html=True,
        )
        if entry["status"] == "done":
            _display_result(selected)
        elif entry["status"] == "error":
            err = entry.get("error", "Neznama chyba")
            if "429" in err or "quota" in err.lower() or "ResourceExhausted" in err:
                st.error(ui.ERROR_RATE_LIMIT_EXHAUSTED)
            else:
                st.error(ui.ERROR_GRADING_FAILED.format(detail=err))

    # --- Auto-refresh while processing ---
    any_processing = any(e["status"] == "processing" for e in st.session_state.files.values())
    if any_processing:
        st_autorefresh(interval=2000, limit=None, key="auto_refresh")


if __name__ == "__main__":
    main()

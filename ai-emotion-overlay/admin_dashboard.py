"""
============================================================
Admin Dashboard — CLI Session Viewer
View all past sessions, export data, and generate graphs.
Run: python admin_dashboard.py
============================================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from loguru import logger
from backend.session_logger import SessionLogger
from backend.emotion_graph import EmotionHistoryGraph


def load_config():
    try:
        with open("configs/config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception:
        return {}


def print_header():
    print("\n" + "="*60)
    print("  AI FACE EMOTION OVERLAY — ADMIN DASHBOARD")
    print("="*60)


def list_sessions(logger_inst: SessionLogger):
    sessions = logger_inst.get_all_sessions()
    if not sessions:
        print("\n  No sessions recorded yet.")
        return []

    print(f"\n  {'ID':<5} {'Start Time':<22} {'End Time':<22} {'Frames':<8} {'Source'}")
    print("  " + "-"*72)
    for s in sessions:
        sid = s.get("id", "-")
        start = s.get("start_time", "-")[:19]
        end = (s.get("end_time") or "-")[:19]
        frames = s.get("total_frames", 0)
        source = s.get("source", "-")
        print(f"  {sid:<5} {start:<22} {end:<22} {frames:<8} {source}")
    return sessions


def show_session_detail(logger_inst: SessionLogger, session_id: int):
    summary = logger_inst.get_session_summary(session_id)
    if not summary:
        print(f"  No data for session {session_id}")
        return

    print(f"\n  Session {session_id} Summary")
    print("  " + "-"*40)
    print(f"  Total frames logged: {summary.get('total_frames', 0)}")
    print()

    from backend.emotion_classifier import EMOTION_LABELS
    for e in EMOTION_LABELS:
        val = summary.get(f"avg_{e}", 0.0) or 0.0
        bar = "█" * int(val * 30)
        print(f"  {e.capitalize():<10} {bar:<30} {val*100:.1f}%")


def main():
    print_header()
    config = load_config()
    db_path = config.get("session", {}).get("db_path", "outputs/sessions.db")
    csv_dir = config.get("session", {}).get("csv_dir", "outputs/csv")

    logger_inst = SessionLogger(db_path=db_path, csv_dir=csv_dir)
    grapher = EmotionHistoryGraph(output_dir="outputs")

    while True:
        print("\n  Options:")
        print("  [1] List all sessions")
        print("  [2] View session detail")
        print("  [3] Export session as CSV")
        print("  [4] Generate emotion history graph")
        print("  [5] Generate emotion pie chart")
        print("  [q] Quit")

        choice = input("\n  Enter choice: ").strip().lower()

        if choice == "q":
            print("  Goodbye!")
            break

        elif choice == "1":
            list_sessions(logger_inst)

        elif choice == "2":
            sessions = list_sessions(logger_inst)
            if sessions:
                sid = input("  Enter session ID: ").strip()
                try:
                    show_session_detail(logger_inst, int(sid))
                except ValueError:
                    print("  Invalid session ID")

        elif choice == "3":
            list_sessions(logger_inst)
            sid = input("  Enter session ID to export: ").strip()
            try:
                path = logger_inst.export_csv(session_id=int(sid))
                if path:
                    print(f"  ✓ CSV exported: {path}")
                else:
                    print("  Export failed")
            except ValueError:
                print("  Invalid ID")

        elif choice == "4":
            list_sessions(logger_inst)
            sid = input("  Enter session ID: ").strip()
            try:
                sid_int = int(sid)
                timeline = logger_inst.get_emotion_timeline(sid_int, downsample=3)
                path = grapher.export_session_graph(
                    timeline,
                    session_id=sid_int,
                    title=f"Session {sid_int} Emotion Timeline"
                )
                if path:
                    print(f"  ✓ Graph saved: {path}")
            except ValueError:
                print("  Invalid ID")

        elif choice == "5":
            list_sessions(logger_inst)
            sid = input("  Enter session ID: ").strip()
            try:
                sid_int = int(sid)
                summary = logger_inst.get_session_summary(sid_int)
                path = grapher.export_dominant_pie(summary, session_id=sid_int)
                if path:
                    print(f"  ✓ Pie chart saved: {path}")
            except ValueError:
                print("  Invalid ID")

        else:
            print("  Unknown option")


if __name__ == "__main__":
    main()

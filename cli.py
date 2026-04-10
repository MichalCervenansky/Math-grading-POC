import argparse
import sys
from pathlib import Path

from src import ui_strings as ui
from src.models import TaskGradingResult
from src.pipelines import grade_exam

# ANSI colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _print_status(msg: str, remaining: float = 0) -> None:
    print(f"\r{CYAN}[WAIT] {msg}{RESET}", end="", file=sys.stderr, flush=True)
    if remaining <= 1:
        print(file=sys.stderr)  # newline after countdown finishes


def _print_progress(msg: str) -> None:
    print(f"{CYAN}[INFO] {msg}{RESET}", file=sys.stderr)


def _print_task(task: TaskGradingResult) -> None:
    print(f"\n{BOLD}{'=' * 44}")
    print(f"  {task.task_name}")
    color = GREEN if task.total_score == task.max_possible_score else YELLOW
    print(f"  {ui.RESULT_SCORE}: {color}{task.total_score} / {task.max_possible_score}{RESET}")
    print(f"{'=' * 44}{RESET}")

    for comp in task.component_scores:
        color = GREEN if comp.awarded_points == comp.max_points else YELLOW
        note = f"  ({comp.note})" if comp.note else ""
        print(
            f"  {comp.component_name:.<35} "
            f"{color}{comp.awarded_points} / {comp.max_points}{RESET}{note}"
        )

    if task.mistakes:
        print(f"\n  {RED}{ui.RESULT_MISTAKES}:{RESET}")
        for m in task.mistakes:
            print(f"  {RED}- {m.correction} (-{m.points_deducted}b){RESET}")
    else:
        print(f"\n  {GREEN}{ui.RESULT_NO_MISTAKES}{RESET}")


def main() -> None:
    parser = argparse.ArgumentParser(description=ui.CLI_DESCRIPTION)
    parser.add_argument("--file", "-f", required=True, help=ui.CLI_FILE_HELP)
    parser.add_argument("--rubric", "-r", default=None, help=ui.CLI_RUBRIC_HELP)
    parser.add_argument("--api-key", "-k", default=None, help=ui.CLI_API_KEY_HELP)
    args = parser.parse_args()

    pdf_path = args.file
    if not Path(pdf_path).exists():
        print(f"{RED}Chyba: Subor '{pdf_path}' neexistuje.{RESET}", file=sys.stderr)
        sys.exit(1)

    rubric_text = None
    if args.rubric:
        rubric_path = Path(args.rubric)
        if not rubric_path.exists():
            print(
                f"{RED}Chyba: Subor s rubrikou '{args.rubric}' neexistuje.{RESET}",
                file=sys.stderr,
            )
            sys.exit(1)
        rubric_text = rubric_path.read_text(encoding="utf-8")

    try:
        triage, result = grade_exam(
            pdf_path=pdf_path,
            rubric_text=rubric_text,
            api_key=args.api_key,
            on_status=_print_status,
            on_progress=_print_progress,
        )
    except RuntimeError as e:
        print(f"{RED}Chyba: {e}{RESET}", file=sys.stderr)
        sys.exit(1)

    # Triage result
    if triage.is_readable:
        print(f"\n{GREEN}[OK] {ui.RESULT_READABLE}{RESET}")
    else:
        print(f"\n{RED}[!] {ui.RESULT_NOT_READABLE}{RESET}")
        print(f"    {ui.RESULT_REASON}: {triage.reason}")
        sys.exit(0)

    if result is None:
        sys.exit(0)

    # Grading results
    for task in result.tasks:
        _print_task(task)

    # Total
    print(f"\n{BOLD}{'=' * 44}")
    color = GREEN if result.total_score == result.max_possible_score else YELLOW
    print(f"  {ui.RESULT_TOTAL}: {color}{result.total_score} / {result.max_possible_score}{RESET}")
    print(f"{'=' * 44}{RESET}")

    # Feedback
    if result.feedback_summary:
        print(f"\n{ui.RESULT_FEEDBACK}: {result.feedback_summary}")


if __name__ == "__main__":
    main()

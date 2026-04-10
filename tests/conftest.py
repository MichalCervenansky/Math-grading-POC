import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

from src.models import (  # noqa: E402
    GradingResult,
    MistakeDetail,
    TaskComponentScore,
    TaskGradingResult,
    TriageResult,
)


def pytest_collection_modifyitems(config, items):
    """Auto-skip e2e tests when GEMINI_API_KEY is not set."""
    skip_e2e = pytest.mark.skip(reason="GEMINI_API_KEY not set -- skipping E2E test")
    for item in items:
        if "e2e" in item.keywords and not os.environ.get("GEMINI_API_KEY"):
            item.add_marker(skip_e2e)


@pytest.fixture
def sample_triage_readable():
    return TriageResult(is_readable=True, reason="Dokument je citatelny")


@pytest.fixture
def sample_triage_unreadable():
    return TriageResult(is_readable=False, reason="Necitatelne")


@pytest.fixture
def sample_grading_result():
    return GradingResult(
        tasks=[
            TaskGradingResult(
                task_name="Uloha 4",
                total_score=3.5,
                max_possible_score=5.0,
                component_scores=[
                    TaskComponentScore(
                        component_name="Zobrazenie bodov",
                        max_points=1.0,
                        awarded_points=1.0,
                        note="Spravne",
                    ),
                    TaskComponentScore(
                        component_name="Grafika",
                        max_points=1.0,
                        awarded_points=1.0,
                        note="Spravne",
                    ),
                    TaskComponentScore(
                        component_name="Vseobecne rovnice",
                        max_points=1.0,
                        awarded_points=0.5,
                        note="Jedna chyba",
                    ),
                    TaskComponentScore(
                        component_name="Parametricke rovnice",
                        max_points=1.0,
                        awarded_points=0.5,
                        note="Jedna chyba",
                    ),
                    TaskComponentScore(
                        component_name="Smernicovy tvar",
                        max_points=1.0,
                        awarded_points=0.5,
                        note="Jedna chyba",
                    ),
                ],
                mistakes=[
                    MistakeDetail(
                        question_number_or_topic="Rovnica priamky AB",
                        student_answer="-8 + 48 = 0",
                        correct_answer="-8x + 48 = 0",
                        correction="Chyba premenna x",
                        points_deducted=0.5,
                    ),
                ],
                recognized_data="Body A(2,3), B(8,3)...",
                verification_notes="Overenie rovnic...",
            ),
        ],
        total_score=3.5,
        max_possible_score=5.0,
        feedback_summary="Celkove dobre riesenie s drobnymi chybami.",
    )


@pytest.fixture
def mat4_pdf_path():
    path = Path(__file__).parent.parent / "test_examples" / "mat4.pdf"
    assert path.exists(), f"Test PDF not found: {path}"
    return path

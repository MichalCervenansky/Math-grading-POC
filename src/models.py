from pydantic import BaseModel, Field


class TriageResult(BaseModel):
    is_readable: bool = Field(description="Whether the solution is legible")
    reason: str = Field(description="Reason for the legibility assessment")


class TaskComponentScore(BaseModel):
    component_name: str = Field(description="Name of the grading component")
    max_points: float
    awarded_points: float
    note: str = Field(description="Note about this component's grading")


class MistakeDetail(BaseModel):
    question_number_or_topic: str
    student_answer: str
    correct_answer: str
    correction: str
    points_deducted: float


class TaskGradingResult(BaseModel):
    task_name: str = Field(description="Name or number of the task")
    total_score: float
    max_possible_score: float
    component_scores: list[TaskComponentScore]
    mistakes: list[MistakeDetail]
    recognized_data: str = Field(
        description="All data recognized from the student's solution (Phase 1: Recognition)"
    )
    verification_notes: str = Field(
        description=(
            "Independent verification computations and comparison "
            "with student answers (Phase 2: Verification)"
        )
    )


class GradingResult(BaseModel):
    tasks: list[TaskGradingResult]
    total_score: float = Field(description="Sum of all task scores")
    max_possible_score: float = Field(description="Maximum possible total score")
    feedback_summary: str = Field(description="Overall grading summary in Slovak")

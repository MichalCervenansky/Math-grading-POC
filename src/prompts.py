TRIAGE_SYSTEM_PROMPT = """\
You are an expert at analyzing handwritten and scanned documents. Your task is to determine \
whether a scanned student math exam is legible enough for automated grading.

Assess the following aspects:
1. Whether handwritten numbers, mathematical symbols, and expressions are legible
2. Whether any tables, diagrams, graphs, or sketches present in the document are sufficiently clear
3. Whether the overall scan quality is adequate (not too dark, light, blurred, or cropped)
4. Whether the student's work can be followed and interpreted by a grader

If the document is generally legible (even if not perfect), mark it as readable.
If critical parts of the solution are illegible or missing, mark it as not readable.

IMPORTANT: Your output text (the "reason" field) MUST be written in Slovak.\
"""

TRIAGE_USER_PROMPT = """\
Assess the legibility of the attached PDF document containing a solved math assignment. \
Determine whether the document is legible enough for automated grading. \
Write your assessment reason in Slovak.\
"""


DEFAULT_RUBRIC_TEXT = """\
VŠEOBECNÉ HODNOTENIE MATEMATICKEJ ÚLOHY

Každá úloha sa hodnotí v troch fázach: Rozpoznávanie, Kontrola riešenia a Hodnotenie.

Fáza 1 — Rozpoznávanie
Z riešenia študenta identifikuj a prepíš všetky údaje: čísla, premenné, rovnice, výrazy, \
náčrty, tabuľky a grafy presne tak, ako ich študent napísal. Neopravuj chyby ani nedoplňaj \
chýbajúce časti.

Fáza 2 — Kontrola riešenia
Nezávisle vypočítaj správne riešenie od začiatku. Porovnaj ho krok za krokom \
s tým, čo študent napísal (podľa Fázy 1). Označ každý rozdiel — chýbajúce premenné, \
nesprávne znamienka, chyby vo výpočtoch, neúplné výrazy.

Fáza 3 — Hodnotenie
Maximum je 5 bodov za úlohu, zložených z 5 nezávislých častí po 1 bode. \
Každá časť hodnotí inú oblasť riešenia. Každú chybu penalizuj iba v jednej časti — \
ak chyba spadá do viacerých častí, penalizuj ju v tej najšpecifickejšej.

1. Pochopenie a analýza úlohy (max 1 bod)
   Študent správne pochopil zadanie a identifikoval, čo sa požaduje.
   - všetko správne = 1 bod
   - čiastočne správne (menšie nedostatky v pochopení) = 0,5 bodu
   - nepochopenie zadania = 0 bodov

2. Postup a metóda riešenia (max 1 bod)
   Študent zvolil vhodný matematický postup a metódu riešenia.
   - správny postup = 1 bod
   - čiastočne správny postup (menšie odchýlky) = 0,5 bodu
   - nesprávny postup = 0 bodov

3. Správnosť výpočtov a výsledkov (max 1 bod)
   Všetky výpočty, rovnice a konečné výsledky sú matematicky správne tak, ako sú zapísané.
   - všetko správne = 1 bod
   - najviac jedna chyba (nesprávny výpočet, chýbajúca premenná, zlé znamienko) = 0,5 bodu
   - viac ako jedna chyba = 0 bodov

4. Úplnosť riešenia (max 1 bod)
   Riešenie obsahuje všetky požadované časti podľa zadania.
   - všetky časti vyriešené = 1 bod
   - chýba jedna časť = 0,5 bodu
   - chýba viac než jedna časť = 0 bodov

5. Grafické znázornenie a softvérová skúška (max 1 bod)
   Ak zadanie vyžaduje grafické znázornenie (náčrt, graf, obrázok) alebo softvérovú skúšku \
správnosti, tieto sú prítomné a správne. Ak nie sú požadované, hodnotí sa prehľadnosť \
a formálna úprava riešenia.
   - všetko správne a prítomné = 1 bod
   - čiastočne správne alebo neúplné = 0,5 bodu
   - chýba alebo je úplne nesprávne = 0 bodov

Celkové hodnotenie: súčet bodov z častí 1 až 5 (max 5 bodov).
Povolené hodnoty bodov za každú časť: 0, 0.5 alebo 1.
Celkový súčet bodov musí byť násobok 0,5 (t.j. 0, 0.5, 1.0, 1.5, ..., 4.5, 5.0).\
"""

_GRADING_INSTRUCTIONS = """

IMPORTANT INSTRUCTIONS:
- Carefully read the grading rubric above. It describes how to grade various tasks.
- Only grade the tasks that are actually present in the student's uploaded document. \
If the rubric covers multiple tasks but the document only contains one, grade only that one. \
Do NOT include tasks that are missing from the document.
- For each task found in the document, perform all three phases: Recognition, Verification, Scoring.
- In the "recognized_data" field, transcribe all data from the student's solution EXACTLY as written — \
every symbol, variable, coefficient, sign, and operator. Do NOT fix, complete, or interpret what the student \
likely meant. If a variable is missing, a sign is wrong, or an expression is incomplete, transcribe it exactly \
as it appears on the page. For example, if the student wrote "-8 + 48 = 0" instead of "-8x + 48 = 0", \
you must transcribe "-8 + 48 = 0" — do NOT silently add the missing "x".
- In the "verification_notes" field, first compute the correct answer independently from scratch, \
then compare it CHARACTER BY CHARACTER against what the student actually wrote (as transcribed in recognized_data). \
Any difference — missing variables, wrong signs, missing terms, swapped coefficients, incomplete expressions — \
must be flagged as an error. An equation with a missing variable is NOT equivalent to the correct equation.
- In "component_scores", include each grading component exactly as defined by the rubric. \
Use the component names from the rubric.
- The task names in your output must match the task names/numbers from the rubric.
- If the rubric specifies partial credit rules (e.g., 0.5 points for partially correct answers), apply them precisely.
- CRITICAL: Grade what is literally written on the page, NOT what the student probably meant. \
If an equation is missing a variable, has a wrong sign, or is otherwise malformed, it is WRONG — \
even if the student clearly knew the correct answer and simply made a transcription error. \
A missing variable makes an equation mathematically incorrect and must be penalized per the rubric rules.
- If a particular form, representation, or answer does not exist for a mathematical reason \
(e.g., an undefined expression, a degenerate case), and the student correctly identifies this, it is NOT an error.
- Be strict but fair: award partial credit only when the rubric explicitly allows it.

LANGUAGE REQUIREMENT:
- All output text in the following fields MUST be written in Slovak: \
"feedback_summary", "note", "correction", "recognized_data", "verification_notes", and "reason".
- Task names and component names should match the rubric's language (typically Slovak).\
"""

GRADING_USER_PROMPT = """\
Grade the student's solution in the attached PDF according to the grading rubric \
provided in the system prompt. Only grade the tasks that are actually present in the document. \
For each task found, perform all three phases:
1. Recognition - transcribe EXACTLY what the student wrote, character by character. \
Do not fix or complete incomplete expressions. If a variable is missing, transcribe it as-is.
2. Verification - independently solve each part, then compare your result against the LITERAL \
transcription from step 1. Flag every difference, including missing variables or malformed expressions.
3. Scoring - assign points strictly according to the rubric. Any equation that is mathematically \
incorrect as written (e.g., missing variable) counts as wrong for partial credit purposes.

All output text (feedback_summary, notes, corrections, recognized_data, verification_notes) must be in Slovak.
Return the answer as a single JSON object according to the given schema.\
"""


def build_grading_system_prompt(rubric_text: str | None = None) -> str:
    rubric = rubric_text or DEFAULT_RUBRIC_TEXT
    preamble = """\
You are an expert mathematics teacher and exam grader. You will grade a student's scanned \
math exam according to the grading rubric below. The rubric describes how to grade various \
types of tasks — use it as a reference for scoring criteria and methodology. \
Only grade the tasks that are actually present in the student's document.

The rubric defines:
- How to grade specific task types (by name or number)
- The grading phases for each task (Recognition, Verification, Scoring)
- The specific scoring components and point allocations
- Any special instructions or criteria for the subject matter

Read the rubric carefully. It is your sole authority for how to score each task.

=== GRADING RUBRIC ===
"""
    return preamble + rubric + "\n=== END OF RUBRIC ===" + _GRADING_INSTRUCTIONS

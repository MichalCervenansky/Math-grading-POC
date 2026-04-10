# --- Aplikacia ---
APP_TITLE = "Automaticke hodnotenie matematickych skusok"
APP_DESCRIPTION = "Nahrajte naskenovanu skusku pre automaticke hodnotenie"

# --- Bocny panel ---
SIDEBAR_API_KEY_LABEL = "Google Gemini API kluc"
SIDEBAR_API_KEY_HELP = "Zadajte vas API kluc pre Gemini 2.5 Pro"
SIDEBAR_RUBRIC_LABEL = "Hodnotiace kriteria (rubrika)"
SIDEBAR_RUBRIC_HELP = "Upravte hodnotiace kriteria alebo ponechajte predvolene"

# --- Nahratie suboru ---
UPLOAD_LABEL = "Nahrat PDF subor so skuskou"
UPLOAD_TYPES = ["pdf"]

# --- Priebeh ---
PROGRESS_UPLOADING = "Nahravam PDF na server... (krok 1/3)"
PROGRESS_TRIAGE = "Kontrolujem citatelnost dokumentu... (krok 2/3)"
PROGRESS_GRADING = "Hodnotim riesenie... (krok 3/3)"
PROGRESS_RATE_LIMIT = "Cakam na uvolnenie API limitu... ({seconds:.0f}s)"
PROGRESS_CLEANUP = "Cistim docasne subory..."

# --- Vysledky ---
RESULT_READABLE = "Dokument je citatelny"
RESULT_NOT_READABLE = "Dokument NIE je citatelny - vyzaduje manualnu kontrolu"
RESULT_REASON = "Dovod"
RESULT_SCORE = "Skore"
RESULT_COMPONENT = "Cast hodnotenia"
RESULT_POINTS = "Body"
RESULT_NOTE = "Poznamka"
RESULT_MISTAKES = "Najdene chyby"
RESULT_NO_MISTAKES = "Ziadne chyby"
RESULT_TOTAL = "Celkove hodnotenie"
RESULT_FEEDBACK = "Spatna vazba"
RESULT_RECOGNIZED = "Rozpoznane udaje"
RESULT_VERIFICATION = "Kontrolne prepocty"

# --- Chyby ---
ERROR_NO_API_KEY = (
    "Chyba: API kluc nie je nastaveny. "
    "Nastavte GEMINI_API_KEY v .env alebo zadajte v bocnom paneli."
)
ERROR_RATE_LIMIT_EXHAUSTED = "Chyba: API limit bol vycerpany. Skuste to neskor."
ERROR_UPLOAD_FAILED = "Chyba: Nepodarilo sa nahrat PDF subor."
ERROR_GRADING_FAILED = "Chyba: Hodnotenie zlyhalo. {detail}"

# --- CLI ---
CLI_DESCRIPTION = "Automaticke hodnotenie matematickych skusok cez prikazovy riadok"
CLI_FILE_HELP = "Cesta k PDF suboru so skuskou"
CLI_RUBRIC_HELP = "Cesta k textovemu suboru s hodnotiacimi kriteriami"
CLI_API_KEY_HELP = "Google Gemini API kluc (alternativa k .env)"

# --- Tlacidla ---
BUTTON_GRADE = "Spustit hodnotenie"

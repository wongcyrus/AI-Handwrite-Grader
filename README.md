# AI-Handwriting-Grader
As an educator, grading tests and assignments is a challenging and time-consuming task. The process involves several steps, such as collecting all completed scripts, reviewing the standard answers and marking for each question, assigning marks, and repeating the process for each student. Once all questions have been marked, the total score for each student must be calculated and entered into a spreadsheet. Finally, the scored scripts are returned to the students.

The current process is quite tedious and involves several unnecessary steps, such as flipping through papers, calculating total marks, and manually entering them into a spreadsheet. Reviewing standard answers and grading each question individually is also quite inefficient, as educators often have to repeat the process until they can memorize the marking scheme. Furthermore, this approach can sometimes result in unfair grading, as educators may not review all student answers for each question at the same time. To address this issue, some educators opt to score each question individually, but this requires flipping through the script multiple times, adding to the workload.

The process is not only physically exhausting but can also result in long-term back and neck pain for educators. Moreover, this process does not necessarily contribute to student learning. The issue at hand could be resolved with the application of machine learning and AI methods. Firstly, automating the process as much as possible would eliminate the need for manual paper flipping. Secondly, utilizing AI processing and analysis would facilitate a more efficient review of students' answers, potentially reducing the workload for educators. Lastly, it would ensure that answers are scored objectively by concealing personal identity.

This version is not reliant on cloud services and can be utilized by all educators through the free GitHub CodeSpaces platform.


## Template File
1. sample/VTC Test Name List.xlsx - example name list with ID/NAME/CLASS columns; copy and customize this file in `data/` to match your students.
2. smtp-template.config - rename and populate this file with your SMTP server/credentials to enable the email step.

## Required data files
- `data/<prefix>.pdf` – the scanned exam or assignment PDF (prefix matches the exam name and drives all downstream file paths, e.g., `VTC Test.pdf`).
- `data/<prefix> Name List.xlsx` – the roster used by `step1` (copy/paste from the sample and keep columns `ID`, `NAME`, `CLASS`).
- `data/<prefix> Marking Scheme.docx` – the Word document containing the standard answers that `step2` ingests.
- `data/<prefix> Answer Sheet.docx` – the template filled in by `step1` (generated automatically when you run the notebook).

Make sure the prefix is consistent across all these filenames because every notebook calls `setup_paths(prefix, data_folder)` to resolve the inputs and the results will live in `marking_form/<prefix>/…`.

## High level steps
1. Fork the repository and launch a GitHub CodeSpace (or local environment) so you can install the requirements and render the notebooks.
2. Upload your scanned exam PDF plus a name list (e.g., copy and fill `sample/VTC Test Name List.xlsx`) and marking scheme Word file into the `data/` folder.
3. Run `step1_generate_answer_sheet.ipynb` to merge the name list with the Word template, export per-student DOCX/PDF files, and compile a combined answer sheet ready for printing.
4. Run `step2_generate_marking_scheme_excel.ipynb` to parse the Word marking scheme via Gemini and save a structured Excel workbook (Marking Scheme + Summary).
5. Run `step3_question_annotations.ipynb` to convert the PDF into images, auto-detect bounding boxes, and adjust each answer region before saving `annotations.json` under `marking_form/`.
6. Run `step4_scoring_preprocessing.ipynb` to load annotations, standard answers, and templates; OCR each cropped response with Gemini, grade answers with the scoring prompt, and build the per-question web review interface.
7. Preview the generated scoring website locally, revisit any questions, and submit final marks back into the `mark.json` files exposed by the website.
8. Run `step5_post_scoring_checks.ipynb` to confirm every question has a mark, verify IDs against the name list, and clean temporary version files.
9. Run `step6_scoring_postprocessing.ipynb` to zip the website, calculate the final mark sheet, annotate PDF scripts, sample strong/weak work, and save `details_score_report.xlsx` plus supporting exports.
10. Run `step7_email_score.ipynb` to load `details_score_report.xlsx`, attach each student’s scored PDF from `marking_form/<exam>/marked/pdfs/`, and send personalized emails via SMTP.

## Notebook pipeline details

### Shared utilities (`grading_utils.py`)
- `setup_paths(prefix, data_dir, base_dir="..")` builds the centralized path dictionary used by every notebook: it resolves the source PDF, name list, marking scheme, and every output folder under `marking_form/<exam>`, including images, annotations, questions, JavaScript, marked variants, and `cache/`.
- `create_directories(paths)` creates those directories in advance so notebooks can write image exports, HTML, and JSON files without manual `mkdir` calls.
- `init_gemini_client(env_path="../.env")` reads `GOOGLE_GENAI_API_KEY` from `.env`, fails fast if the key is missing, and returns a Vertex AI Express Mode client shared across the pipeline.
- `create_gemini_config()` standardizes the safety settings plus default temperature/top-p so each OCR and grading request behaves consistently.
- `load_annotations(annotations_path)` flattens the saved bounding boxes, rekeys them by label, and returns the ordered `questions` list (`NAME`, `ID`, `CLASS`, then every question) for Steps 4–6.
- `build_student_id_mapping(base_path_questions, base_path_annotations)` reads the `ID/mark.json` entry to map pages back to student IDs and exposes `getStudentId(page)` for downstream lookups.
- `markdown_to_html()` converts the Gemini performance feedback into HTML snippets that `step7` embeds in every email body.
- `get_cache_key`, `get_from_cache`, and `save_to_cache` hash prompt parameters and store JSON in `cache/` so OCR, grading, and performance calls only hit Gemini when input truly changes.

### Step 1: Generate Answer Sheets (`step1_generate_answer_sheet.ipynb`)
- Loads the Name List Excel (use `sample/VTC Test Name List.xlsx` as the example), validates every student ID is unique, replaces the `Name:`, `Student ID:`, and `Class:` placeholders inside the DOCX template, and saves each student’s custom DOCX file.
- Converts each DOCX to PDF via headless LibreOffice, merges all PDFs into `../data/<prefix> Answer Sheets Combined.pdf`, and removes the intermediate per-student files.

### Step 2: Extract the Marking Scheme (`step2_generate_marking_scheme_excel.ipynb`)
- Converts the Word marking scheme into markdown using `mammoth` and `html2text`, then feeds the markdown to Vertex AI Gemini with a structured schema (`MarkingSchemeResponse`) so every question yields `question_number`, `question_text`, `marking_scheme`, and `marks`, plus a shared `general_grading_guide`.
- Validates that every `marking_scheme` is non-empty (raising a friendly error if any are missing), appends the general guide to each question’s rubric, and writes the clean data to an Excel workbook with `Marking Scheme` and `Summary` sheets.

### Step 3: Define Answer Bounding Boxes (`step3_question_annotations.ipynb`)
- Converts the exam PDF into JPEG pages with `pdf2image`, stores the result under `marking_form/<exam>/images/`, and lets you configure `number_of_pages` for quick tests.
- Starts Vertex AI Express Mode (via `init_gemini_client`) to auto-detect bounding boxes, but also lets you manually adjust the regions; the cleaned `annotations.json` becomes the authoritative source for every question label.

### Step 4: Scoring Preprocessing (`step4_scoring_preprocessing.ipynb`)
- Loads annotations, `Name List`, and the structured marking scheme into `standard_answer_df`, derives dictionaries for question text and marks, and copies the UI assets from `templates/javascript/` plus `favicon.ico`.
- Renders `index.html` and every `questions/<question>/index.html` + `question.js` via Jinja2 (with a Markdown filter) so graders can view extracted answers, similarity scores, reasoning, and marks.
- Defines `ocr_image_from_file()` (cropping + sharpening) and the `grade_answer()`/`grade_answers()` helpers that call Gemini with consistent configs, cache the replies, and return structured `GradingResult` objects containing `similarity_score`, `mark`, and `reasoning`.
- Iterates through every question, runs OCR and grading on the captured images, writes `data.csv` for each question, and renders the JavaScript-powered UI so you can approve or override the auto-scores before submitting them to the web interface.

### Step 5: Post-Scoring Checks (`step5_post_scoring_checks.ipynb`)
- Walks every question subdirectory to ensure `mark.json` exists and no entries leave both `mark` and `overridedMark` blank, warning if tokens still need grading.
- Cross-checks the marked IDs against the uploaded name list (reporting IDs that are missing in either direction).
- Removes temporary `control-*.json` and `mark-*.json` files generated by the website so the final data stays clean.

-### Step 6: Post-Scoring Packaging (`step6_scoring_postprocessing.ipynb`)
 - Reapplies the version-file cleanup, zips the generated website, and copies the raw scanned images into `marked/images/` to annotate them without touching the originals.
 - Reads every question’s `mark.json`, uses `build_student_id_mapping()` plus the annotation ordering to derive `marksDf` (ID, NAME, CLASS, per-question marks, total `Marks`) that prefers the name list values for student names.
 - Overlays each annotation label with its final mark via OpenCV, stitches each student’s pages into `marked/pdfs/<ID>.pdf`, merges everything into `marked/scripts/all.pdf`, and builds curated sample PDFs (good/average/weak) by inserting the real scripts between template pages from `templates/pdf/`.
 - Pivots the collected answers and reasoning data into wide sheets and saves them along with `marksDf` into `details_score_report.xlsx` plus a lightweight `score_report.xlsx`, then calls Gemini (with caching) to write a `Performance` narrative per student.
 - Archives the scripted folder as `scripts.zip` for sharing.
 - Outputs explained:
	 * `marking_form/<prefix>/images/` – annotated copies of every page used for creating the marked scripts.
	 * `marking_form/<prefix>/questions/` – each question folder now contains the latest `mark.json`, `data.csv`, and generated HTML/JS controls so you can re-open the web UI or inspect individual grading data.
	 * `marking_form/<prefix>/details_score_report.xlsx` – multi-sheet workbook (Marks, Answers, Reasoning, AnswersRaw, ReasoningRaw) that feeds `step7` and can be shared with stakeholders.
	 * `marking_form/<prefix>/score_report.xlsx` – concise marks-only sheet with ID, NAME, CLASS, and total `Marks`.
	 * `marking_form/<prefix>/marked/pdfs/<ID>.pdf` – per-student scored scripts; `marked/scripts/all.pdf` combines them, and `scripts.zip` bundles the folder for distribution.
	 * `marking_form/<prefix>.zip` – zipped copy of the scored website for archival or sharing.
	 * `cache/` – stores OCR/grading/performance responses keyed by prompt parameters so rerunning notebooks reuses previous Gemini calls instead of re-calling the API.
	 - How the files are produced:
		 1. `marking_form/<prefix>/images/` and `annotations/` are populated in `step3_question_annotations.ipynb` by converting the scanned PDF to JPEGs and writing `annotations.json` after you adjust bounding boxes.
		 2. Each `questions/<Question>` directory is created in `step4_scoring_preprocessing.ipynb`: OCRed answers are written to `data.csv`, Gemini scores to `mark.json`, and the Jinja2 templates output the HTML/JS that powers the review UI.
		 3. `details_score_report.xlsx` plus `score_report.xlsx` and the `Performance` sheet are generated in `step6_scoring_postprocessing.ipynb` after collecting all marks/answers/reasoning, casting wide pivots, and calling Gemini for narrative summaries.
		 4. The marked images, per-student PDFs, combined `scripts/all.pdf`, curated `sampleOf*.pdf`, and website zip originate from the later cells of `step6`, which copy images, draw annotations via OpenCV, save PDFs with Pillow, merge them with PyPDF4, and zip both the website and `marked_scripts` directory.
		 5. `cache/` files are created whenever `get_cache_key()` is used in steps 4 and 6 for OCR, grading, and performance prompts; the utilities in `grading_utils.py` stash the Vertex AI responses so the same prompt reuses previous answers.
	- Explain each resulting file/folder (images/, annotations/, questions/, marked/, score reports, Performance sheet, scripts.zip, website zip, cache entries)

### Step 7: Email Scores (`step7_email_score.ipynb`)
- Loads SMTP credentials from `smtp.config` (copy `smtp-template.config` and fill in secrets beforehand), reads `details_score_report.xlsx` (the `Marks` sheet plus the optional `Performance` sheet), and maps IDs to scored PDFs under `marked/pdfs/`.
- Converts the markdown `PerformanceReport` into HTML via `markdown_to_html()`, formats the email body with `body_template`, attaches each student’s `<ID>.pdf`, and delivers the message through TLS-authenticated SMTP while showing a progress bar.

## Generated outputs (per prefix)
- `marking_form/<prefix>/images/` – JPEG exports of every scanned page used for OCR and markup.
- `marking_form/<prefix>/annotations/annotations.json` – bounding box metadata used by the web UI (also creates `annotations_list`, `annotations_dict`, and `questions` for scoring).
- `marking_form/<prefix>/questions/<Question>/mark.json` – saved marks/overrides for each question plus `data.csv` for answers, similarity scores, and reasoning.
- `marking_form/<prefix>/marked/` – contains `images/` (annotated copies), `pdfs/<ID>.pdf` (per-student scored scripts), and `scripts/all.pdf` (combined bundle of all students) plus curated samples (e.g., `sampleOf3.pdf`).
- `marking_form/<prefix>/details_score_report.xlsx` and `score_report.xlsx` – Excel exports that include marks, answers, reasoning, and the Gemini-generated performance narratives (used by `step7`).
- `marking_form/<prefix>.zip` and `scripts.zip` – zipped copies of the grading website and the scored scripts folder for handoff.
- `cache/` – stores JSON responses keyed by `get_cache_key()` for OCR, grading, and performance prompts so reruns avoid re-querying Vertex AI.

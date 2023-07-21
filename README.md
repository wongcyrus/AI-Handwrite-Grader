# AI-Handwrite-Grader
This project designed to help teachers grade their students' handwriting assignments using AI. The notebook provides a template file for the teacher to fill in their class name list and standard answers, and then uses computer vision to analyze the students' scanned assignments and generate a website for the teacher to input scores. The notebook also includes post-processing steps to generate score reports and annotated scripts, as well as an option to email the scores back to the students. This tool can save teachers time and provide more accurate and consistent grading.

## Template File
1. NamelistAndAnswerTemplate.xlsx - the template of your class name list and standard answers.
2. smtp-template.config - Rename it to smtp-template.config and provide the GMAIL SMTP Server information

## High level steps
1. Begin by forking this repository.
2. Create a CodeSpaces to work in.
3. Upload your scanned assignment or test scripts to the "data/" folder.
4. Fill in the name list and standard answer and upload to the same "data/" folder.
5. Run "question_annotations.ipynb" and highlight the position of each question.
6. Run "scoring_preprocessing.ipynb" to validate the ID and question, then generate the scoring website.
7. Start the web server and provide the score for each question.
8. Run "scoring_preprocessing.ipynb" to post-validate any missing questions.
9. Run "scoring_postprocessing.ipynb" to generate score reports and annotated scripts.
10. Finally, run "email_score.ipynb" to send the script back to the students.


# AI-Handwriting-Grader
As an educator, grading tests and assignments is a challenging and time-consuming task. The process involves several steps, such as collecting all completed scripts, reviewing the standard answers and marking for each question, assigning marks, and repeating the process for each student. Once all questions have been marked, the total score for each student must be calculated and entered into a spreadsheet. Finally, the scored scripts are returned to the students.

The current process is quite tedious and involves several unnecessary steps, such as flipping through papers, calculating total marks, and manually entering them into a spreadsheet. Reviewing standard answers and grading each question individually is also quite inefficient, as educators often have to repeat the process until they can memorize the marking scheme. Furthermore, this approach can sometimes result in unfair grading, as educators may not review all student answers for each question at the same time. To address this issue, some educators opt to score each question individually, but this requires flipping through the script multiple times, adding to the workload.

The process is not only physically exhausting but can also result in long-term back and neck pain for educators. Moreover, this process does not necessarily contribute to student learning. The issue at hand could be resolved with the application of machine learning and AI methods. Firstly, automating the process as much as possible would eliminate the need for manual paper flipping. Secondly, utilizing AI processing and analysis would facilitate a more efficient review of students' answers, potentially reducing the workload for educators. Lastly, it would ensure that answers are scored objectively by concealing personal identity.

This version is not reliant on cloud services and can be utilized by all educators through the free GitHub CodeSpaces platform.

## Microsoft Tech Blog - The Power of AI in Grading Handwriting Assignments
https://techcommunity.microsoft.com/t5/educator-developer-blog/the-power-of-ai-in-grading-handwriting-assignments/ba-p/3881976 

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


## Demo and Explanation (Cantonese)
[![Watch the video](https://img.youtube.com/vi/yhNc9sm9ks0/0.jpg)](https://youtu.be/yhNc9sm9ks0)



## Maintance requirement file
Update requirements-dev.txt
```
pip list --format=json | jq -r ".[].name" > requirements-dev.txt
```
Revert to Pillow==9.5.0 if you hits error.


## Using Vertex AI Gemini Pro

### GCP application Login 
```
gcloud auth application-default login
gcloud config set project XXXXX
gcloud auth application-default set-quota-project XXXXX
```

### Enable Google Cloud API
```
gcloud services enable speech.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

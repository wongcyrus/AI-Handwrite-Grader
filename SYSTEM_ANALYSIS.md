# AI Handwriting Grader - System Analysis

**Analysis Date**: 2025-12-25  
**Branch**: user-friendly-mode  
**Purpose**: Pre-refactoring analysis for implementing user-friendly mode

## Overall Architecture
The system is a multi-stage pipeline for automated grading of handwritten student assignments using AI/ML techniques. It consists of Jupyter notebooks for processing and a Flask web server for manual scoring interface.

## Core Workflow (10 Steps from README)

### 1. Data Input Stage
- **Input**: Scanned PDF assignments uploaded to `/data/` folder
- **Template**: `NamelistAndAnswerTemplate.xlsx` with two sheets:
  - `NameList`: Student roster 
  - `Answer`: Standard answers with questions, correct answers, and marks
- **SMTP Config**: Email configuration for sending results back

### 2. Question Annotation (`question_annotations.ipynb`)
- **Purpose**: Convert PDF to images and define question boundaries
- **Process**:
  - Install system dependencies (poppler-utils)
  - Convert PDF pages to images using pdf2image
  - Create interactive annotation interface to mark question areas
  - Generate `annotations.json` with coordinates for each question
  - Store annotations with labels (NAME, ID, CLASS, Q1, Q2, etc.)

### 3. Scoring Preprocessing (`scoring_preprocessing.ipynb`)
- **Purpose**: Validate data and generate web-based scoring interface
- **Key Logic**:
  - Load annotations and flatten to list format
  - Extract question labels, excluding metadata (NAME, ID, CLASS)
  - Validate standard answers against detected questions
  - Create directory structure: `/marking_form/{filename}/`
    - `/images/` - PDF page images
    - `/annotations/` - Question boundary data
    - `/questions/` - Individual question scoring data
    - `/javascript/` - Web interface assets
  - Generate HTML templates for each question using Jinja2
  - Create main index page linking to all questions

### 4. Web Server (`server.py`)
- **Purpose**: Serve scoring interface and collect manual grades
- **Flask Routes**:
  - `GET /` - Main scoring dashboard
  - `GET /<path>` - Static files (images, CSS, JS)
  - `POST /questions/{question}/index.html` - Save scoring data
- **Data Storage**: JSON files for marks and control data with timestamps
- **Caching**: Image caching with 3-hour expiry for performance

### 5. Manual Scoring Interface
- **Web Interface Features**:
  - DataTables for sortable question list
  - Image display of student answers
  - Similarity-based auto-scoring with manual override
  - Configurable parameters:
    - Full marks per question
    - Minimum similarity threshold
    - Grading granularity (step size)
  - Real-time mark calculation and validation

### 6. Post-processing (`scoring_postprocessing.ipynb`)
- **Purpose**: Generate final reports and annotated scripts
- **Functions**:
  - Backup all grading results with timestamps
  - Calculate total scores per student
  - Generate Excel score reports
  - Create individual annotated PDF scripts
  - Collect sample answers for future reference
  - Prepare files for email distribution

### 7. Email Distribution (`email_score.ipynb`)
- **Purpose**: Send graded scripts back to students
- **Process**:
  - Load SMTP configuration
  - Match student emails from name list
  - Attach individual scored PDFs
  - Send personalized emails with results

## Data Flow Architecture

```
PDF Input → Image Conversion → Question Annotation → 
Web Interface Generation → Manual Scoring → 
Result Processing → Email Distribution
```

## Key Technical Components

### AI/ML Integration Points:
- **OCR**: EasyOCR for text extraction
- **Similarity Matching**: Sentence transformers for answer comparison
- **Image Processing**: OpenCV for image manipulation
- **Gemini Integration**: Google's Gemini AI for advanced text analysis

### File Structure:
```
/data/
  ├── {assignment}.pdf
  └── {assignment}.xlsx
/marking_form/{assignment}/
  ├── images/
  ├── annotations/
  ├── questions/{question}/
  │   ├── mark.json
  │   └── control.json
  └── marked/
      ├── images/
      ├── pdf/
      └── scripts/
```

### Configuration Management:
- Environment variables for file paths
- JSON-based annotation storage
- Excel-based answer templates
- SMTP configuration files

## Current Pain Points for "User Friendly Mode":
1. **Complex Setup**: Multiple notebook execution steps
2. **Technical Barriers**: Requires Jupyter/Python knowledge  
3. **Manual Coordination**: No unified interface
4. **Error Handling**: Limited validation and recovery
5. **Progress Tracking**: No visual progress indicators
6. **File Management**: Manual file organization

## Refactoring Goals for User-Friendly Mode:
- Create unified web interface replacing notebook workflow
- Add step-by-step wizard with progress tracking
- Implement automatic error handling and validation
- Simplify file upload and management
- Provide real-time feedback and guidance
- Abstract technical complexity from end users

## Next Steps:
1. Design simplified workflow interface
2. Create modular Python functions from notebook code
3. Build progressive web application
4. Add comprehensive error handling
5. Implement user guidance system

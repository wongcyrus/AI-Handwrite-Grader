# Deprecated Files

This folder contains legacy code and files from the original notebook-based implementation of the AI Handwriting Grader. These files are kept for reference only and are not part of the current Connected Agents architecture.

## Contents

### Notebooks (Original Implementation)
- `question_annotations.ipynb` - Manual question boundary annotation
- `question_annotations_gemini.ipynb` - Gemini-based annotation
- `question_annotations_nova.ipynb` - Nova model annotation
- `scoring_preprocessing.ipynb` - Score preprocessing workflow
- `scoring_preprocessing_gemini.ipynb` - Gemini preprocessing
- `scoring_preprocessing_gemini_extraction.ipynb` - Gemini text extraction
- `scoring_postporcessing.ipynb` - Post-processing and report generation
- `email_score.ipynb` - Email distribution of results

### Legacy Server
- `server.py` - Original Flask server implementation

### Templates
- `NamelistAndAnswerTemplate.xlsx` - Original Excel template
- `smtp-template.config` - SMTP configuration template

### Requirements
- `requirements.txt` - Original package requirements
- `requirements-dev.txt` - Development requirements

## Migration Notes

The current implementation uses:
- **Connected Agents Architecture** instead of notebooks
- **Microservices** instead of monolithic server
- **Azure AI Foundry** instead of direct model APIs
- **Web Interface** instead of Jupyter notebooks

## Usage

These files are **deprecated** and should not be used in production. They are maintained for:
- Historical reference
- Understanding the evolution of the system
- Potential feature extraction for future enhancements

For current implementation, see:
- `/app/` - Current Flask application
- `CONNECTED_AGENTS.md` - Architecture documentation
- `USER_GUIDE.md` - Usage instructions

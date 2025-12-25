# AI Handwriting Grader - User Guide

## Overview
The AI Handwriting Grader uses Azure AI Foundry Connected Agents to automate the grading of handwritten assignments and tests. Different user roles have access to different features and workflows.

## User Roles

### 1. System Administrator
**Responsibilities**: Initial setup, agent deployment, system maintenance

#### Setup Tasks
```bash
# 1. Deploy Connected Agents (one-time setup)
python deploy_agents.py

# 2. Configure environment variables
cp .env.template .env
# Edit .env with your Azure credentials and agent IDs

# 3. Start the application
python app.py
```

#### Configuration Management
- Manage Azure AI Foundry project settings
- Monitor agent performance and costs
- Update agent instructions and configurations
- Handle system-wide troubleshooting

---

### 2. Educator/Teacher
**Responsibilities**: Create projects, upload materials, review AI grading results

#### Creating a New Grading Project
1. **Login** to the web interface
2. **Create Project**: Click "New Project" and provide:
   - Project name and description
   - Subject and grade level
   - Grading rubric details

3. **Upload Materials**:
   - **PDF Files**: Scanned student assignments/tests
   - **Excel Template**: Standard answers and student roster
   - **Rubric**: Scoring criteria and point allocations

#### Grading Workflow
1. **Start Annotation**: Define question boundaries on sample pages
2. **AI Processing**: Connected agents analyze handwriting and content
3. **Review Results**: Check AI-generated scores and feedback
4. **Manual Adjustments**: Override scores where needed
5. **Generate Reports**: Export grades and feedback

#### Best Practices
- Ensure clear, high-quality scans (300+ DPI)
- Use consistent question numbering
- Review low-confidence scores manually
- Provide detailed rubrics for better AI accuracy

---

### 3. Teaching Assistant/Grader
**Responsibilities**: Manual scoring, quality assurance, student feedback

#### Manual Scoring Interface
1. **Access Assigned Projects**: View projects requiring manual review
2. **Score Questions**: 
   - Review AI suggestions and confidence scores
   - Provide manual scores for unclear answers
   - Add detailed feedback comments

3. **Quality Assurance**:
   - Verify AI-detected handwriting accuracy
   - Check scoring consistency across students
   - Flag unusual patterns or potential issues

#### Batch Processing
- Process multiple students simultaneously
- Apply consistent scoring standards
- Use keyboard shortcuts for efficiency

---

### 4. Student
**Responsibilities**: View results, understand feedback

#### Accessing Results
1. **Login** with provided credentials
2. **View Grades**: See scores for completed assignments
3. **Review Feedback**: Read detailed comments and suggestions
4. **Download Reports**: Get annotated copies of assignments

#### Understanding AI Feedback
- **Confidence Scores**: Higher scores indicate more reliable AI analysis
- **Highlighted Areas**: Sections that were difficult to read or analyze
- **Improvement Suggestions**: Specific recommendations for better performance

---

## Workflow Examples

### Complete Grading Workflow (Educator) - Async Processing
```
1. Create Project → 2. Upload Files → 3. Start Annotation Job (Returns immediately)
     ↓
4. Poll Job Status → 5. Monitor Progress → 6. Review AI Results (When complete)
     ↓
7. Manual Adjustments → 8. Generate Reports → 9. Distribute to Students
```

### Avoiding Web Request Timeouts
- **Immediate Response**: Job submission returns job ID instantly
- **Background Processing**: AI analysis runs asynchronously  
- **Progress Polling**: Frontend polls status every 5 seconds
- **No Timeouts**: Web requests complete in <1 second

### Quality Assurance Workflow (TA)
```
1. Receive Assignment → 2. Review AI Scores → 3. Check Low-Confidence Items
     ↓
4. Manual Scoring → 5. Add Feedback → 6. Submit for Approval
```

### Student Review Workflow
```
1. Receive Notification → 2. Login to Portal → 3. View Grades & Feedback
     ↓
4. Download Annotated Assignment → 5. Plan Improvements
```

## Connected Agents Interaction

### For Educators
- **Handwriting Analyzer**: Automatically extracts text from scanned assignments
- **Content Evaluator**: Compares student answers against your rubric
- **Scoring Coordinator**: Provides consistent, fair grade calculations
- **Main Orchestrator**: Coordinates the entire grading workflow

### Processing Times for All AI Operations
All AI-powered operations now use asynchronous processing to avoid web request timeouts:

#### Full Annotation Job (~20 minutes)
- **Initialization**: 1 minute - Setting up Connected Agents
- **OCR Processing**: 4 minutes - Handwriting analysis and text extraction  
- **Content Evaluation**: 10 minutes - AI analysis of student answers
- **Final Scoring**: 5 minutes - Score coordination and report generation

#### Individual Handwriting Analysis (~5 minutes)
- **Processing**: 2 minutes - Analyzing handwriting patterns
- **Extraction**: 3 minutes - Converting to text with confidence scores

#### Answer Evaluation (~8 minutes)
- **Content Analysis**: 5 minutes - Comparing against standard answers
- **Scoring**: 3 minutes - Calculating final grades and feedback

### Async Processing Benefits
- **No Timeouts**: All web requests complete in <1 second
- **Real-time Progress**: Live updates every 5 seconds
- **Background Processing**: AI work happens without blocking the interface
- **Scalable**: Multiple jobs can run simultaneously

### Progress Tracking
- Real-time progress updates with current processing step
- Estimated completion time based on current progress
- Detailed status information for each Connected Agent
- Check job status and progress
- Review confidence scores and accuracy
- Identify questions requiring manual review
- Monitor processing times and costs

## Troubleshooting by Role

### System Administrator
- **Agent Failures**: Check Azure credentials and quotas
- **Performance Issues**: Monitor resource usage and scaling
- **Integration Problems**: Verify API connections and permissions

### Educator
- **Poor OCR Results**: Improve scan quality, adjust lighting
- **Incorrect Scoring**: Refine rubrics, provide more examples
- **Missing Questions**: Verify annotation boundaries

### Teaching Assistant
- **Inconsistent Scores**: Check rubric interpretation, flag for review
- **Student Disputes**: Document scoring rationale, escalate if needed

### Student
- **Cannot Access Results**: Contact instructor or IT support
- **Unclear Feedback**: Request clarification from instructor

## Best Practices by Role

### System Administrator
- Regular backup of agent configurations
- Monitor Azure costs and usage patterns
- Keep documentation updated
- Plan for peak grading periods

### Educator
- Start with small pilot projects
- Provide clear, detailed rubrics
- Review AI suggestions before finalizing
- Maintain consistent grading standards

### Teaching Assistant
- Focus on low-confidence scores first
- Document unusual cases for future reference
- Communicate with educators about patterns
- Use batch processing for efficiency

### Student
- Review feedback carefully for learning opportunities
- Contact instructors for clarification when needed
- Keep digital copies of graded work
- Use feedback to improve future performance

## Support and Resources

- **Technical Issues**: Contact system administrator
- **Grading Questions**: Consult with lead educator
- **Training Materials**: Available in the help section
- **Best Practices Guide**: Updated based on user feedback

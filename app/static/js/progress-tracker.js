/**
 * Progress tracking for AI processing jobs
 * Shows realistic processing stages and estimated completion times
 */

class JobProgressTracker {
    constructor(jobId, statusEndpoint) {
        this.jobId = jobId;
        this.statusEndpoint = statusEndpoint;
        this.pollInterval = 5000; // 5 seconds
        this.maxRetries = 3;
        this.retryCount = 0;
    }

    startTracking() {
        this.updateProgress();
        this.intervalId = setInterval(() => this.updateProgress(), this.pollInterval);
    }

    stopTracking() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    }

    async updateProgress() {
        try {
            const response = await fetch(`${this.statusEndpoint}/${this.jobId}`);
            const status = await response.json();
            
            this.renderProgress(status);
            
            if (status.status === 'completed' || status.status === 'error') {
                this.stopTracking();
                this.onComplete(status);
            }
            
            this.retryCount = 0; // Reset on success
            
        } catch (error) {
            console.error('Error fetching job status:', error);
            this.retryCount++;
            
            if (this.retryCount >= this.maxRetries) {
                this.stopTracking();
                this.onError('Failed to fetch job status after multiple retries');
            }
        }
    }

    renderProgress(status) {
        const progressContainer = document.getElementById('progress-container');
        if (!progressContainer) return;

        const stageIcons = {
            'initializing': '⚙️',
            'processing_ocr': '👁️',
            'processing_content': '🧠',
            'finalizing_scores': '📊',
            'completed': '✅',
            'error': '❌'
        };

        progressContainer.innerHTML = `
            <div class="progress-header">
                <h3>${stageIcons[status.status] || '⏳'} ${status.current_step || 'Processing...'}</h3>
                <span class="progress-percentage">${status.progress || 0}%</span>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${status.progress || 0}%"></div>
            </div>
            
            <div class="progress-details">
                <div class="time-info">
                    <span>Elapsed: ${this.formatTime(status.elapsed_seconds || 0)}</span>
                    <span>${status.estimated_completion || 'Calculating...'}</span>
                </div>
                
                <div class="stage-indicators">
                    ${this.renderStageIndicators(status.status)}
                </div>
            </div>
        `;
    }

    renderStageIndicators(currentStatus) {
        const stages = [
            { key: 'initializing', label: 'Setup', duration: '1 min' },
            { key: 'processing_ocr', label: 'OCR', duration: '4 min' },
            { key: 'processing_content', label: 'AI Analysis', duration: '10 min' },
            { key: 'finalizing_scores', label: 'Scoring', duration: '5 min' }
        ];

        return stages.map(stage => {
            const isActive = stage.key === currentStatus;
            const isCompleted = this.isStageCompleted(stage.key, currentStatus);
            const statusClass = isCompleted ? 'completed' : (isActive ? 'active' : 'pending');
            
            return `
                <div class="stage-indicator ${statusClass}">
                    <div class="stage-dot"></div>
                    <div class="stage-info">
                        <span class="stage-label">${stage.label}</span>
                        <span class="stage-duration">${stage.duration}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    isStageCompleted(stage, currentStatus) {
        const stageOrder = ['initializing', 'processing_ocr', 'processing_content', 'finalizing_scores', 'completed'];
        const stageIndex = stageOrder.indexOf(stage);
        const currentIndex = stageOrder.indexOf(currentStatus);
        return currentIndex > stageIndex;
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    onComplete(status) {
        console.log('Job completed:', status);
        // Override this method to handle completion
    }

    onError(message) {
        console.error('Job error:', message);
        // Override this method to handle errors
    }
}

// CSS for progress tracking (add to your stylesheet)
const progressCSS = `
.progress-container {
    max-width: 600px;
    margin: 20px auto;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: #f9f9f9;
}

.progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.progress-header h3 {
    margin: 0;
    color: #333;
}

.progress-percentage {
    font-weight: bold;
    color: #007bff;
}

.progress-bar {
    width: 100%;
    height: 20px;
    background: #e9ecef;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 15px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #007bff, #0056b3);
    transition: width 0.3s ease;
}

.progress-details {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.time-info {
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 0.9em;
    color: #666;
}

.stage-indicators {
    display: flex;
    gap: 15px;
}

.stage-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.stage-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-bottom: 5px;
}

.stage-indicator.pending .stage-dot {
    background: #ccc;
}

.stage-indicator.active .stage-dot {
    background: #007bff;
    animation: pulse 1.5s infinite;
}

.stage-indicator.completed .stage-dot {
    background: #28a745;
}

.stage-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.stage-label {
    font-size: 0.8em;
    font-weight: bold;
}

.stage-duration {
    font-size: 0.7em;
    color: #666;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}
`;

// Usage example for async job processing
const jobTracker = new JobProgressTracker(null, '/api/jobs');

// Start a job asynchronously
async function startGradingJob(projectId, pdfUrl, excelUrl) {
    try {
        const response = await fetch('/api/jobs/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project_id: projectId,
                pdf_url: pdfUrl,
                excel_url: excelUrl
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Start tracking the job progress
            jobTracker.jobId = result.job_id;
            jobTracker.startTracking();
            
            // Show progress container
            document.getElementById('progress-container').style.display = 'block';
            
            return result.job_id;
        } else {
            throw new Error(result.error || 'Failed to start job');
        }
    } catch (error) {
        console.error('Error starting job:', error);
        alert('Failed to start grading job: ' + error.message);
    }
}

// Override completion handler
jobTracker.onComplete = function(status) {
    if (status.status === 'completed') {
        alert('Grading completed successfully!');
        // Redirect to results page or refresh data
        window.location.reload();
    } else if (status.status === 'error') {
        alert('Grading failed: ' + (status.message || 'Unknown error'));
    }
};

// Override error handler
jobTracker.onError = function(message) {
    alert('Job tracking error: ' + message);
    document.getElementById('progress-container').style.display = 'none';
};

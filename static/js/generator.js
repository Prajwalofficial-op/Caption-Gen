// Video Caption Generator JavaScript

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const uploadArea = document.getElementById('upload-area');
    const videoFileInput = document.getElementById('video-file');
    const videoPreview = document.getElementById('video-preview');
    const videoPreviewContainer = document.getElementById('video-preview-container');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const fileDuration = document.getElementById('file-duration');
    const processingStatus = document.getElementById('processing-status');
    const processingMessage = document.getElementById('processing-message');
    const captionForm = document.getElementById('caption-form');
    const resultsSection = document.getElementById('results-section');
    const analysisContent = document.getElementById('analysis-content');
    const captionOutput = document.getElementById('caption-output');
    const hashtagsList = document.getElementById('hashtags-list');
    const hashtagsContainer = document.getElementById('hashtags-container');
    const platformOptions = document.querySelectorAll('.platform-option');
    const toneOptions = document.querySelectorAll('.tone-option');
    const generateBtn = document.getElementById('generate-btn');
    const copyBtn = document.getElementById('copy-btn');
    const saveBtn = document.getElementById('save-btn');
    const newBtn = document.getElementById('new-btn');
    const loadingDiv = document.getElementById('loading');
    const errorMessage = document.getElementById('error-message');
    
    // State variables
    let currentVideoId = null;
    let currentPlatform = 'instagram';
    let currentTone = 'friendly';
    let currentCaption = '';
    let currentHashtags = [];
    let processingInterval = null;
    let pollCount = 0;
    const maxPollCount = 60; // 2 minutes max
    
    // Upload area click handler
    uploadArea.addEventListener('click', () => {
        videoFileInput.click();
    });
    
    // Drag and drop
    ['dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            if (eventName === 'dragover') {
                uploadArea.style.borderColor = '#6366f1';
                uploadArea.style.backgroundColor = 'rgba(99, 102, 241, 0.1)';
            } else if (eventName === 'dragleave') {
                uploadArea.style.borderColor = '#cbd5e1';
                uploadArea.style.backgroundColor = '';
            } else if (eventName === 'drop') {
                uploadArea.style.borderColor = '#cbd5e1';
                uploadArea.style.backgroundColor = '';
                if (e.dataTransfer.files.length) {
                    videoFileInput.files = e.dataTransfer.files;
                    handleVideoSelect();
                }
            }
        });
    });
    
    // Video file selection
    videoFileInput.addEventListener('change', handleVideoSelect);
    
    // Platform selection
    platformOptions.forEach(option => {
        option.addEventListener('click', () => {
            platformOptions.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
            currentPlatform = option.getAttribute('data-platform');
            document.querySelector('input[name="platform"]').value = currentPlatform;
        });
    });
    
    // Tone selection
    toneOptions.forEach(option => {
        option.addEventListener('click', () => {
            toneOptions.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
            currentTone = option.getAttribute('data-tone');
            document.querySelector('input[name="tone"]').value = currentTone;
        });
    });
    
    // Generate caption
    generateBtn.addEventListener('click', generateCaption);
    
    // Copy caption
    copyBtn.addEventListener('click', copyCaption);
    
    // Save caption
    saveBtn.addEventListener('click', saveCaption);
    
    // New video
    newBtn.addEventListener('click', resetForm);
    
    // Show error
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
    
    // Functions
    function handleVideoSelect() {
        const file = videoFileInput.files[0];
        if (!file) return;
        
        // Clear previous errors
        errorMessage.style.display = 'none';
        
        // Validate file type
        const validTypes = [
            'video/mp4', 'video/quicktime', 'video/x-msvideo', 
            'video/x-matroska', 'video/webm', 'video/x-flv'
        ];
        
        if (!validTypes.includes(file.type)) {
            const ext = file.name.split('.').pop().toLowerCase();
            showError(`Unsupported file type: .${ext}. Please use MP4, MOV, AVI, MKV, WEBM, or FLV.`);
            return;
        }
        
        // Validate file size
        if (file.size > 100 * 1024 * 1024) { // 100MB
            showError('File size exceeds 100MB limit');
            return;
        }
        
        // Show preview
        const videoURL = URL.createObjectURL(file);
        videoPreview.src = videoURL;
        videoPreviewContainer.style.display = 'block';
        
        // Get video duration
        videoPreview.onloadedmetadata = () => {
            const duration = videoPreview.duration;
            
            // Validate duration
            if (duration > 60) {
                showError(`Video duration (${Math.round(duration)}s) exceeds 60 second limit`);
                resetForm();
                return;
            }
            
            if (duration < 1) {
                showError(`Video too short (${Math.round(duration)}s). Minimum 1 second required.`);
                resetForm();
                return;
            }
            
            // Show file info
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            fileDuration.textContent = `${Math.round(duration)} seconds`;
            fileInfo.style.display = 'block';
            
            // Hide upload area
            uploadArea.style.display = 'none';
            
            // Upload video
            uploadVideo(file);
        };
        
        videoPreview.onerror = () => {
            showError('Could not load video. Please try a different file.');
            resetForm();
        };
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function uploadVideo(file) {
        const formData = new FormData();
        formData.append('video_file', file);
        formData.append('platform', currentPlatform);
        formData.append('tone', currentTone);
        formData.append('keywords', document.getElementById('keywords').value);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        
        // Show processing status
        processingStatus.style.display = 'block';
        processingMessage.textContent = 'Uploading video...';
        
        fetch('/api/upload/', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Upload response:', data);
            if (data.success) {
                currentVideoId = data.video_id;
                processingMessage.textContent = data.message || 'Video uploaded. AI processing started...';
                
                // Show form options
                captionForm.style.display = 'block';
                
                // Start polling for status
                startStatusPolling();
            } else {
                processingStatus.style.display = 'none';
                showError('Upload failed: ' + (data.error || 'Unknown error'));
                resetForm();
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            processingStatus.style.display = 'none';
            showError('Upload failed. Please try again.');
            resetForm();
        });
    }
    
    function startStatusPolling() {
        if (processingInterval) {
            clearInterval(processingInterval);
        }
        
        pollCount = 0;
        
        processingInterval = setInterval(() => {
            pollCount++;
            if (pollCount > maxPollCount) {
                clearInterval(processingInterval);
                showError('Processing timeout. Please try again.');
                resetForm();
                return;
            }
            
            checkProcessingStatus();
        }, 2000); // Check every 2 seconds
        
        // Check immediately
        checkProcessingStatus();
    }
    
    function checkProcessingStatus() {
        if (!currentVideoId) return;
        
        fetch(`/api/status/${currentVideoId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Status response:', data);
                
                if (data.status === 'processing') {
                    processingMessage.textContent = 'AI is analyzing your video... ' + pollCount + 's';
                } else if (data.status === 'processed') {
                    // Processing complete
                    clearInterval(processingInterval);
                    processingStatus.style.display = 'none';
                    
                    // Show results
                    showResults(data);
                } else if (data.status === 'failed') {
                    // Processing failed
                    clearInterval(processingInterval);
                    processingStatus.style.display = 'none';
                    showError(data.error || 'Video processing failed. Please try again with a different video.');
                    resetForm();
                }
            })
            .catch(error => {
                console.error('Status check error:', error);
            });
    }
    
    function generateCaption() {
        if (!currentVideoId) {
            showError('Please upload a video first');
            return;
        }
        
        loadingDiv.style.display = 'block';
        generateBtn.disabled = true;
        
        // Reload the page to restart processing with new settings
        setTimeout(() => {
            checkProcessingStatus();
            loadingDiv.style.display = 'none';
            generateBtn.disabled = false;
        }, 1000);
    }
    
    function showResults(data) {
        console.log('Showing results:', data);
        
        // Show results section
        resultsSection.style.display = 'block';
        
        // Show analysis
        let analysisHTML = '';
        if (data.objects && data.objects.length > 0) {
            analysisHTML += `<p><strong>Objects detected:</strong> `;
            analysisHTML += data.objects.map(obj => 
                `<span class="object-tag">${obj.object} (${obj.count})</span>`
            ).join(' ');
            analysisHTML += `</p>`;
        }
        
        if (data.description) {
            analysisHTML += `<p><strong>Video description:</strong> ${data.description}</p>`;
        }
        
        if (data.duration) {
            analysisHTML += `<p><strong>Duration:</strong> ${data.duration}</p>`;
        }
        
        analysisContent.innerHTML = analysisHTML || '<p>Video analysis complete.</p>';
        
        // Show caption
        currentCaption = data.caption || 'Caption generated successfully!';
        captionOutput.innerHTML = `<p>${currentCaption.replace(/\n/g, '<br>')}</p>`;
        
        // Show hashtags
        currentHashtags = data.hashtags || [];
        if (currentHashtags.length > 0) {
            hashtagsList.innerHTML = currentHashtags.map(tag => 
                `<span class="hashtag" onclick="copyToClipboard('${tag}')">${tag}</span>`
            ).join('');
            hashtagsContainer.style.display = 'block';
        } else {
            hashtagsContainer.style.display = 'none';
        }
    }
    
    function copyCaption() {
        if (!currentCaption) {
            showError('No caption to copy');
            return;
        }
        
        // Combine caption and hashtags
        let textToCopy = currentCaption;
        if (currentHashtags.length > 0) {
            textToCopy += '\n\n' + currentHashtags.join(' ');
        }
        
        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                // Show feedback
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                copyBtn.style.backgroundColor = '#10b981';
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                    copyBtn.style.backgroundColor = '';
                }, 2000);
            })
            .catch(err => {
                console.error('Failed to copy:', err);
                showError('Failed to copy caption to clipboard.');
            });
    }
    
    function saveCaption() {
        if (!currentVideoId || !currentCaption) {
            showError('No caption to save');
            return;
        }
        
        fetch('/api/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                video_id: currentVideoId,
                caption: currentCaption
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Save response:', data);
            if (data.success) {
                // Show feedback
                const originalText = saveBtn.innerHTML;
                saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved!';
                saveBtn.style.backgroundColor = '#10b981';
                
                setTimeout(() => {
                    saveBtn.innerHTML = originalText;
                    saveBtn.style.backgroundColor = '';
                }, 2000);
            } else {
                showError('Failed to save caption: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Save error:', error);
            showError('Failed to save caption.');
        });
    }
    
    function resetForm() {
        // Reset all elements
        videoFileInput.value = '';
        if (videoPreview.src) {
            URL.revokeObjectURL(videoPreview.src);
            videoPreview.src = '';
        }
        videoPreviewContainer.style.display = 'none';
        fileInfo.style.display = 'none';
        processingStatus.style.display = 'none';
        captionForm.style.display = 'none';
        resultsSection.style.display = 'none';
        uploadArea.style.display = 'block';
        errorMessage.style.display = 'none';
        loadingDiv.style.display = 'none';
        
        // Reset state
        currentVideoId = null;
        currentCaption = '';
        currentHashtags = [];
        pollCount = 0;
        
        if (processingInterval) {
            clearInterval(processingInterval);
            processingInterval = null;
        }
        
        // Reset form fields
        document.getElementById('keywords').value = '';
        
        // Reset selections
        platformOptions.forEach(opt => opt.classList.remove('selected'));
        document.querySelector('.platform-option.instagram').classList.add('selected');
        currentPlatform = 'instagram';
        
        toneOptions.forEach(opt => opt.classList.remove('selected'));
        document.querySelector('.tone-option[data-tone="friendly"]').classList.add('selected');
        currentTone = 'friendly';
        
        // Reset buttons
        generateBtn.disabled = false;
    }
    
    // Helper function for hashtag copy
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text)
            .then(() => {
                // Show toast
                const toast = document.createElement('div');
                toast.textContent = 'Copied: ' + text;
                toast.style.position = 'fixed';
                toast.style.bottom = '20px';
                toast.style.right = '20px';
                toast.style.backgroundColor = '#10b981';
                toast.style.color = 'white';
                toast.style.padding = '10px 20px';
                toast.style.borderRadius = '8px';
                toast.style.zIndex = '1000';
                document.body.appendChild(toast);
                
                setTimeout(() => {
                    document.body.removeChild(toast);
                }, 2000);
            })
            .catch(err => console.error('Copy failed:', err));
    };
});
// API Base URL
const API_BASE = '';

// Audio recording variables
let mediaRecorder = null;
let audioChunks = [];
let recordingStartTime = null;
let recordingInterval = null;
let audioStream = null;
let audioContext = null;
let analyser = null;
let animationFrame = null;
let recordedBlob = null;

// Speech recognition variables
let recognition = null;
let finalTranscript = '';
let interimTranscript = '';

// Scenario data
const scenarios = {
    1: "안녕하세요, 서울중앙지검 김철수 검사입니다. 당신 명의의 계좌가 보이스피싱 범죄에 사용되었습니다. 지금 바로 확인하지 않으면 내일 체포영장이 발부됩니다. 주민등록번호 123456-1234567과 계좌번호 1234-567890을 말씀해주세요.",
    2: "금융감독원입니다. 고객님 계좌에서 이상거래가 감지되었습니다. 즉시 안전계좌로 자금을 이체하셔야 피해를 막을 수 있습니다. 카드번호 1234-5678-9012-3456과 OTP 번호를 알려주세요.",
    3: "안녕하세요. 택배 배송 관련하여 연락드렸습니다. 오늘 오후 2시경 방문 예정인데 댁에 계실까요?"
};

// Tab switching
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Deactivate all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Activate selected button
    event.target.classList.add('active');
}

// Load scenario
function loadScenario(num) {
    const text = scenarios[num];
    document.getElementById('text-input').value = text;

    // Switch to text tab
    switchToTextTab();
}

function switchToTextTab() {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById('text-tab').classList.add('active');
    document.querySelectorAll('.tab-btn')[0].classList.add('active');
}

// Analyze text
async function analyzeText() {
    const text = document.getElementById('text-input').value.trim();

    if (!text) {
        alert('분석할 텍스트를 입력하세요.');
        return;
    }

    // Show loading
    showLoading();

    try {
        // Use Gemini + Rule Filter API (new system)
        const response = await fetch(`${API_BASE}/api/analyze/gemini`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                enable_filter: true
            })
        });

        if (!response.ok) {
            if (response.status === 429) {
                throw new Error('요청 제한 초과: 1분당 10회까지만 가능합니다.');
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayGeminiResults(data);
    } catch (error) {
        console.error('Error:', error);
        alert('분석 중 오류가 발생했습니다: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Toggle recording
async function toggleRecording() {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        await startRecording();
    } else {
        stopRecording();
    }
}

// Start recording
async function startRecording() {
    try {
        // Request microphone access
        audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 16000
            }
        });

        // Create media recorder with explicit format
        // Try WebM Opus first (best compatibility), fallback to default
        let mimeType = 'audio/webm;codecs=opus';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = 'audio/webm';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = ''; // Use default
            }
        }

        const options = mimeType ? { mimeType } : {};
        mediaRecorder = new MediaRecorder(audioStream, options);
        audioChunks = [];

        console.log('[DEBUG] Recording with mimeType:', mimeType || 'default');

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            // Create blob from chunks with actual recorded type
            recordedBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });

            // Create playback URL
            const audioURL = URL.createObjectURL(recordedBlob);
            const audioPlayback = document.getElementById('audio-playback');
            audioPlayback.src = audioURL;

            // Show recorded audio section
            document.getElementById('recorded-audio').style.display = 'block';

            // Stop visualizer
            if (animationFrame) {
                cancelAnimationFrame(animationFrame);
            }
            document.getElementById('audio-visualizer').style.display = 'none';
        };

        // Start recording
        mediaRecorder.start();
        recordingStartTime = Date.now();

        // Update UI
        const recordBtn = document.getElementById('record-btn');
        const recordText = document.getElementById('record-text');
        recordBtn.classList.add('recording');
        recordText.textContent = '녹음 중지';

        // Show and start timer
        document.getElementById('recording-time').style.display = 'block';
        recordingInterval = setInterval(updateRecordingTime, 100);

        // Start visualizer
        startVisualizer();

        // Start speech recognition
        startSpeechRecognition();

        console.log('Recording started');

    } catch (error) {
        console.error('Error starting recording:', error);
        alert('마이크 접근 권한이 필요합니다.');
    }
}

// Start speech recognition
function startSpeechRecognition() {
    // Check browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn('Speech recognition not supported in this browser');
        return;
    }

    try {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'ko-KR';

        finalTranscript = '';
        interimTranscript = '';

        // Show live transcript section
        document.getElementById('transcript-live').style.display = 'block';

        recognition.onresult = (event) => {
            interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;

                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }

            // Update live transcript display
            const liveText = document.getElementById('live-transcript-text');
            liveText.classList.add('recognizing');
            liveText.innerHTML = finalTranscript + '<span style="color: #999;">' + interimTranscript + '</span>';
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
        };

        recognition.onend = () => {
            const liveText = document.getElementById('live-transcript-text');
            liveText.classList.remove('recognizing');

            // Show final transcript in recorded audio section
            if (finalTranscript.trim()) {
                document.getElementById('final-transcript').style.display = 'block';
                document.getElementById('final-transcript-text').textContent = finalTranscript.trim();
            }
        };

        recognition.start();
        console.log('Speech recognition started');

    } catch (error) {
        console.error('Error starting speech recognition:', error);
    }
}

// Stop speech recognition
function stopSpeechRecognition() {
    if (recognition) {
        recognition.stop();
        recognition = null;
    }
}

// Clear transcript
function clearTranscript() {
    finalTranscript = '';
    interimTranscript = '';
    document.getElementById('live-transcript-text').textContent = '음성을 인식하는 중...';
    document.getElementById('final-transcript').style.display = 'none';
}

// Stop recording
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();

        // Stop all tracks
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
        }

        // Stop speech recognition
        stopSpeechRecognition();

        // Update UI
        const recordBtn = document.getElementById('record-btn');
        const recordText = document.getElementById('record-text');
        recordBtn.classList.remove('recording');
        recordText.textContent = '녹음 시작';

        // Stop timer
        if (recordingInterval) {
            clearInterval(recordingInterval);
        }
        document.getElementById('recording-time').style.display = 'none';

        console.log('Recording stopped');
    }
}

// Update recording time
function updateRecordingTime() {
    const elapsed = Date.now() - recordingStartTime;
    const seconds = Math.floor(elapsed / 1000);
    const milliseconds = Math.floor((elapsed % 1000) / 100);
    const timeDisplay = document.getElementById('time-display');
    timeDisplay.textContent = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}.${milliseconds}`;
}

// Start audio visualizer
function startVisualizer() {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(audioStream);
    source.connect(analyser);

    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const canvas = document.getElementById('visualizer-canvas');
    const canvasCtx = canvas.getContext('2d');

    document.getElementById('audio-visualizer').style.display = 'block';

    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = 100;

    function draw() {
        animationFrame = requestAnimationFrame(draw);

        analyser.getByteFrequencyData(dataArray);

        canvasCtx.fillStyle = '#000';
        canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / bufferLength) * 2.5;
        let barHeight;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            barHeight = (dataArray[i] / 255) * canvas.height;

            const hue = (i / bufferLength) * 360;
            canvasCtx.fillStyle = `hsl(${hue}, 100%, 50%)`;
            canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

            x += barWidth + 1;
        }
    }

    draw();
}

// Analyze recorded audio
async function analyzeRecordedAudio() {
    if (!recordedBlob) {
        alert('먼저 음성을 녹음하세요.');
        return;
    }

    showLoading();

    try {
        const formData = new FormData();
        // Use correct file extension based on recorded mimeType
        const extension = recordedBlob.type.includes('webm') ? '.webm' :
                         recordedBlob.type.includes('ogg') ? '.ogg' :
                         recordedBlob.type.includes('m4a') ? '.m4a' :
                         recordedBlob.type.includes('mp4') ? '.m4a' : '.wav';
        formData.append('file', recordedBlob, `recording${extension}`);

        const response = await fetch(`${API_BASE}/api/analyze/audio`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Convert AnalysisResponse format to Gemini format for display
        const geminiFormat = {
            score: data.risk_score,
            risk_level: data.risk_level,
            is_phishing: data.is_phishing,
            reasoning: data.alert_message,
            model: "Gemini 2.5 Flash + Rule Filter",
            filter_applied: data.component_scores?.filter_applied || false,
            llm_score: data.component_scores?.llm_score || data.risk_score,
            keyword_analysis: {},
            cached: false
        };

        displayGeminiResults(geminiFormat);
    } catch (error) {
        console.error('Error:', error);
        alert('분석 중 오류가 발생했습니다: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Analyze audio file
async function analyzeAudioFile() {
    const fileInput = document.getElementById('audio-file');
    const file = fileInput.files[0];

    if (!file) {
        alert('음성 파일을 선택하세요.');
        return;
    }

    // Get audio duration for time estimation
    let audioDuration = null;
    try {
        audioDuration = await getAudioDuration(file);
        console.log('[DEBUG] Audio duration:', audioDuration, 'seconds');
    } catch (e) {
        console.warn('Could not determine audio duration:', e);
    }

    // Show loading with estimated time
    showLoading(audioDuration);

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/analyze/audio`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data, true);
    } catch (error) {
        console.error('Error:', error);
        alert('분석 중 오류가 발생했습니다: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Display results
// Display Gemini API results
function displayGeminiResults(data) {
    // Show results section
    document.getElementById('results').style.display = 'block';

    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });

    // Update risk score (using Gemini's score 0-100)
    updateRiskScore(data.score, data.risk_level);

    // Update risk info
    document.getElementById('risk-level').textContent = data.risk_level;
    document.getElementById('risk-level').className = `risk-level ${data.is_phishing ? 'CRITICAL' : 'SAFE'}`;
    document.getElementById('alert-message').textContent = data.reasoning;

    const phishingBadge = document.getElementById('is-phishing');
    phishingBadge.innerHTML = `<span>피싱 여부: </span><strong>${data.is_phishing ? '예' : '아니오'}</strong>`;
    phishingBadge.style.color = data.is_phishing ? 'var(--danger-color)' : 'var(--success-color)';

    // Hide component scores and techniques sections
    const componentScoresDiv = document.querySelector('.component-scores');
    const scoresContainer = document.getElementById('scores-container');
    if (componentScoresDiv) {
        componentScoresDiv.style.display = 'none';
    }
    if (scoresContainer) {
        scoresContainer.style.display = 'none';
    }

    const techniquesDiv = document.querySelector('.techniques');
    if (techniquesDiv) {
        techniquesDiv.style.display = 'none';
    }

    // Hide PII and transcript sections (not used in Gemini API)
    document.getElementById('pii-section').style.display = 'none';
    document.getElementById('transcript-section').style.display = 'none';
}

function displayResults(data, isAudio = false) {
    // Show results section
    document.getElementById('results').style.display = 'block';

    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });

    // Update risk score
    updateRiskScore(data.risk_score, data.risk_level);

    // Update risk info
    document.getElementById('risk-level').textContent = data.risk_level;
    document.getElementById('risk-level').className = `risk-level ${data.risk_level}`;
    document.getElementById('alert-message').textContent = data.alert_message;

    const phishingBadge = document.getElementById('is-phishing');
    phishingBadge.innerHTML = `<span>피싱 여부: </span><strong>${data.is_phishing ? '예' : '아니오'}</strong>`;
    phishingBadge.style.color = data.is_phishing ? 'var(--danger-color)' : 'var(--success-color)';

    // Update component scores
    updateComponentScores(data.component_scores);

    // Update techniques
    updateTechniques(data.techniques_detected);

    // Update PII section
    if (data.masked_text) {
        document.getElementById('pii-section').style.display = 'block';
        document.getElementById('masked-text').textContent = data.masked_text;

        const piiDetected = data.pii_detected || {};
        const piiText = Object.keys(piiDetected).length > 0
            ? `감지된 개인정보: ${Object.entries(piiDetected).map(([k, v]) => `${k} ${v}건`).join(', ')}`
            : '개인정보가 감지되지 않았습니다.';
        document.getElementById('pii-detected').textContent = piiText;
    } else {
        document.getElementById('pii-section').style.display = 'none';
    }

    // Update transcript (for audio)
    if (isAudio && data.transcript) {
        document.getElementById('transcript-section').style.display = 'block';
        document.getElementById('transcript').textContent = data.transcript;
    } else {
        document.getElementById('transcript-section').style.display = 'none';
    }
}

// Update risk score gauge
function updateRiskScore(score, level) {
    const scoreElement = document.getElementById('risk-score');
    const gaugeFill = document.getElementById('gauge-fill');

    // Animate score
    let current = 0;
    const target = Math.round(score);
    const increment = target / 50;

    const interval = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(interval);
        }
        scoreElement.textContent = Math.round(current);
    }, 20);

    // Update gauge fill
    const dashArray = 251.2;
    const dashOffset = dashArray - (dashArray * score / 100);
    gaugeFill.style.strokeDashoffset = dashOffset;

    // Update gauge color
    let color;
    if (score >= 90) color = '#d32f2f';
    else if (score >= 70) color = '#f44336';
    else if (score >= 50) color = '#ff9800';
    else if (score >= 30) color = '#ffc107';
    else color = '#4CAF50';

    gaugeFill.style.stroke = color;
    scoreElement.style.color = color;
}

// Update component scores
function updateComponentScores(scores) {
    if (!scores) return;

    if (scores.keyword !== undefined) updateBar('keyword', scores.keyword);
    if (scores.sentiment !== undefined) updateBar('sentiment', scores.sentiment);
    if (scores.similarity !== undefined) updateBar('similarity', scores.similarity);
}

function updateBar(type, value) {
    const bar = document.getElementById(`${type}-bar`);
    const valueSpan = document.getElementById(`${type}-score`);

    if (!bar || !valueSpan || value === undefined) return;

    setTimeout(() => {
        bar.style.width = `${value}%`;
        valueSpan.textContent = value.toFixed(1);
    }, 100);
}

// Update techniques
function updateTechniques(techniques) {
    const container = document.getElementById('techniques');

    if (!techniques || techniques.length === 0) {
        container.innerHTML = '<span class="no-data">탐지된 기법이 없습니다.</span>';
        return;
    }

    container.innerHTML = techniques.map(tech =>
        `<span class="technique-tag">${tech}</span>`
    ).join('');
}

// Helper function to get audio duration
function getAudioDuration(file) {
    return new Promise((resolve, reject) => {
        const audio = document.createElement('audio');
        audio.preload = 'metadata';

        audio.onloadedmetadata = function() {
            window.URL.revokeObjectURL(audio.src);
            resolve(audio.duration);
        };

        audio.onerror = function() {
            reject(new Error('Failed to load audio'));
        };

        audio.src = URL.createObjectURL(file);
    });
}

// Loading state with timer
let loadingStartTime = null;
let loadingTimer = null;

function showLoading(audioDuration = null) {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    // Start timer
    loadingStartTime = Date.now();
    const timerElement = document.querySelector('.loading-text');

    // Estimate processing time: ~0.5x audio duration for STT + 2s for analysis
    const estimatedTime = audioDuration ? Math.ceil(audioDuration * 0.5 + 2) : null;

    if (timerElement) {
        loadingTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - loadingStartTime) / 1000);

            if (estimatedTime && elapsed < estimatedTime) {
                const remaining = estimatedTime - elapsed;
                timerElement.textContent = `분석 중... (${elapsed}초 경과 / 약 ${remaining}초 남음)`;
            } else if (estimatedTime && elapsed >= estimatedTime) {
                timerElement.textContent = `분석 중... (${elapsed}초 경과 / 거의 완료)`;
            } else {
                timerElement.textContent = `분석 중... (${elapsed}초 경과)`;
            }
        }, 100);
    }
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';

    // Clear timer
    if (loadingTimer) {
        clearInterval(loadingTimer);
        loadingTimer = null;
    }

    // Reset text
    const timerElement = document.querySelector('.loading-text');
    if (timerElement) {
        timerElement.textContent = '분석 중...';
    }
}

// File input handling
document.getElementById('audio-file')?.addEventListener('change', function(e) {
    const fileName = e.target.files[0]?.name || '파일을 선택하세요';
    document.getElementById('file-name').textContent = fileName;
});

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('Sentinel-Voice Demo Ready');
});

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

    const piiMasking = document.getElementById('pii-masking').checked;

    // Show loading
    showLoading();

    try {
        const response = await fetch(`${API_BASE}/api/analyze/text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                enable_pii_masking: piiMasking
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
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

        // Create media recorder
        mediaRecorder = new MediaRecorder(audioStream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            // Create blob from chunks
            recordedBlob = new Blob(audioChunks, { type: 'audio/wav' });

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

        console.log('Recording started');

    } catch (error) {
        console.error('Error starting recording:', error);
        alert('마이크 접근 권한이 필요합니다.');
    }
}

// Stop recording
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();

        // Stop all tracks
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
        }

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
        formData.append('file', recordedBlob, 'recording.wav');

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

// Analyze audio file
async function analyzeAudioFile() {
    const fileInput = document.getElementById('audio-file');
    const file = fileInput.files[0];

    if (!file) {
        alert('음성 파일을 선택하세요.');
        return;
    }

    // Show loading
    showLoading();

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
    updateBar('keyword', scores.keyword);
    updateBar('sentiment', scores.sentiment);
    updateBar('similarity', scores.similarity);
}

function updateBar(type, value) {
    const bar = document.getElementById(`${type}-bar`);
    const valueSpan = document.getElementById(`${type}-score`);

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

// Loading state
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
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

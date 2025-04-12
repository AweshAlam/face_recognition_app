document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const loginBtn = document.getElementById('login-btn');
    const messageDiv = document.getElementById('message');
    const loginFeedback = document.getElementById('login-feedback');
    const context = canvas.getContext('2d');

    let faceDetectionInterval;

    // Access Webcam and Start Face Detection
    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            video.srcObject = stream;
            video.play();
            loginFeedback.textContent = 'Camera active. Click button to log in.';

            // Start face detection loop after camera is active
            video.addEventListener('loadedmetadata', () => {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                console.log('Video dimensions:', video.videoWidth, video.videoHeight);
                startFaceDetectionLoop();
            });

        } catch (err) {
            console.error("Error accessing webcam: ", err);
            messageDiv.textContent = 'Error accessing webcam. Please ensure permission is granted.';
            messageDiv.className = 'message error';
            loginBtn.disabled = true;
        }
    }

    async function startFaceDetectionLoop() {
        console.log('Face detection loop running');
        faceDetectionInterval = setInterval(async () => {
            const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions());
            // console.log('Detections:', detections);
    
            // Clear the canvas
            context.clearRect(0, 0, canvas.width, canvas.height);
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
            detections.forEach(detection => {
                const box = detection.box;
                // console.log('Detection Box:', box);
                context.strokeStyle = 'green'; // Or 'red' if you prefer
                context.lineWidth = 3;
                context.strokeRect(box.x, box.y, box.width, box.height);
            });
        }, 100); // Adjust interval as needed (e.g., every 100ms)
    }

    // Handle Login Attempt
    loginBtn.addEventListener('click', async () => {
        loginFeedback.textContent = 'Capturing & Processing...';
        messageDiv.textContent = ''; // Clear previous messages
        loginBtn.disabled = true; // Disable button during attempt

        // Stop face detection during login attempt
        clearInterval(faceDetectionInterval);

        // Capture image
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageData = canvas.toDataURL('image/jpeg', 0.9);

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image: imageData }),
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                messageDiv.textContent = result.message;
                messageDiv.className = 'message success';
                loginFeedback.textContent = 'Login successful! Redirecting...';
                window.location.href = result.redirect_url || '/dashboard';
            } else {
                messageDiv.textContent = `Login failed: ${result.message}`;
                messageDiv.className = 'message error';
                loginFeedback.textContent = 'Login failed. Try again.';
                loginBtn.disabled = false; // Re-enable button
                startFaceDetectionLoop(); // Restart face detection
            }
        } catch (error) {
            console.error('Error during login fetch:', error);
            messageDiv.textContent = 'An error occurred during login. Please check console or try again.';
            messageDiv.className = 'message error';
            loginFeedback.textContent = 'Error. Please try again.';
            loginBtn.disabled = false; // Re-enable button
            startFaceDetectionLoop(); // Restart face detection
        }
    });

    // Initialize
    startCamera();
});
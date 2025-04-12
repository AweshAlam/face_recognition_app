document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureBtn = document.getElementById('capture-btn');
    const submitBtn = document.getElementById('submit-btn');
    const registerForm = document.getElementById('register-form');
    const messageDiv = document.getElementById('message');
    const captureFeedback = document.getElementById('capture-feedback');
    const capturedImagesContainer = document.getElementById('captured-images-container');
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const context = canvas.getContext('2d');

    let capturedImageDatas = [];
    let faceDetectionInterval;
    const maxCaptures = 5;

    // Access Webcam and Start Face Detection
    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            video.srcObject = stream;
            video.play();
            captureFeedback.textContent = 'Camera started. Position your face clearly.';

            video.addEventListener('loadedmetadata', () => {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                startFaceDetectionLoop();
            });

        } catch (err) {
            console.error("Error accessing webcam: ", err);
            messageDiv.textContent = 'Error accessing webcam. Please ensure permission is granted and no other app is using it.';
            messageDiv.className = 'message error';
            captureBtn.disabled = true;
        }
    }

    async function startFaceDetectionLoop() {
        faceDetectionInterval = setInterval(async () => {
            const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions());

            context.clearRect(0, 0, canvas.width, canvas.height);
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            detections.forEach(detection => {
                const box = detection.box;
                context.strokeStyle = 'green';
                context.lineWidth = 3;
                context.strokeRect(box.x, box.y, box.width, box.height);
            });
        }, 100);
    }

    // Capture Photo
    captureBtn.addEventListener('click', () => {
        if (capturedImageDatas.length < maxCaptures) {
            captureFeedback.textContent = 'Capturing...';
            canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = canvas.toDataURL('image/jpeg', 0.9);
            capturedImageDatas.push(imageData);

            // Display thumbnail with number
            const imgContainer = document.createElement('div');
            imgContainer.style.position = 'relative'; // For absolute positioning of the number
            const img = document.createElement('img');
            img.src = imageData;
            img.classList.add('captured-image-thumbnail');
            imgContainer.appendChild(img);

            const numberSpan = document.createElement('span');
            numberSpan.textContent = capturedImageDatas.length;
            numberSpan.style.position = 'absolute';
            numberSpan.style.bottom = '2px';
            numberSpan.style.right = '2px';
            numberSpan.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            numberSpan.style.color = 'white';
            numberSpan.style.fontSize = '0.8em';
            numberSpan.style.padding = '2px 4px';
            numberSpan.style.borderRadius = '4px';
            imgContainer.appendChild(numberSpan);

            capturedImagesContainer.appendChild(imgContainer);

            captureBtn.textContent = `Capture Photo (${capturedImageDatas.length}/${maxCaptures})`;
            captureFeedback.textContent = `Photo captured! ${capturedImageDatas.length}/${maxCaptures} images taken.`;

            console.log('Captured Images Count:', capturedImageDatas.length); // ADDED
            if (capturedImageDatas.length === maxCaptures) {
                console.log('Max captures reached, enabling submit button.'); // ADDED
                submitBtn.disabled = false; // Enable submit button after 5 captures
                captureBtn.disabled = true; // Disable capture button
                captureFeedback.textContent = 'All 5 photos captured. You can now fill details and register.';
                clearInterval(faceDetectionInterval); // Stop face detection
            }
        } else {
            captureFeedback.textContent = `You have already captured ${maxCaptures} photos.`;
        }
    });

    // Handle Registration Submission
    registerForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        if (capturedImageDatas.length !== maxCaptures) {
            messageDiv.textContent = `Please capture exactly ${maxCaptures} photos.`;
            messageDiv.className = 'message error';
            return;
        }

        const name = nameInput.value.trim();
        const email = emailInput.value.trim();

        if (!name || !email) {
            messageDiv.textContent = 'Please enter both name and email.';
            messageDiv.className = 'message error';
            return;
        }

        messageDiv.textContent = 'Processing registration...';
        messageDiv.className = 'message info';
        submitBtn.disabled = true; // Keep it disabled during processing

        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    email: email,
                    images: capturedImageDatas // Send a list of image data
                }),
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                messageDiv.textContent = result.message + ' Redirecting to login...';
                messageDiv.className = 'message success';
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else {
                messageDiv.textContent = `Registration failed: ${result.message}`;
                messageDiv.className = 'message error';
                submitBtn.disabled = false; // Re-enable in case of failure
                captureBtn.disabled = false; // Re-enable capture button for retry
                startFaceDetectionLoop(); // Restart face detection
            }
        } catch (error) {
            console.error('Error during registration fetch:', error);
            messageDiv.textContent = 'An error occurred during registration. Please check console or try again.';
            messageDiv.className = 'message error';
            submitBtn.disabled = false; // Re-enable in case of failure
            captureBtn.disabled = false; // Re-enable capture button for retry
            startFaceDetectionLoop(); // Restart face detection
        }
    });

    // Initialize
    startCamera();
});
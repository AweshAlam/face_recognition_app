import face_recognition
import numpy as np
import cv2
import base64
from PIL import Image
import io

# --- Configuration ---
# Lower tolerance means stricter matching (0.6 is common)
FACE_COMPARISON_TOLERANCE = 0.6

# --- Helper Functions ---

def base64_to_image(base64_string):
    """Converts a Base64 string (with or without prefix) to an OpenCV image (NumPy array)."""
    if "base64," in base64_string:
        base64_string = base64_string.split("base64,")[1]
    try:
        img_bytes = base64.b64decode(base64_string)
        img_pil = Image.open(io.BytesIO(img_bytes))
        # Convert PIL Image to OpenCV format (NumPy array)
        # PIL is RGB, OpenCV is BGR
        img_np = np.array(img_pil)
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        return img_cv
    except Exception as e:
        print(f"Error decoding base64 string: {e}")
        return None

def get_face_encodings(image):
    """
    Detects faces and computes their 128-d embeddings.
    Returns a list of embeddings, or None if error, empty list if no faces.
    """
    if image is None:
        return None # Indicate error in decoding/loading

    # Convert BGR (OpenCV) to RGB (face_recognition)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    try:
        # Detect face locations (using HOG or CNN model)
        # model='cnn' is more accurate but slower, requires dlib compiled with CUDA for GPU speedup
        face_locations = face_recognition.face_locations(rgb_image, model='hog')

        if not face_locations:
            print("No faces detected in the image.")
            return [] # Indicate no faces found

        if len(face_locations) > 1:
            print(f"Warning: Multiple ({len(face_locations)}) faces detected. Using the first one.")
            # Optionally, you could try to find the largest face or return an error

        # Compute face encodings (128-d vectors)
        # We only compute for the first face if multiple are found
        face_encodings = face_recognition.face_encodings(rgb_image, [face_locations[0]])
        return face_encodings # Returns a list containing one embedding array
    except Exception as e:
        print(f"Error during face encoding: {e}")
        return None

def compare_faces(known_face_encodings, face_encoding_to_check):
    """
    Compares a face encoding against a list of known encodings.
    Returns the index of the best match if found, otherwise None.
    """
    if not known_face_encodings or face_encoding_to_check is None or len(face_encoding_to_check) == 0:
        return None

    # Ensure encodings are NumPy arrays
    known_encodings_np = [np.array(enc) for enc in known_face_encodings]
    if not face_encoding_to_check or not isinstance(face_encoding_to_check, list) or len(face_encoding_to_check) == 0:
        return None
    encoding_to_check_np = np.array(face_encoding_to_check[0]) # We assume one encoding to check

    # Compare faces
    matches = face_recognition.compare_faces(
        known_encodings_np,
        encoding_to_check_np,
        tolerance=FACE_COMPARISON_TOLERANCE
    )

    # Calculate distances (lower is better match)
    face_distances = face_recognition.face_distance(
        known_encodings_np,
        encoding_to_check_np
    )

    best_match_index = -1
    min_distance = 1.0 # Max possible distance is sqrt(2) ~= 1.4, tolerance is typically < 1.0

    # Find the best match among those that passed the tolerance threshold
    if True in matches:
        # Find the index of the first match
        # For a more robust approach, find the match with the minimum distance
        matched_indices = [i for i, match in enumerate(matches) if match]
        distances_of_matches = face_distances[matched_indices]
        best_match_index_in_matches = np.argmin(distances_of_matches)
        best_match_index = matched_indices[best_match_index_in_matches]

        print(f"Match found. Index: {best_match_index}, Distance: {face_distances[best_match_index]:.4f}")
        return best_match_index
    else:
        print("No match found within tolerance.")
        if len(face_distances) > 0:
            print(f"Minimum distance found: {np.min(face_distances):.4f} (Tolerance: {FACE_COMPARISON_TOLERANCE})")
        return None
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from db_config import users_collection, SECRET_KEY # Import collection and secret key
from face_utils import base64_to_image, get_face_encodings, compare_faces
import os
import numpy as np
from bson.objectid import ObjectId # Import ObjectId

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = SECRET_KEY # Needed for session management

# --- Basic Session Check ---
# In a real app, you'd have more robust auth checks
def is_logged_in():
    return 'user_id' in session

# --- Routes ---

@app.route('/')
def index():
    if is_logged_in():
        user_id_str = session['user_id']
        user = users_collection.find_one({"_id": ObjectId(user_id_str)})
        return render_template('dashboard.html', user_name=user.get('name', 'User'))
    return render_template('index.html') # Landing page with links to register/login

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid request data"}), 400

        name = data.get('name')
        email = data.get('email')
        images_base64 = data.get('images') # Expecting a list of base64 strings

        if not name or not email or not images_base64 or not isinstance(images_base64, list) or len(images_base64) != 5:
            return jsonify({"status": "error", "message": "Missing required fields or incorrect number of images (expecting 5)"}), 400

        # Check if email already exists
        if users_collection.find_one({"email": email}):
            return jsonify({"status": "error", "message": f"Email '{email}' already registered."}), 409

        face_embeddings_list = []
        for image_base64 in images_base64:
            image = base64_to_image(image_base64)
            if image is None:
                return jsonify({"status": "error", "message": "Failed to decode one of the images"}), 400

            face_encodings = get_face_encodings(image)

            if face_encodings is None or not face_encodings:
                return jsonify({"status": "error", "message": "No face detected in one of the images. Please try again."}), 400
            if len(face_encodings) > 1:
                return jsonify({"status": "error", "message": "Multiple faces detected in one of the images. Please ensure only one face is clearly visible."}), 400

            face_embeddings_list.append(face_encodings[0].tolist()) # Convert to list

        # Store user data in MongoDB
        try:
            user_data = {
                "name": name,
                "email": email,
                "face_embeddings": face_embeddings_list # Store a list of embeddings
            }
            result = users_collection.insert_one(user_data)
            print(f"User registered successfully with ID: {result.inserted_id}")
            flash("Registration successful! You can now log in.", "success")
            return jsonify({"status": "success", "message": "Registration successful!"})

        except Exception as e:
            print(f"Error inserting user into MongoDB: {e}")
            return jsonify({"status": "error", "message": "Database error during registration."}), 500

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"status": "error", "message": "Missing image data"}), 400

        image_base64 = data.get('image')
        image = base64_to_image(image_base64)
        if image is None:
            return jsonify({"status": "error", "message": "Failed to decode image"}), 400

        # Get encoding of the face in the login attempt
        unknown_encodings = get_face_encodings(image)

        if unknown_encodings is None:
            return jsonify({"status": "error", "message": "Error processing login image."}), 500
        if not unknown_encodings:
            return jsonify({"status": "error", "message": "No face detected in login image."}), 400
        if len(unknown_encodings) > 1:
            return jsonify({"status": "error", "message": "Multiple faces detected in login image."}), 400

        # Retrieve known faces from DB
        try:
            known_users = list(users_collection.find({}, {"_id": 1, "name": 1, "face_embeddings": 1})) # Changed field name
            if not known_users:
                return jsonify({"status": "error", "message": "No registered users found."}), 404

            known_ids = []
            known_names = []

            for user in known_users:
                embeddings = user.get("face_embeddings") # Get the list of embeddings
                if isinstance(embeddings, list) and len(embeddings) > 0:
                    known_embeddings = [np.array(emb) for emb in embeddings] # Convert list of lists to list of numpy arrays
                    known_ids.append(user["_id"])
                    known_names.append(user.get("name", "N/A"))

                    # Compare with all embeddings for the user
                    for known_embedding in known_embeddings:
                        match = compare_faces([known_embedding], unknown_encodings) # Compare one by one
                        if match is not None:
                            matched_user_id = user["_id"]
                            matched_user_name = user.get("name", "N/A")
                            session['user_id'] = str(matched_user_id) # Store user ID as string
                            session['user_name'] = matched_user_name
                            print(f"Login successful for user: {matched_user_name} (ID: {matched_user_id})")
                            flash(f"Welcome back, {matched_user_name}!", "success")
                            return jsonify({
                                "status": "success",
                                "message": f"Login successful! Welcome {matched_user_name}!",
                                "redirect_url": url_for('dashboard')
                            })
                else:
                    print(f"Warning: No valid face embeddings found for user {user.get('_id')}.")

            # If no match found after checking all users and their embeddings
            print("Login failed: Face not recognized.")
            return jsonify({"status": "error", "message": "Login failed. Face not recognized or does not match."}), 401

        except Exception as e:
            print(f"Error retrieving users from MongoDB during login: {e}")
            return jsonify({"status": "error", "message": "Database error during login."}), 500

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))

    # Fetch user details again for display (or use session data)
    user_id_str = session['user_id']
    user = users_collection.find_one({"_id": ObjectId(user_id_str)})
    if not user:
        # Handle case where user might have been deleted after login
        session.pop('user_id', None)
        session.pop('user_name', None)
        flash("Your user account was not found. Please log in again.", "error")
        return redirect(url_for('login'))

    return render_template('dashboard.html', user_name=user.get('name', 'User'))


@app.route('/logout')
def logout():
    session.pop('user_id', None) # Remove user ID from session
    session.pop('user_name', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))


# --- Run the App ---
if __name__ == '__main__':
    # Check if the collection object was successfully created in db_config.py
    if users_collection is None:
        print("\n !!! MongoDB Collection not available (likely due to connection error during startup). Cannot start Flask app. !!!\n")
        print("Check terminal output above for MongoDB connection errors.")
    else:
        # Use 0.0.0.0 to make it accessible on your network (use with caution)
        # debug=True is helpful for development but should be False in production
        print(f"Starting Flask app. Access at http://127.0.0.1:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
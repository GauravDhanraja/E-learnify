
import datetime
import os
import pyrebase, firebase_auth, firebase_admin
from firebase_admin import credentials, firestore, storage
from flask import Flask, render_template, request, url_for, session, send_file, redirect
import essentials.credentials


firebase_admin.initialize_app(credentials.Certificate(essentials.credentials.creds_for_firebase()))
firebase = pyrebase.initialize_app(essentials.credentials.creds_for_pyrebase())
auth = firebase.auth()

app = firebase_admin.initialize_app(credentials.Certificate(essentials.credentials.creds_for_firebase()), {
    "storageBucket" : "e-learnify-898a1.appspot.com",
}, name="storage")
bucket = storage.bucket(app=app)

db = firestore.client()

#userData = db.collection("users").document(session["user_id"]).get().to_dict()

app = Flask(__name__, static_url_path='/static', static_folder='static')


def sign_in(email, password):
    user_record = auth.sign_in_with_email_and_password(email, password)
    return user_record

def sign_out():
    del session['user_id']
    return True

def get_users_data():
    user_id = session["user_id"]
    data = db.collection('users').document(session['user_id']).get().to_dict()

    return data


@app.before_request
def authenticate():
    if 'user_id' not in session and request.endpoint == 'index':
        return redirect(url_for('sign_in_route'))
    
@app.route('/', methods=['POST', 'GET'])
def index():
    return redirect(url_for('sign_in_route'))


@app.route('/sign-out')
def sign_out_route():
    if sign_out():
        session.pop('user_id', None)
        return redirect(url_for('sign_in_route'))
    else:
        return 'Sign-out failed'


@app.route('/admin/home')
def admin_dashboard():
    if 'user_id' in session:
        userDetails = get_users_data()
        userData = {"name" : userDetails["name"],}
        return render_template("admin/home.html",userData = userData)
    else:
        return redirect(url_for('sign_in_route'))


@app.route('/student/home', methods=["GET", "POST"])
def public_dashboard():
    if 'user_id' in session:
        userDetails = get_users_data()
        userData = {"name" : userDetails["name"],}
        return render_template("public/home.html",userData = userData)
    else:
        return redirect(url_for('sign_in_route'))    


@app.route("/student/profile", methods = ["GET"])
def profile_page():
    if 'user_id' in session:
        userDetails = get_users_data()
        userData = {"name" : userDetails["name"],}
    return render_template("public/profile.html",userData = userData)


@app.route('/userprof/<filename>')
def get_user_profile_pic(filename):
    blob = bucket.blob(f'userprof/{filename}')
    
    temp_file = os.path.join(app.static_folder, 'images', filename)
    blob.download_to_filename(temp_file)
    
    return send_file(temp_file, mimetype='image/png')


@app.route("/student/announcements", methods = ["GET"])
def courses_dashboard():
    if 'user_id' in session:
        userDetails = get_users_data()
        userData = {"name" : userDetails["name"],}
    return render_template("public/announcements.html",userData = userData)


@app.route('/sign-in', methods=['POST', 'GET'])
@app.route('/sign-in', methods=['POST', 'GET'])
def sign_in_route():
    if 'user_id' in session:
        # Fetch user's role from session data
        user_id = session['user_id']
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_role = user_data.get('role', None)
            
            # Redirect based on user's role
            if user_role == "student":
                return redirect(url_for('public_dashboard'))
            elif user_role == "admin":
                return redirect(url_for('admin_dashboard'))
            else:
                return 'You are not authorized to access this dashboard.'

    # If user is not already authenticated or their role is not defined, proceed with sign-in
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            if not email or not password:
                return 'Email and password are required.'
            user_record = sign_in(email, password)
            
            # Fetch user's role from Firestore
            user_doc = db.collection('users').document(user_record["localId"]).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_role = user_data.get('role', None)
                
                # Redirect based on user's role
                if user_role == "student":
                    session["user_id"] = user_record["localId"]
                    return redirect(url_for('public_dashboard'))
                elif user_role == "admin":
                    session["user_id"] = user_record["localId"]
                    return redirect(url_for('admin_dashboard'))
                else:
                    return 'You are not authorized to access this dashboard.'
            else:
                return 'User data not found.'

        except Exception as e:
            print("Exception:", e)
            return render_template('index.html')
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "MeOWmEWOnIGGAa")
    app.run(debug=True)

import datetime
import os
import pyrebase, firebase_auth, firebase_admin
from firebase_admin import credentials, firestore, storage
from flask import Flask, render_template, request, url_for, session, send_file, redirect, make_response
import essentials.credentials


firebase_admin.initialize_app(credentials.Certificate(essentials.credentials.creds_for_firebase()))
firebase = pyrebase.initialize_app(essentials.credentials.creds_for_pyrebase())
auth = firebase.auth()

app = firebase_admin.initialize_app(credentials.Certificate(essentials.credentials.creds_for_firebase()), {
    "storageBucket" : "e-learnify-898a1.appspot.com",
}, name="storage")
bucket = storage.bucket(app=app)

db = firestore.client()


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


@app.route("/admin/profile", methods = ["GET"])
def admin_profile_page():
    if 'user_id' in session:
        userDetails = get_users_data()
        userData = {"name" : userDetails["name"],}
    return render_template("admin/profile.html",userData = userData)


@app.route('/student/home', methods=["GET", "POST"])
def student_dashboard():
    if 'user_id' in session:
        userDetails = get_users_data()
        userData = {"name" : userDetails["name"],}
        return render_template("public/home.html",userData = userData)
    else:
        return redirect(url_for('sign_in_route'))    


@app.route("/student/profile", methods = ["GET"])
def student_profile_page():
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


def authenticate_user(email, password):
    if not email or not password:
        return None, 'Email and password are required'
    user_record = sign_in(email, password)
    session["user_id"] = user_record["localId"]
    return user_record, None

def fetch_user_role(user_id):
    user_doc = db.collection('users').document(user_id).get()
    user_data = {}
    if user_doc.exists:
        user_data = user_doc.to_dict()
    return user_data.get('role', None)

def redirect_based_on_role(user_role, user_record):
    if user_role == "student" or user_role == "admin":
        session["user_id"] = user_record["localId"]
        return redirect(url_for(f'{user_role}_dashboard'))
    else:
        return make_response('You are not authorized to access this dashboard.', 403)


@app.route('/sign-in', methods=['POST', 'GET'])
def sign_in_route():
    if 'user_id' in session:
        user_role = fetch_user_role(session['user_id'])
        return redirect_based_on_role(user_role)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_record, error = authenticate_user(email, password)
        if error:
            return "An error occured during authentication. Please try again."
        user_id = user_record["localId"]
        user_role = fetch_user_role(user_id)
        return redirect_based_on_role(user_role, user_record)

    return render_template('index.html')


if __name__ == "__main__":
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "MeOWmEWOnIGGAa")
    app.run(debug=True)
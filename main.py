
import datetime
import os
import pyrebase, firebase_auth, firebase_admin
from firebase_admin import credentials, firestore, storage
from flask import Flask, render_template, request, url_for, session, send_file, redirect

import essentials.credentials
import web.admin, web.public, web.uploads

firebase_admin.initialize_app(credentials.Certificate(essentials.credentials.creds_for_firebase()))
firebase = pyrebase.initialize_app(essentials.credentials.creds_for_pyrebase())
auth = firebase.auth()

app = firebase_admin.initialize_app(credentials.Certificate(essentials.credentials.creds_for_firebase()), {
    "storageBucket" : "e-learnify-898a1.appspot.com",
}, name="storage")
bucket = storage.bucket(app=app)

db = firestore.client()

#userData = db.collection("users").document(session["user_id"]).get().to_dict()

app = Flask(__name__)

def sign_in(email, password):
    user_record = auth.sign_in_with_email_and_password(email, password)
    return user_record

def sign_out():
    del session['user_id']
    return True

@app.before_request
def authenticate():
    if 'user_id' not in session and request.endpoint in ['home']:
        return redirect(url_for('sign_in_route'))
    
    
@app.route('/sign-in', methods=['POST', 'GET'])
def sign_in_route():
    if 'user_id' in session:
        if user_record  == "elearnify016@gmail.in":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("public_dashboard"))
    else:
        
        if request.method == 'POST':
            
            try:
                email = request.form.get('email')
                password = request.form.get('password')
                print(email, " ", password)
                if not email or not password:
                    return 'Email and password are required.'
                user_record = sign_in(email, password)
                if user_record and email == "elearnify016@gmail.com":
                    session['user_id'] = user_record['localId']
                    return redirect(url_for('admin_dashboard'))
                else:
                    session["user_id"] = user_record["localId"]
                    return redirect(url_for('public_dashboard'))
            except:
                return render_template('/public/sign_in.html')
        else:
            return render_template('/public/sign_in.html')
        

@app.route("/public/css/sign-in.css", methods=["GET"])
def public_index_css():
    return send_file("web/public/css/sign_in.css")


@app.route("/public/css/home.css", methods=["GET"])
def public_home_css():
    return send_file("web/public/css/home.css")


@app.route("/public/css/style.css", methods=["GET"])
def public_style_css():
    return send_file("web/public/css/style.css")


@app.route("/public/css/courses.css", methods=["GET"])
def public_courses_css():
    return send_file("web/public/css/courses.css")

@app.route("/public/js/script.js", methods=["GET"])
def public_script_js():
    return send_file("web/public/js/script.js")


@app.route('/sign-out')
def sign_out_route():
    if sign_out():
        session.pop('user_id', None)
        return redirect(url_for('sign_in_route'))
    else:
        return 'Sign-out failed'
    
    
@app.route('/admin/home', methods=["GET", "POST"])
def admin_dashboard():
    if request.method == 'GET':
        return render_template("admin/home.html",)
    

@app.route('/home', methods=["GET", "POST"])
def public_dashboard():
    if 'user_id' in session:
        user_id = session["user_id"]
        userDetails = db.collection("users").document(user_id).get().to_dict()
        userData = {"name" : userDetails["name"],}
        return render_template("public/home.html",userData = userData)
    else:
        return redirect(url_for('sign_in_route'))
    

@app.route("/images/profilepic", methods = ["GET"])
def profile_image_fetcher():
    try:
        user_id = session["user_id"]
        bucket.blob(f"userprof/{user_id}.jpg").download_to_filename("pfp.jpg")
    except:
        return "error"
    return send_file("pfp.jpg")
    
    

if __name__ == "__main__":
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "MeOWmEWOnIGGAa")
    app.run(debug=True)
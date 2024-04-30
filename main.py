
from datetime import datetime, timedelta
from google.cloud import storage
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
    session.clear()
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


courses = [
    {"title": "Discrete Mathematics and Transform Techniques", "thumbnail": "/static/images/dsc-mths.png", "name": "MAT"},
    {"title": "Materials Chemistry for Computer System", "thumbnail": "/static/images/chem.avif", "name": "CHE"},
    {"title": "Applied Digital Logic Design (ADLD)", "thumbnail": "/static/images/digital.jpg", "name": "ADLD"},
    {"title": "Introduction to C programming", "thumbnail": "/static/images/c.jpg", "name": "CPP"},
    {"title": "Basic Electrical Engineering", "thumbnail": "/static/images/elec.jpg", "name": "BEE"},
    {"title": "Technical English", "thumbnail": "/static/images/tech.jpg", "name": "ENG"},
    {"title": "Constitution of India", "thumbnail": "/static/images/constituiton.webp", "name": "COI"}
]

@app.route('/student/home', methods=["GET", "POST"])
def student_dashboard():
    if 'user_id' in session:
        user_details = get_users_data()
        userData = {"name" : user_details["name"],}
    
        return render_template("public/home.html", userData=userData, courses=courses)
    else:
        return redirect(url_for('sign_in_route'))

@app.route("/student/profile", methods = ["GET"])
def student_profile_page():
    if 'user_id' in session:
        user_details = get_users_data()
        userData = {"name" : user_details["name"], "usn": user_details["usn"]}
    return render_template("public/profile.html",userData = userData)


@app.route("/student/courses/<int:course_id>", methods = ["GET"])
def student_course(course_id):
    if 'user_id' in session:
        user_details = get_users_data()
        userData = {"name": user_details["name"]}
        course = courses[course_id]
        course_notes = show_course_notes(course['name'])
        
        return render_template("public/courses.html", userData=userData, course=course, course_notes=course_notes)

@app.route("/student/download_file/<course_name>/<filename>", methods = ['GET'])
def download_course_notes(course_name, filename):
    if 'user_id' in session:
        user_details = get_users_data()
        userData = {"name": user_details["name"]}
        
        course = next((c for c in courses if c['name'] == course_name), None)
        if course:
                blob = bucket.blob(f'subjects/{course_name}/public/{filename}')
                if blob.exists():
                    expiration_time = datetime.utcnow() + timedelta(minutes=60)
                    download_url = blob.generate_signed_url(expiration=expiration_time)
                    return redirect(download_url)
                else:
                    return "File not found", 404
        return "Course not found", 404
    else:
        return "Unauthorized", 401

def show_course_notes(course_name):
    if 'user_id' in session:  
        user_uid = session.get('user_uid')
        user_details = get_users_data()
        course = next((c for c in courses if c['name'] == course_name), None)
        if course:
            upload_path = f"subjects/{course_name}/public"  
            blobs = list(bucket.list_blobs(prefix=f"subjects/{course_name}/public/"))
            files = []
            for blob in blobs:
                file_data = {
                    'filename': blob.name.split('/')[-1],
                    'download_url': blob.public_url
                }
                files.append(file_data)
            return files
        else:
            return []

@app.route('/student/upload/<course_name>', methods=['POST'])
def upload_assignment(course_name):
    if 'user_id' in session:
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return """ 
            <script>
                alert("No file selected for upload!");
                window.history.back();
            </script>
            """

        user_uid = session.get('user_uid')
        user_details = get_users_data()
        usn = user_details["usn"]
        course = next((c for c in courses if c['name'] == course_name), None)
        if course:
            upload_path = f"subjects/{course_name}/private/{usn}"

            filename = uploaded_file.filename
            blob = bucket.blob(upload_path + '/' + filename)
            blob.upload_from_file(uploaded_file)

            return redirect(url_for("student_dashboard"))
        else:
            return "User not found!", 404



@app.route('/userprof/<filename>')
def get_user_profile_pic(filename):
    blob = bucket.blob(f'userprof/{filename}')
    
    temp_file = os.path.join(app.static_folder, 'images', filename)
    blob.download_to_filename(temp_file)
    
    return send_file(temp_file, mimetype='image/png')


def get_message(message_type):
    doc_ref = db.collection(message_type).document('announcement')
    doc = doc_ref.get().to_dict()

    if doc is not None:
        message = doc.get('message')
        return message
    else:
        return "No message..."

@app.route("/post-announcement", methods=["POST"])
def update_message():
    if 'user_id' in session:
        user_details = get_users_data()
        user_name = user_details["name"]
    else:
        return "Unauthorized! Please log in to post announcements."

    message = request.form.get("announcement-message")
    if not message:
        return "Announcement message cannot be empty."  

    try:
        ann_ref = db.collection(user_name).document('announcement')
        ann_ref.update({'message': message})
    except Exception as e:
        return f"Failed to post announcement: {str(e)}"
    return "Announcement submitted successfully!"  

@app.route("/student/announcements", methods = ["GET"])
def announcement_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login')) # or return a response with an error message
    user_details = get_users_data()
    if user_details is not None:
        userData = {"name" : user_details["name"],}
    else:
        userData = {}
    messages = {
        'adld_message': get_message('ADLD'),
        'cpp_message': get_message('CPP'),
        'mat_message': get_message('MAT'),
        'che_message': get_message('CHE'),
        'bee_message': get_message('BEE'),
        'eng_message': get_message('ENG'),
        'coi_message': get_message('COI')
    }
    return render_template("public/announcements.html",userData = userData, **messages)


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



@app.route('/admin/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return """ 
        <script>
            alert("No file selected for upload!");
            window.history.back();
        </script>
        """

    user_uid = session.get('user_uid')
    user_details = get_users_data()
    if user_details:
        user_name = user_details["name"]
        upload_path = f"subjects/{user_name}/public"

        filename = uploaded_file.filename
        blob = bucket.blob(upload_path + '/' + filename)
        blob.upload_from_file(uploaded_file)

        return redirect(url_for("admin_dashboard"))
    else:
        return "User not found!", 404

@app.route('/admin/delete_file', methods = ['POST'])
def delete_file():
    user_uid = session.get('user_uid')
    user_details = get_users_data()
    if user_details:
        user_name = user_details["name"]
        filename = request.form['filename']
        blob_name = f"subjects/{user_name}/public/{filename}"
        blob = bucket.blob(blob_name)
        blob.delete()
        return redirect(url_for("admin_dashboard"))

@app.route('/admin/download_file', methods=['POST'])
def download_file():
    filename = request.form['filename']
    user_uid = session.get('user_uid')
    user_details = get_users_data()
    if user_details:
        user_name = user_details["name"]
        blob_name = f"subjects/{user_name}/public/{filename}"
        blob = bucket.blob(blob_name)
        if blob.exists():
            expiration_time = datetime.utcnow() + timedelta(minutes=60)  # expires in 1 hour
            signed_url = blob.generate_signed_url(expiration = expiration_time, method='GET')
            return redirect(signed_url)
        else:
            return "File not found!", 404
    else:
        return "User not found!", 404

def show_uploaded_files():
    user_uid = session.get('user_uid')
    user_details = get_users_data()
    if user_details:
        user_name = user_details["name"]
        upload_path = f"subjects/{user_name}/public"
        blobs = list(bucket.list_blobs(prefix=f"subjects/{user_name}/public/"))
        files = []
        for blob in blobs:
            file_data = {
                'filename': blob.name.split('/')[-1],
                'download_url': blob.public_url
            }
            files.append(file_data)
        return files
    else:
        return []

@app.route('/admin/home')
def admin_dashboard():
    if 'user_id' in session:
        user_details = get_users_data()
        userData = {"name" : user_details["name"],}
        files = show_uploaded_files()
        return render_template("admin/home.html", userData = userData, files = files)
    else:
        return redirect(url_for('sign_in_route'))


@app.route("/admin/profile", methods = ["GET"])
def admin_profile_page():
    if 'user_id' in session:
        user_details = get_users_data()
        userData = {"name" : user_details["name"], "course": user_details["course_name"], "code": user_details["course_code"], "lect": user_details["lect"], "dep": user_details["dep"]}
    return render_template("admin/profile.html",userData = userData)


def get_usn(student_doc):
    student_data = student_doc.to_dict()
    return student_data.get('usn')

@app.route("/admin/students", methods=["GET"])
def admin_students_list():
    if 'user_id' in session:
        user_details = get_users_data()
        userData = {"name": user_details["name"]}
        students_ref = db.collection('users').where('role', '==', 'student').get()
        
        student_name = []
        student_usn = []    
        student_files = []
        for student_doc in students_ref:
            name = student_doc.get('name')
            usn = get_usn(student_doc)
            if name and usn:
                student_name.append(name)
                student_usn.append(usn)
                file_data = show_assignment(usn)
                student_files.append(file_data)  
        
        return render_template("admin/students.html", userData=userData, student_name=student_name, student_usn=student_usn, student_files=student_files)


def show_assignment(usn):
    user_uid = session.get('user_uid')
    user_details = get_users_data()
    if user_details:
        user_name = user_details["name"]
        upload_path = f"subjects/{user_name}/private"
        student_folder_prefix = f"{upload_path}/{usn}/"  
        student_blobs = list(bucket.list_blobs(prefix=student_folder_prefix))
        files = []
        for blob in student_blobs:
            file_data = {
                'filename': blob.name.split('/')[-1]
            }
            files.append(file_data)
        
        return files
    else:
        return []


@app.route('/admin/assignment_file', methods=['POST'])
def assignment_file():
    filename = request.form['filename']
    user_uid = session.get('user_uid')
    user_details = get_users_data()
    if user_details:
        user_name = user_details["name"]
        usn = request.form.get('usn')
        if usn:
            blob_name = f"subjects/{user_name}/private/{usn}/{filename}"
            blob = bucket.blob(blob_name)
            if blob.exists():
                expiration_time = datetime.utcnow() + timedelta(minutes=60)  # expires in 1 hour
                signed_url = blob.generate_signed_url(expiration=expiration_time, method='GET')
                return redirect(signed_url)
            else:
                return "File not found!", 404
        else:
            return "USN not provided!", 400
    else:
        return "User not found!", 404



if __name__ == "__main__":
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "MeOWmEWOnIGGAa")
    app.run(debug=True)
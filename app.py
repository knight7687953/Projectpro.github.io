from flask import Flask, session, redirect, url_for, request, render_template, jsonify
import pymongo, bcrypt, json, string
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)
app.secret_key = "saamdaam"

# Connect to MongoDB
client = pymongo.MongoClient("mongodb+srv://random:random@random.dcwtx3j.mongodb.net/?retryWrites=true&w=majority")
db = client["random"]
users = db["users"]
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        users = db["users"]
        if username and password:
            existing_user = users.find_one({"username": username})
            if existing_user is None:
                hashpass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                users.insert_one({"username": username, "password": hashpass, "projects": [], "role": "user", "name": name})
                return render_template('register_success.html')
        else:
            return render_template('wrong email.html')
        return render_template('wrong email.html')
    return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    users = db["users"]
    login_user = users.find_one({'username': request.form['username']})
    if login_user:
        if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            if login_user.get('role') == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('home'))
        return render_template('error.html')
    return render_template('error.html')

@app.route('/home')
def home():
    user = users.find_one({"username": session['username']})
    if user.get('role') == 'admin':
        return render_template('admin.html')
    projects = user.get('projects')
    return render_template('dashboard.html', projects=projects)

@app.route('/status', methods=['POST'])
def status():
    status_now = request.args.get('status')
    project_id = request.args.get('id')
    users.update_one(
    {'projects.project_id': project_id},
    {'$set': {'projects.$.status': status_now}})
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/submit', methods=['POST', 'GET'])
def submit_page():
    if request.method == 'GET':
        if 'username' in session:
            return render_template('submit.html')
        return redirect(url_for('login'))
    else:
        if 'username' in session:
            username = session['username']
            name = request.form['projectname']
            department = request.form['department']
            members = request.form.getlist('projectmembers[]')
            instructor = request.form['instructor']
            link = request.form['link']
            project = {"name": name,"department":department, "members": members, "link": link, "status": "pending", "project_id" : random_string(), "instructor": instructor}
            users.update_one({"username": username}, {"$push": {"projects": project}})
            return redirect(url_for('home'))
        return redirect(url_for('login'))

def random_string():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(10))

@app.route('/admin')
def admin():
    if 'username' in session and users.find_one({"username": session['username']}).get('role') == 'admin':
        all_projects = []
        for user in users.find():
            for project in user.get('projects'):
                all_projects.append(project)
        return render_template('admin.html', projects=all_projects)
    return render_template('login.html')

@app.route('/feedback', methods=['POST'])
def feedback():
    project_id = request.form['project_id']
    feedback_content = request.form['feedback']
    if feedback_content is not None:
        users.update_one({'projects.project_id': project_id},{'$set': {'projects.$.feedback': feedback_content}})
        return redirect(url_for('admin'))
    return "Something went wrong. <a href='/admin'>Try again.</a> "

if __name__ == '__main__':
    app.run()
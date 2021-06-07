from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
   return render_template('index.html')

@app.route('/post_home')
def post_home():
   return render_template('post_home.html')

@app.route('/login')
def login():
   return render_template('login.html')

@app.route('/sign_up')
def sign_up():
   return render_template('sign_up.html')

@app.route('/content')
def content():
   return render_template('content.html')

app.run('0.0.0.0',port=5000,debug=True)
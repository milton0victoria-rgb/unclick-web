import os
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')
@app.route("/googlef946c634cabb459.html")
def google_verification():
    return render_template("googlef946c634cabb459.html")
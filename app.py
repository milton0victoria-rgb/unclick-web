import os
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')
@app.route("/googlefd946c634cabb459.html")
def google_verification():
    return render_template("googlefd946c634cabb459.html")
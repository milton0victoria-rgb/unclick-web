import os
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')
@app.route("/googlefd946c634cabb459.html")
def google_verification():
    # Esto le dice a Google "aquí estoy", sin depender de leer el archivo
    return "google-site-verification: googlefd946c634cabb459.html"
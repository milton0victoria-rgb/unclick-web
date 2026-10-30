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

# --- NUEVA RUTA PARA EL SITEMAP ---
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    # Le decimos a Google que la única página es la principal
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://unclick-web.onrender.com/</loc>
            <changefreq>weekly</changefreq>
            <priority>1.0</priority>
        </url>
    </urlset>'''
    return xml, 200, {'Content-Type': 'application/xml'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


import sqlite3
import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'gasy_2026_final_secure'

DB_PATH = '/tmp/boutique.db'
TOKEN_TELEGRAM = "8632263179:AAFDjyU6d4eTCMgg4wM4xB1sDBGmWEMod2s"
ID_TELEGRAM = "7129218282"
# Assure-toi que cette URL est la bonne
BASE_URL = "https://reaction-gasy-com.onrender.com"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS commandes 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, pack TEXT, prix TEXT, 
                     lien TEXT, coms TEXT, mode TEXT, statut TEXT DEFAULT 'en_attente')''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    order_id = request.args.get('order_id')
    statut = None
    if order_id:
        try:
            conn = sqlite3.connect(DB_PATH)
            res = conn.execute("SELECT statut FROM commandes WHERE id=?", (order_id,)).fetchone()
            statut = res[0] if res else None
            conn.close()
        except: pass
    
    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reaction Gasy 🇲🇬</title>
        <style>
            body { font-family: sans-serif; background: #f0f2f5; padding: 20px; text-align: center; }
            .card { background: white; border-radius: 15px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
            .btn { background: #1877f2; color: white; border: none; padding: 12px; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; text-decoration: none; display: block; margin-top: 10px; }
            input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Reaction Gasy 🇲🇬</h2>
            {% if order_id %}
                {% if statut == 'en_attente' %}
                    <h3 style="color:orange;">⏳ Vérification...</h3>
                    <p>Commande #{{order_id}}. Dolayn vérifie ton paiement.</p>
                    <script>setTimeout(function(){ location.reload(); }, 6000);</script>
                {% elif statut == 'valide' %}
                    <h3 style="color:green;">✅ Payé !</h3>
                    <p>Commande validée. Merci !</p>
                    <a href="/" class="btn" style="background:green;">Nouvel achat</a>
                {% elif statut == 'refuse' %}
                    <h3 style="color:red;">❌ Refusé</h3>
                    <p>Paiement non validé.</p>
                    <a href="/" class="btn">Réessayer</a>
                {% endif %}
            {% else %}
                <form action="/order" method="post" enctype="multipart/form-data">
                    <input type="number" name="pack" placeholder="Quantité (ex: 100)" required>
                    <input type="text" name="lien" placeholder="Lien Facebook" required>
                    <input type="text" name="coms" placeholder="Ton nom">
                    <select name="mode"><option>Mobile Money</option><option>Carte Yas</option></select>
                    <input type="file" name="capture" required>
                    <button type="submit" class="btn">COMMANDER</button>
                </form>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, order_id=order_id, statut=statut)

@app.route('/order', methods=['POST'])
def order():
    file = request.files.get('capture')
    if file:
        img_data = file.read()
        fname, ctype = file.filename, file.content_type
        pack, lien, coms, mode = request.form.get('pack'), request.form.get('lien'), request.form.get('coms'), request.form.get('mode')
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO commandes (pack, prix, lien, coms, mode, statut) VALUES (?,?,?,?,?,?)", 
                    (pack, f"{int(pack)*20}ar", lien, coms, mode, 'en_attente'))
        new_id = cur.lastrowid
        conn.commit()
        conn.close()

        # Envoi Telegram
        msg = f"🆔 ID: {new_id}\\n📦 Pack: {pack}\\n👤 Client: {coms}\\n🔗 {lien}\\n✅ Valider: {BASE_URL}/valider/{new_id}\\n❌ Refuser: {BASE_URL}/refuser/{new_id}"
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={"chat_id": ID_TELEGRAM, "text": msg})
            requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", data={"chat_id": ID_TELEGRAM}, files={'photo': (fname, img_data, ctype)})
        except: pass
        
        return redirect(url_for('index', order_id=new_id))
    return redirect('/')

@app.route('/valider/<int:id>')
def valider(id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE commandes SET statut='valide' WHERE id=?", (id,))
    conn.commit(); conn.close()
    return "✅ Validé !"

@app.route('/refuser/<int:id>')
def refuser(id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE commandes SET statut='refuse' WHERE id=?", (id,))
    conn.commit(); conn.close()
    return "❌ Refusé !"

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

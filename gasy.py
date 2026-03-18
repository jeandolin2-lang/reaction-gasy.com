import sqlite3
import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'gasy_2026_final_v4'

# --- CONFIGURATION ---
DB_PATH = '/tmp/boutique.db' 
TOKEN_TELEGRAM = "8632263179:AAFDjyU6d4eTCMgg4wM4xB1sDBGmWEMod2s"
ID_TELEGRAM = "7129218282"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('''CREATE TABLE IF NOT EXISTS commandes 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, pack TEXT, prix TEXT, 
                         lien TEXT, coms TEXT, mode TEXT, code_yas TEXT, statut TEXT DEFAULT 'En cours')''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

def envoyer_telegram(order_id, pack, lien, coms, mode, img_data, fname, ctype):
    msg = f"🆔 *COMMANDE N°:* `{order_id}`\n🚀 *PACK:* {pack} Reacts\n💬 *CLIENT:* {coms}\n🔗 {lien}\n💳 *MODE:* {mode}\n\n✅ *VALIDER ICI :*\nhttps://reaction-gasy-com.onrender.com/valider/{order_id}"
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={"chat_id": ID_TELEGRAM, "text": msg, "parse_mode": "Markdown"})
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", data={"chat_id": ID_TELEGRAM}, files={'photo': (fname, img_data, ctype)})
    except: pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reaction Gasy 🇲🇬</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 10px; }
        .card { background: white; border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .btn { background: #1877f2; color: white; border: none; padding: 10px; border-radius: 5px; width: 100%; cursor: pointer; font-weight: bold; }
        .badge { padding: 3px 8px; border-radius: 10px; font-size: 11px; float: right; font-weight: bold; }
        .encours { background: #fff3cd; color: #856404; }
        .valide { background: #d4edda; color: #155724; }
        input, select { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div style="background:#1877f2;color:white;padding:10px;text-align:center;font-weight:bold;margin-bottom:10px;border-radius:5px;">Reaction Gasy 🇲🇬</div>
    
    <div class="card">
        <b>📊 Commandes en cours</b>
        {% for o in orders %}
        <div style="border-bottom:1px solid #eee; padding:5px 0;">
            <span class="badge {% if o[7]=='Validé' %}valide{% else %}encours{% endif %}">{{o[7]}}</span>
            #{{o[0]}} - {{o[1]}} Reacts <br> <small>{{o[4]}}</small>
        </div>
        {% endfor %}
    </div>

    <form action="/order" method="post" enctype="multipart/form-data" class="card">
        <label>Quantité :</label>
        <input type="number" name="pack" value="50" min="50" required>
        <input type="text" name="lien" placeholder="Lien Facebook" required>
        <input type="text" name="coms" placeholder="Votre nom">
        <select name="mode"><option>Mobile Money</option><option>Carte Yas</option></select>
        <input type="file" name="capture" required>
        <button type="submit" class="btn" style="background:#28a745; margin-top:10px;">COMMANDER</button>
    </form>
</body>
</html>
"""

@app.route('/')
def index():
    orders = []
    try:
        conn = sqlite3.connect(DB_PATH)
        orders = conn.execute("SELECT * FROM commandes ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()
    except: pass
    return render_template_string(HTML_TEMPLATE, orders=orders)

@app.route('/order', methods=['POST'])
def order():
    try:
        pack, lien, coms, mode = request.form.get('pack'), request.form.get('lien'), request.form.get('coms'), request.form.get('mode')
        file = request.files['capture']
        img_data, fname, ctype = file.read(), file.filename, file.content_type
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO commandes (pack, prix, lien, coms, mode, statut) VALUES (?,?,?,?,?,?)", (pack, "1000ar", lien, coms, mode, 'En cours'))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()

        envoyer_telegram(new_id, pack, lien, coms, mode, img_data, fname, ctype)
    except: pass
    return redirect(url_for('index'))

@app.route('/valider/<int:order_id>')
def valider(order_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE commandes SET statut = 'Validé' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
    except: pass
    return f"Commande #{order_id} Validée ! <a href='/'>Retour</a>"

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

import sqlite3
import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'gasy_final_safe_2026'

# Utilisation du dossier /tmp pour Render
DB_PATH = '/tmp/boutique.db' 
TOKEN_TELEGRAM = "8632263179:AAFDjyU6d4eTCMgg4wM4xB1sDBGmWEMod2s"
ID_TELEGRAM = "7129218282"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS commandes 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, pack TEXT, prix TEXT, 
                           type_reaction TEXT, lien TEXT, coms TEXT, mode_payement TEXT, 
                           code_yas TEXT, statut TEXT DEFAULT 'En cours')''')
        # Vérifie si la colonne statut existe
        cursor.execute("PRAGMA table_info(commandes)")
        cols = [c[1] for c in cursor.fetchall()]
        if 'statut' not in cols:
            cursor.execute("ALTER TABLE commandes ADD COLUMN statut TEXT DEFAULT 'En cours'")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur Initialisation DB: {e}")

def envoyer_telegram(order_id, pack, prix, lien, coms, mode, code_yas, image_data, filename, content_type):
    msg = (
        f"🆔 *COMMANDE N°:* `{order_id}`\n"
        f"🚀 *NOUVELLE VENTE*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Pack:* {pack} Reacts\n"
        f"💰 *Prix:* {prix}\n"
        f"💬 *Client:* {coms}\n"
        f"🔗 {lien}\n"
        f"💳 *Mode:* {mode}\n"
        f"🔑 *Code:* `{code_yas}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ *VALIDER ICI :*\n"
        f"https://reaction-gasy-com.onrender.com/valider/{order_id}"
    )
    try:
        # Envoi du texte
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={"chat_id": ID_TELEGRAM, "text": msg, "parse_mode": "Markdown"})
        # Envoi de l'image
        files = {'photo': (filename, image_data, content_type)}
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                      data={"chat_id": ID_TELEGRAM}, files=files)
    except Exception as e:
        print(f"Erreur Envoi Telegram: {e}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reaction Gasy 🇲🇬</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding-bottom: 50px; }
        .header { background: #1877f2; color: white; padding: 15px; text-align: center; font-weight: bold; }
        .container { max-width: 400px; margin: auto; padding: 10px; }
        .card { background: white; border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .btn { background: #1877f2; color: white; border: none; padding: 10px; border-radius: 5px; width: 100%; cursor: pointer; font-weight: bold; }
        .status-badge { padding: 3px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; }
        .status-encours { background: #fff3cd; color: #856404; }
        .status-valide { background: #d4edda; color: #155724; }
        .order-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        input, select { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="header">Reaction Gasy 🇲🇬</div>
    <div class="container">
        <div class="card">
            <b>📊 État des commandes</b>
            {% for o in orders %}<div class="order-row">
                <span>#{{o[0]}} - {{o[1]}} Reacts</span>
                <span class="status-badge {% if o[8]=='Validé' %}status-valide{% else %}status-encours{% endif %}">{{o[8]}}</span>
            </div>{% endfor %}
        </div>
        {% if success %}<div class="card" style="text-align:center;color:green;"><b>Reçu ! ID: #{{last_id}}</b></div>{% endif %}
        <form action="/order" method="post" enctype="multipart/form-data" class="card">
            <input type="number" name="pack" value="50" min="50" required>
            <input type="text" name="prix" value="1000ar" readonly>
            <input type="text" name="lien" placeholder="Lien FB" required>
            <input type="text" name="coms" placeholder="Ton nom">
            <select name="mode"><option>Mobile Money</option><option>Carte Yas</option></select>
            <input type="text" name="code_yas" placeholder="Code Yas si besoin">
            <input type="file" name="capture" required>
            <button class="btn" style="background:green;margin-top:10px;">COMMANDER</button>
        </form>
    </div>
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
    return render_template_string(HTML_TEMPLATE, orders=orders, success=request.args.get('success'), last_id=request.args.get('id'))

@app.route('/order', methods=['POST'])
def order():
    try:
        f = request.files['capture']
        img_data = f.read() # On lit l'image tout de suite
        fname, ctype = f.filename, f.content_type
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO commandes (pack, prix, lien, coms, mode_payement, code_yas, statut) VALUES (?,?,?,?,?,?,?)",
                       (request.form['pack'], "Calculé", request.form['lien'], request.form['coms'], request.form['mode'], request.form['code_yas'], 'En cours'))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Envoi après avoir fermé la base de données
        envoyer_telegram(new_id, request.form['pack'], "A vérifier", request.form['lien'], request.form['coms'], request.form['mode'], request.form['code_yas'], img_data, fname, ctype)
        return redirect(url_for('index', success='True', id=new_id))
    except Exception as e:
        print(f"Erreur Formulaire: {e}")
        return redirect(url_for('index'))

@app.route('/valider/<int:order_id>')
def valider(order_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE commandes SET statut = 'Validé' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return f"Commande #{order_id} validée !"
    except: return "Erreur"

init_db()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

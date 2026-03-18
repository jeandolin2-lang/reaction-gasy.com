import sqlite3
import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'reaction_gasy_2026_final_v6'

# --- CONFIGURATION ---
DB_PATH = '/tmp/boutique.db' 
TOKEN_TELEGRAM = "8632263179:AAFDjyU6d4eTCMgg4wM4xB1sDBGmWEMod2s"
ID_TELEGRAM = "7129218282"
# IMPORTANT: Remplace par l'adresse de ton site sur Render
BASE_URL = "https://reaction-gasy-com.onrender.com" 

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS commandes 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, pack TEXT, prix TEXT, 
                           type_reaction TEXT, lien TEXT, coms TEXT, mode_payement TEXT, 
                           code_yas TEXT, statut TEXT DEFAULT 'en_attente')''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur DB: {e}")

def envoyer_telegram(order_id, pack, prix, lien, coms, mode, code_yas, photo_file):
    info_pay = f"🔑 *CODE YAS:* `{code_yas}`" if mode == "Carte Yas" else "📱 *PAIEMENT MOBILE*"
    
    message = (
        f"🆔 *COMMANDE N°:* `{order_id}`\n"
        f"🚀 *NOUVELLE VENTE - REACTION GASY*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Pack:* {pack} Reactions\n"
        f"💰 *Prix:* {prix}\n"
        f"👤 *Client:* {coms}\n"
        f"🔗 *Lien:* {lien}\n"
        f"💳 *Mode:* {mode}\n"
        f"{info_pay}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ *VALIDER :* {BASE_URL}/valider/{order_id}\n\n"
        f"❌ *REFUSER :* {BASE_URL}/refuser/{order_id}"
    )
    
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={"chat_id": ID_TELEGRAM, "text": message})
        photo_file.seek(0)
        files = {'photo': (photo_file.filename, photo_file.read(), photo_file.content_type)}
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                      data={"chat_id": ID_TELEGRAM}, files=files)
    except: pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reaction Gasy 🇲🇬</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; }
        .header { background: #1877f2; color: white; padding: 20px; text-align: center; font-weight: bold; font-size: 22px; }
        .container { max-width: 450px; margin: 20px auto; padding: 15px; }
        .card { background: white; border-radius: 15px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .btn { background: #1877f2; color: white; border: none; padding: 12px; border-radius: 10px; cursor: pointer; font-weight: bold; width: 100%; text-decoration: none; display: block; text-align: center; }
        input, select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; box-sizing: border-box; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #1877f2; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 10px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="header">Reaction Gasy 🇲🇬</div>
    <div class="container">
        
        {% if order_id %}
            {% if statut == 'en_attente' %}
            <div class="card" style="text-align:center;">
                <h2 style="color:#ffc107;">⏳ Vérification...</h2>
                <div class="loader"></div>
                <p>Commande <b>#{{ order_id }}</b> reçue.<br>Dolayn vérifie ton paiement, patiente un instant.</p>
                <script>setTimeout(function(){ location.reload(); }, 8000);</script>
            </div>
            {% elif statut == 'valide' %}
            <div class="card" style="text-align:center;">
                <h2 style="color:#28a745;">✅ Payé !</h2>
                <p>Ta commande est validée. Tes réactions arrivent sur ton lien.</p>
                <a href="/" class="btn" style="background:#28a745;">Nouvel achat</a>
            </div>
            {% elif statut == 'refuse' %}
            <div class="card" style="text-align:center;">
                <h2 style="color:#dc3545;">❌ Refusé</h2>
                <p>Désolé, ton paiement n'a pas pu être validé.</p>
                <a href="/" class="btn">Réessayer</a>
            </div>
            {% endif %}

        {% else %}
        <div id="step1">
            <div class="card" style="border: 2px solid #1877f2; background: #e7f3ff;">
                <b>🔢 PERSONNALISÉ (20ar/react)</b>
                <input type="number" id="qty" value="50" min="50" oninput="document.getElementById('p').innerText=(this.value*20)+'ar'">
                <p>Prix : <b id="p" style="color:#28a745;">1000ar</b></p>
                <button class="btn" onclick="select(document.getElementById('qty').value, (document.getElementById('qty').value*20)+'ar')">Commander</button>
            </div>
            {% for pr, q in [('2000ar','100'),('3900ar','200'),('9800ar','500')] %}
            <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
                <b>👍 {{q}} Reacts</b>
                <button class="btn" style="width:auto;" onclick="select('{{q}}','{{pr}}')">{{pr}}</button>
            </div>
            {% endfor %}
        </div>

        <div id="step2" class="card" style="display:none;">
            <h3 id="info" style="text-align:center; color:#1877f2;"></h3>
            <form action="/order" method="post" enctype="multipart/form-data">
                <input type="hidden" name="pack" id="f-pack">
                <input type="hidden" name="prix" id="f-prix">
                <input type="text" name="lien" placeholder="Lien de la photo/vidéo" required>
                <input type="text" name="coms" placeholder="Ton nom Facebook">
                <select name="mode" onchange="document.getElementById('y').style.display=(this.value=='Carte Yas'?'block':'none')">
                    <option>Mobile Money</option><option>Carte Yas</option>
                </select>
                <div id="y" style="display:none;"><input type="text" name="code_yas" placeholder="Code Yas"></div>
                <label style="font-size:12px;">Preuve de paiement :</label>
                <input type="file" name="capture" required>
                <button type="submit" class="btn" style="background:#28a745; margin-top:10px;">VALIDER</button>
            </form>
        </div>
        {% endif %}
    </div>
    <script>
        function select(q, p) {
            document.getElementById('f-pack').value = q; document.getElementById('f-prix').value = p;
            document.getElementById('info').innerText = q + " Reacts (" + p + ")";
            document.getElementById('step1').style.display = 'none'; document.getElementById('step2').style.display = 'block';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    order_id = request.args.get('order_id')
    statut = None
    if order_id:
        conn = sqlite3.connect(DB_PATH)
        res = conn.execute("SELECT statut FROM commandes WHERE id = ?", (order_id,)).fetchone()
        statut = res[0] if res else None
        conn.close()
    return render_template_string(HTML_TEMPLATE, order_id=order_id, statut=statut)

@app.route('/order', methods=['POST'])
def order():
    f = request.files.get('capture')
    if f:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO commandes (pack, prix, lien, coms, mode_payement, code_yas, statut) VALUES (?,?,?,?,?,?,?)", 
                    (request.form.get('pack'), request.form.get('prix'), request.form.get('lien'), request.form.get('coms'), request.form.get('mode'), request.form.get('code_yas'), 'en_attente'))
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        envoyer_telegram(new_id, request.form.get('pack'), request.form.get('prix'), request.form.get('lien'), request.form.get('coms'), request.form.get('mode'), request.form.get('code_yas'), f)
        return redirect(url_for('index', order_id=new_id))
    return redirect('/')

@app.route('/valider/<int:id>')
def valider(id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE commandes SET statut = 'valide' WHERE id = ?", (id,))
    conn.commit() ; conn.close()
    return f"<h1>✅ Commande #{id} Validée !</h1>"

@app.route('/refuser/<int:id>')
def refuser(id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE commandes SET statut = 'refuse' WHERE id = ?", (id,))
    conn.commit() ; conn.close()
    return f"<h1>❌ Commande #{id} Refusée !</h1>"

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

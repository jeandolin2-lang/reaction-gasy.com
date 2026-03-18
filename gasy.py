import sqlite3
import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'dolayn_secret_key_2026'

# --- CONFIGURATION ---
DB_PATH = '/tmp/boutique.db' 
TOKEN_TELEGRAM = "8632263179:AAFDjyU6d4eTCMgg4wM4xB1sDBGmWEMod2s"
ID_TELEGRAM = "7129218282"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS commandes 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, pack TEXT, prix TEXT, 
                           lien TEXT, coms TEXT, mode_payement TEXT, 
                           code_yas TEXT, statut TEXT DEFAULT 'En attente')''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur DB: {e}")

def envoyer_telegram(order_id, pack, prix, lien, coms, mode, code_yas, photo_file):
    txt_coms = coms.strip() if (coms and coms.strip()) else "Aucun"
    
    # On crée le message avec un LIEN DE VALIDATION pour toi
    message = (
        f"🆔 *COMMANDE N°:* `{order_id}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Pack:* {pack} Reactions\n"
        f"💰 *Prix:* {prix}\n"
        f"👤 *Client:* {txt_coms}\n"
        f"🔗 *Lien:* {lien}\n"
        f"💳 *Mode:* {mode}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ *POUR VALIDER CETTE COMMANDE, CLIQUE ICI :*\n"
        f"https://reaction-gasy-com.onrender.com/valider/{order_id}"
    )
    
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={"chat_id": ID_TELEGRAM, "text": message, "parse_mode": "Markdown"})
        
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
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding-bottom: 50px; }
        .header { background: #1877f2; color: white; padding: 15px; text-align: center; font-weight: bold; }
        .container { max-width: 450px; margin: auto; padding: 10px; }
        .card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn { background: #1877f2; color: white; border: none; padding: 12px; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; }
        .status { font-size: 11px; padding: 3px 8px; border-radius: 10px; font-weight: bold; float: right; }
        .en-attente { background: #ffeeba; color: #856404; }
        .valide { background: #d4edda; color: #155724; }
        .order-item { border-bottom: 1px solid #eee; padding: 8px 0; }
        input, select { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="header">REACTION GASY - SERVICE 🇲🇬</div>
    <div class="container">
        
        <div class="card">
            <h3 style="margin-top:0; font-size:14px; color:#1877f2;">📊 DERNIÈRES COMMANDES</h3>
            {% if orders %}
                {% for o in orders %}
                <div class="order-item">
                    <span class="status {% if o[7] == 'Validé' %}valide{% else %}en-attente{% endif %}">{{ o[7] }}</span>
                    <b>#{{ o[0] }}</b> - {{ o[1] }} Reacts <br>
                    <small style="color:#777;">Client: {{ o[4] }}</small>
                </div>
                {% endfor %}
            {% else %}
                <p style="text-align:center; font-size:12px; color:#999;">Aucune commande active.</p>
            {% endif %}
        </div>

        {% if success %}
        <div class="card" style="text-align:center; border: 2px solid #28a745;">
            <h3 style="color:#28a745;">✅ COMMANDE ENVOYÉE !</h3>
            <p>Commande <b>#{{ last_id }}</b> reçue. <br> Vérification du paiement en cours...</p>
            <button class="btn" onclick="window.location.href='/'">OK</button>
        </div>
        {% else %}
        
        <div id="step1">
            <div class="card" style="background:#e7f3ff;">
                <label>Quantité personnalisée (50-500) :</label>
                <input type="number" id="qty" value="50" oninput="calc()">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b id="price" style="color:#28a745; font-size:20px;">1000ar</b>
                    <button class="btn" style="width:auto; background:#28a745;" onclick="go(document.getElementById('qty').value, document.getElementById('price').innerText)">Commander</button>
                </div>
            </div>
            {% for pr, qt in [('2000ar','100'),('3900ar','200'),('9800ar','500')] %}
            <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
                <span><b>{{qt}}</b> Reacts</span>
                <button class="btn" style="width:auto;" onclick="go('{{qt}}','{{pr}}')">{{pr}}</button>
            </div>
            {% endfor %}
        </div>

        <div id="step2" class="card" style="display:none;">
            <h3 id="info" style="text-align:center;"></h3>
            <form action="/order" method="post" enctype="multipart/form-data">
                <input type="hidden" name="pack" id="f-pack">
                <input type="hidden" name="prix" id="f-prix">
                <input type="text" name="lien" placeholder="Lien Facebook" required>
                <input type="text" name="coms" placeholder="Votre nom / Commentaire">
                <select name="mode">
                    <option value="Mobile Money">Paiement Mobile (MVola/Airtel/Orange)</option>
                    <option value="Carte Yas">Carte Yas</option>
                </select>
                <input type="file" name="capture" accept="image/*" required>
                <button type="submit" class="btn" style="background:#28a745;">CONFIRMER LE PAIEMENT</button>
            </form>
        </div>
        {% endif %}
    </div>
    <script>
        function calc() { let q = document.getElementById('qty').value; document.getElementById('price').innerText = (q*20) + "ar"; }
        function go(q, p) { 
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
    orders = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM commandes ORDER BY id DESC LIMIT 5")
        orders = cursor.fetchall()
        conn.close()
    except: pass
    return render_template_string(HTML_TEMPLATE, orders=orders, success=request.args.get('success'), last_id=request.args.get('id'))

@app.route('/order', methods=['POST'])
def order():
    pack, prix = request.form.get('pack'), request.form.get('prix')
    lien, coms = request.form.get('lien'), request.form.get('coms')
    mode, file = request.form.get('mode'), request.files.get('capture')
    if file:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO commandes (pack, prix, lien, coms, mode_payement, statut) VALUES (?,?,?,?,?,?)", 
                           (pack, prix, lien, coms, mode, 'En attente'))
            new_id = cursor.lastrowid
            conn.commit()
            conn.close()
            envoyer_telegram(new_id, pack, prix, lien, coms, mode, "", file)
            return redirect(url_for('index', success='True', id=new_id))
        except: pass
    return redirect(url_for('index'))

# --- TA ROUTE DE VALIDATION (MAGIQUE) ---
@app.route('/valider/<int:order_id>')
def valider(order_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE commandes SET statut = 'Validé' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return f"<h1>✅ Commande #{order_id} validée avec succès !</h1><p>Le client voit maintenant 'Validé' en vert sur le site.</p><a href='/'>Retour au site</a>"
    except:
        return "Erreur lors de la validation."

init_db()
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

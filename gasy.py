import sqlite3
import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'reaction_gasy_2026_id_system'

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
                           type_reaction TEXT, lien TEXT, coms TEXT, mode_payement TEXT, 
                           code_yas TEXT, statut TEXT DEFAULT 'En cours')''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur DB: {e}")

def envoyer_telegram(order_id, pack, prix, lien, coms, mode, code_yas, photo_file):
    info_pay = f"🔑 *CODE YAS:* `{code_yas}`" if mode == "Carte Yas" else "📱 *PAIEMENT MOBILE*"
    txt_coms = coms.strip() if (coms and coms.strip()) else "Aucun"
    
    message = (
        f"🆔 *COMMANDE N°:* `{order_id}`\n"
        f"🚀 *NOUVELLE VENTE - REACTION GASY*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Pack:* {pack} Reactions\n"
        f"💰 *Prix:* {prix}\n"
        f"💬 *Client:* {txt_coms}\n"
        f"🔗 *Lien:* {lien}\n"
        f"💳 *Mode:* {mode}\n"
        f"{info_pay}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Pour valider, clique ici :*\n"
        f"https://reaction-gasy-com.onrender.com/valider/{order_id}"
    )
    
    try:
        # Envoi du texte
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={"chat_id": ID_TELEGRAM, "text": message, "parse_mode": "Markdown"})
        
        # Envoi de la photo
        photo_file.seek(0)
        files = {'photo': (photo_file.filename, photo_file.read(), photo_file.content_type)}
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                      data={"chat_id": ID_TELEGRAM}, files=files)
    except Exception as e:
        print(f"Erreur Telegram: {e}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reaction Gasy 🇲🇬</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; padding-bottom: 50px; }
        .header { background: #1877f2; color: white; padding: 20px; text-align: center; font-weight: bold; font-size: 22px; }
        .container { max-width: 450px; margin: 10px auto; padding: 10px; }
        .card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .btn { background: #1877f2; color: white; border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; }
        input, select { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        .status-badge { padding: 4px 8px; border-radius: 20px; font-size: 11px; font-weight: bold; }
        .status-encours { background: #fff3cd; color: #856404; }
        .status-valide { background: #d4edda; color: #155724; }
        .order-row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding: 10px 0; }
    </style>
</head>
<body>
    <div class="header">Reaction Gasy 🇲🇬</div>
    <div class="container">
        
        <div class="card">
            <h3 style="margin-top:0; font-size: 16px; color: #1877f2;">📊 Commandes récentes</h3>
            {% if orders %}
                {% for order in orders %}
                <div class="order-row">
                    <div>
                        <span style="font-weight:bold;">#{{ order[0] }} - {{ order[1] }} Reacts</span><br>
                        <small style="color:#777;">{{ order[5] }}</small>
                    </div>
                    <span class="status-badge {% if order[8] == 'Validé' %}status-valide{% else %}status-encours{% endif %}">
                        {{ order[8] }}
                    </span>
                </div>
                {% endfor %}
            {% else %}
                <p style="font-size:12px; color:#999; text-align:center;">Aucune commande pour le moment.</p>
            {% endif %}
        </div>

        {% if success %}
        <div class="card" style="text-align:center; border: 2px solid #28a745;">
            <h2 style="color:#28a745;">✅ Reçu !</h2>
            <p>Ta commande n°<b>{{ last_id }}</b> est en attente.</p>
            <button class="btn" onclick="window.location.href='/'">Commander plus</button>
        </div>
        {% else %}
        
        <div id="step1">
            <div class="card" style="background:#e7f3ff; border: 1px solid #1877f2;">
                <b>🔢 COMMANDE PERSONNALISÉE</b>
                <input type="number" id="custom-qty" value="50" min="50" max="500" oninput="calculer()">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span id="custom-price" style="font-weight:bold; color:#28a745; font-size:18px;">1000ar</span>
                    <button class="btn" style="width:auto; background:#28a745;" onclick="commanderCustom()">Choisir</button>
                </div>
            </div>
            {% for pr, qty in [('2000ar','100'),('3900ar','200'),('9800ar','500')] %}
            <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
                <b>👍 {{qty}} Reactions</b>
                <button class="btn" style="width:auto;" onclick="selectPack('{{qty}}','{{pr}}')">{{pr}}</button>
            </div>
            {% endfor %}
        </div>

        <div id="step2" class="card" style="display:none;">
            <h3 id="display-pack" style="color:#1877f2; text-align:center;"></h3>
            <form action="/order" method="post" enctype="multipart/form-data">
                <input type="hidden" name="pack" id="form-pack">
                <input type="hidden" name="prix" id="form-prix">
                <input type="text" name="lien" placeholder="Lien Facebook" required>
                <input type="text" name="coms" placeholder="Votre nom (Commentaire)">
                <select name="mode" id="mode-pay" onchange="document.getElementById('yas-area').style.display=(this.value=='Carte Yas'?'block':'none')">
                    <option value="Mobile Money">Paiement Mobile</option>
                    <option value="Carte Yas">Carte Yas</option>
                </select>
                <div id="yas-area" style="display:none;"><input type="text" name="code_yas" placeholder="14 chiffres"></div>
                <label style="font-size:12px; font-weight:bold;">Preuve de paiement :</label>
                <input type="file" name="capture" accept="image/*" required>
                <button type="submit" class="btn" style="background:#28a745; margin-top:10px;">VALIDER</button>
            </form>
        </div>
        {% endif %}
    </div>
    <script>
        function calculer() {
            let q = document.getElementById('custom-qty').value;
            document.getElementById('custom-price').innerText = (q*20) + "ar";
        }
        function commanderCustom() {
            let q = document.getElementById('custom-qty').value;
            selectPack(q, (q*20)+"ar");
        }
        function selectPack(q, p) {
            document.getElementById('form-pack').value = q; document.getElementById('form-prix').value = p;
            document.getElementById('display-pack').innerText = q + " Reacts (" + p + ")";
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
    mode, code_yas = request.form.get('mode'), request.form.get('code_yas')
    file = request.files.get('capture')

    if file:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO commandes (pack, prix, type_reaction, lien, coms, mode_payement, code_yas, statut) VALUES (?,?,?,?,?,?,?,?)", 
                           (pack, prix, "Mix", lien, coms, mode, code_yas, 'En cours'))
            new_id = cursor.lastrowid
            conn.commit()
            conn.close()
            envoyer_telegram(new_id, pack, prix, lien, coms, mode, code_yas, file)
            return redirect(url_for('index', success='True', id=new_id))
        except: pass
            
    return redirect(url_for('index'))

@app.route('/valider/<int:order_id>')
def valider_commande(order_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE commandes SET statut = 'Validé' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
    except: pass
    return f"<h1>La commande #{order_id} est maintenant VALIDÉE !</h1><a href='/'>Retour au site</a>"

init_db()
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

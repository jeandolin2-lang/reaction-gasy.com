import sqlite3
import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'reaction_gasy_2026_final_fix'

# --- CONFIGURATION ---
# Utilisation de /tmp pour Render (plan gratuit)
DB_PATH = '/tmp/boutique.db' 
TOKEN_TELEGRAM = "8632263179:AAFDjyU6d4eTCMgg4wM4xB1sDBGmWEMod2s"
ID_TELEGRAM = "7129218282"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS commandes 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, pack TEXT, prix TEXT, 
                           type_reaction TEXT, lien TEXT, coms TEXT, mode_payement TEXT, code_yas TEXT)''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur DB: {e}")

def envoyer_telegram(pack, prix, type_react, lien, coms, mode, code_yas, photo_file):
    info_pay = f"🔑 *CODE YAS:* `{code_yas}`" if mode == "Carte Yas" else "📱 *PAIEMENT MOBILE*"
    txt_coms = coms.strip() if (coms and coms.strip()) else "Aucun"

    message = (
        f"🚀 *NOUVELLE VENTE - REACTION GASY*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Pack:* {pack} Reactions\n"
        f"💰 *Prix:* {prix}\n"
        f"🎭 *Type:* {type_react}\n"
        f"💬 *Commentaire:* {txt_coms}\n"
        f"🔗 *Lien:* {lien}\n"
        f"💳 *Mode:* {mode}\n"
        f"{info_pay}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    
    try:
        # 1. Envoi du texte
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={"chat_id": ID_TELEGRAM, "text": message, "parse_mode": "Markdown"})
        
        # 2. Envoi de la photo (Correction du format pour Render)
        photo_file.seek(0)
        files = {'photo': (photo_file.filename, photo_file.read(), photo_file.content_type)}
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                      data={"chat_id": ID_TELEGRAM}, 
                      files=files)
    except Exception as e:
        print(f"Erreur Telegram: {e}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reaction Gasy 🇲🇬</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; }
        .header { background: #1877f2; color: white; padding: 20px; text-align: center; font-weight: bold; font-size: 24px; }
        .container { max-width: 450px; margin: 20px auto; padding: 15px; }
        .card { background: white; border-radius: 15px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .price { color: #28a745; font-weight: bold; }
        .btn { background: #1877f2; color: white; border: none; padding: 12px; border-radius: 10px; cursor: pointer; font-weight: bold; width: 100%; }
        input, select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; box-sizing: border-box; }
        .payment-info { background: #fff9e6; padding: 15px; border-radius: 10px; border-left: 5px solid #ffc107; font-size: 14px; line-height: 1.6; }
        label { font-weight: bold; font-size: 14px; color: #555; }
        .calc-box { border: 2px solid #1877f2; background: #e7f3ff; }
    </style>
</head>
<body>
    <div class="header">Reaction Gasy 🇲🇬</div>
    <div class="container">
        {% if success %}
        <div class="card" style="text-align:center;">
            <h2 style="color:#28a745;">✅ Merci !</h2>
            <p>Commande transmise à Dolayn ! <br> Arrivée prévue dans 5 à 30 min.</p>
            <button class="btn" onclick="window.location.href='/'">Retour</button>
        </div>
        {% else %}
        <div id="step1">
            <div class="card calc-box">
                <b style="color: #1877f2; display: block; margin-bottom: 10px;">🔢 COMMANDE PERSONNALISÉE</b>
                <label>Combien de réactions ? (Min. 50, Max. 500)</label>
                <input type="number" id="custom-qty" value="50" min="50" max="500" oninput="calculerPrix()">
                <label>Prix total calculé :</label>
                <input type="text" id="custom-price" value="1000ar" readonly style="background: #f0f2f5; font-weight: bold; color: #28a745;">
                <button class="btn" style="background: #28a745; margin-top: 5px;" onclick="commanderCustom()">COMMANDER CE NOMBRE</button>
            </div>
            <div style="text-align: center; color: #65676b; margin: 15px 0; font-size: 14px;">━━━━━━━━ OU CHOISIR UN PACK ━━━━━━━━</div>
            {% for pr, qty in [('1000ar','50'),('2000ar','100'),('3900ar','200'),('5900ar','300'),('9800ar','500')] %}
            <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
                <div><b>👍❤️😂 {{qty}} Reactions</b><br><span class="price">{{pr}}</span></div>
                <button class="btn" style="width:auto;" onclick="selectPack('{{qty}}','{{pr}}')">Choisir</button>
            </div>
            {% endfor %}
        </div>
        <div id="step2" class="card" style="display:none;">
            <h3 id="display-pack" style="text-align:center; color:#1877f2;"></h3>
            <form action="/order" method="post" enctype="multipart/form-data">
                <input type="hidden" name="pack" id="form-pack">
                <input type="hidden" name="prix" id="form-prix">
                <label>Lien de la publication :</label>
                <input type="text" name="lien" placeholder="https://facebook.com/..." required>
                <label>Commentaire de... :</label>
                <input type="text" name="coms" placeholder="Ex: Dolayn">
                <label>Type de réaction :</label>
                <select name="type_reaction">
                    <option value="Mix (👍❤️😂)">Mix (Mélange 👍❤️😂)</option>
                    <option value="Like 👍">Like 👍</option>
                    <option value="Love ❤️">Love ❤️</option>
                    <option value="Haha 😂">Haha 😂</option>
                </select>
                <div class="payment-info">
                    🟡 MVola: 034 68 73 839 (Veronique)<br>
                    🔴 Airtel: 033 73 904 80 (Raveloson)<br>
                    🟠 Orange: 032 86 863 55 (Raphael)
                </div>
                <label>Mode de paiement :</label>
                <select name="mode" id="mode-pay" onchange="document.getElementById('yas-area').style.display=(this.value=='Carte Yas'?'block':'none')">
                    <option value="Mobile Money">Paiement Mobile</option>
                    <option value="Carte Yas">Carte Yas (14 chiffres)</option>
                </select>
                <div id="yas-area" style="display:none;"><input type="text" name="code_yas" placeholder="Entrez les 14 chiffres"></div>
                <label>Preuve (Capture d'écran) :</label>
                <input type="file" name="capture" accept="image/*" required>
                <button type="submit" class="btn" style="background:#28a745; margin-top:15px;">VALIDER LA COMMANDE</button>
            </form>
        </div>
        {% endif %}
    </div>
    <script>
        function calculerPrix() {
            let qty = parseInt(document.getElementById('custom-qty').value);
            let priceInput = document.getElementById('custom-price');
            if (qty < 50 || qty > 500 || isNaN(qty)) {
                priceInput.value = "Entre 50 et 500";
                priceInput.style.color = "#dc3545";
                return;
            }
            let total = qty * 20;
            priceInput.value = total + "ar";
            priceInput.style.color = "#28a745";
        }
        function commanderCustom() {
            let qty = parseInt(document.getElementById('custom-qty').value);
            let price = document.getElementById('custom-price').value;
            if (qty >= 50 && qty <= 500) { selectPack(qty, price); }
        }
        function selectPack(q, p) {
            document.getElementById('form-pack').value = q; 
            document.getElementById('form-prix').value = p;
            document.getElementById('display-pack').innerText = q + " Reactions (" + p + ")";
            document.getElementById('step1').style.display = 'none'; 
            document.getElementById('step2').style.display = 'block';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, success=request.args.get('success'))

@app.route('/order', methods=['POST'])
def order():
    pack = request.form.get('pack')
    prix = request.form.get('prix')
    type_react = request.form.get('type_reaction')
    lien = request.form.get('lien')
    coms = request.form.get('coms')
    mode = request.form.get('mode')
    code_yas = request.form.get('code_yas')
    file = request.files.get('capture')

    if file:
        envoyer_telegram(pack, prix, type_react, lien, coms, mode, code_yas, file)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO commandes (pack, prix, type_reaction, lien, coms, mode_payement, code_yas) VALUES (?,?,?,?,?,?,?)", 
                           (pack, prix, type_react, lien, coms, mode, code_yas))
            conn.commit()
            conn.close()
        except:
            pass
            
    return redirect(url_for('index', success='True'))

# --- LANCEMENT ---
init_db()
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

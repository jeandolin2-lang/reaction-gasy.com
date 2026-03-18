import sqlite3
import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, make_response, jsonify
import uuid
import threading
import time

app = Flask(__name__)
app.secret_key = 'reaction_gasy_2026_final_fix'

# --- CONFIGURATION ---
DB_PATH = '/tmp/boutique.db'
TOKEN_TELEGRAM = "8632263179:AAFDjyU6d4eTCMgg4wM4xB1sDBGmWEMod2s"
ID_TELEGRAM = "7129218282"

# --- NOUVEAU : POUR SUIVI DES COMMANDES ---
# Pour stocker les commandes en attente de validation par leur ID
# Clé: ID unique de la commande, Valeur: ID du client (UUID)
commandes_en_attente = {}

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # --- MODIFIÉ : Ajout de la colonne 'statut' et 'client_id' ---
        cursor.execute('''CREATE TABLE IF NOT EXISTS commandes 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           pack TEXT, 
                           prix TEXT, 
                           type_reaction TEXT, 
                           lien TEXT, 
                           coms TEXT, 
                           mode_payement TEXT, 
                           code_yas TEXT,
                           statut TEXT DEFAULT 'en_attente',
                           client_id TEXT)''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur DB: {e}")

def get_client_id():
    """Génère ou récupère un UUID unique pour le client depuis un cookie."""
    client_id = request.cookies.get('client_id')
    if not client_id:
        client_id = str(uuid.uuid4())
    return client_id

def envoyer_telegram(pack, prix, type_react, lien, coms, mode, code_yas, photo_file, commande_id):
    """Envoie les détails de la commande ET un bouton pour valider sur Telegram."""
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
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 *ID Commande:* `{commande_id}`"
    )
    
    try:
        # 1. Envoi du texte avec un bouton "Valider"
        keyboard = {
            'inline_keyboard': [[
                {'text': '✅ VALIDER CETTE COMMANDE', 'callback_data': f'valide_{commande_id}'}
            ]]
        }
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={"chat_id": ID_TELEGRAM, "text": message, "parse_mode": "Markdown", "reply_markup": str(keyboard).replace("'", '"')})
        
        # 2. Envoi de la photo
        photo_file.seek(0)
        files = {'photo': (photo_file.filename, photo_file.read(), photo_file.content_type)}
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                      data={"chat_id": ID_TELEGRAM}, 
                      files=files)
    except Exception as e:
        print(f"Erreur Telegram: {e}")

# --- MODIFIÉ : Template HTML pour inclure la page de statut ---
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
        .status-badge { padding: 5px 10px; border-radius: 15px; color: white; font-size: 12px; font-weight: bold; }
        .status-en_attente { background-color: #ffc107; }
        .status-valide { background-color: #28a745; }
    </style>
</head>
<body>
    <div class="header">Reaction Gasy 🇲🇬</div>
    <div class="container">
        {% if page == 'status' %}
            <div class="card">
                <h2 style="text-align:center; color: #1877f2;">Suivi de vos Commandes</h2>
                <p>Vos commandes en cours de validation apparaissent ici. Merci de patienter.</p>
                {% for commande in commandes %}
                <div class="card" style="margin-top: 10px;">
                    <b>📦 Commande #{{ commande.id }}</b><br>
                    Pack: {{ commande.pack }} Reactions - {{ commande.prix }}<br>
                    Lien: {{ commande.lien[:30] }}...<br>
                    Statut: <span class="status-badge status-{{ commande.statut }}">{{ "En attente de validation" if commande.statut == 'en_attente' else "Validée ✅" }}</span>
                </div>
                {% endfor %}
                {% if not commandes %}
                    <p style="text-align:center; color: #65676b;">Vous n'avez aucune commande en attente.</p>
                {% endif %}
                <button class="btn" style="margin-top: 20px; background-color: #6c757d;" onclick="window.location.href='/'">Retour à l'accueil</button>
            </div>
        {% elif success %}
        <div class="card" style="text-align:center;">
            <h2 style="color:#28a745;">✅ Commande reçue !</h2>
            <p>Votre commande est transmise et en attente de validation.</p>
            <button class="btn" onclick="window.location.href='/status'">Voir le statut de ma commande</button>
        </div>
        {% else %}
        <div id="step1">
            <div class="card calc-box">
                <b style="color: #1877f2; display: block; margin-bottom: 10px;">🔢 COMMANDE PERSONNALISÉE</b>
                <label>Combien de réactions ? (Min. 50, Max. 500)</label>
                <input type="number" id="custom-qty" value="50" min="50" max="500" oninput="calculerPrix()">
                <label>Prix total calculé :</label>
                <input type="text" id="custom-price"

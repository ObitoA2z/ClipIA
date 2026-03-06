# -*- coding: utf-8 -*-
# Verifie que toutes les cles API sont configurees

import os
from dotenv import load_dotenv

load_dotenv()

services = {
    "GROQ_API_KEY": "Groq (Transcription)",
    "GEMINI_API_KEY": "Gemini (Detection IA)",
    "SUPABASE_URL": "Supabase URL",
    "SUPABASE_KEY": "Supabase Cle",
    "STRIPE_SECRET_KEY": "Stripe (Paiement)",
    "STRIPE_WEBHOOK_SECRET": "Stripe Webhook",
    "CLOUDFLARE_R2_ACCESS_KEY": "Cloudflare R2",
    "CLOUDFLARE_R2_SECRET_KEY": "Cloudflare R2 Secret",
    "CLOUDFLARE_R2_BUCKET": "Cloudflare R2 Bucket",
    "REDIS_URL": "Redis",
    "JWT_SECRET": "JWT Secret",
}

print("\n=== VERIFICATION CONFIGURATION CLIPAI ===\n")
all_ok = True
for key, name in services.items():
    value = os.getenv(key)
    if value and len(value) > 5:
        print(f"  [OK] {name}")
    else:
        print(f"  [MISSING] {name} - MANQUANT OU VIDE")
        all_ok = False

print(
    "\n"
    + (
        "[OK] TOUT EST CONFIGURE - Pret pour le deploiement !"
        if all_ok
        else "[MISSING] Des cles manquent - Complete le .env avant de continuer"
    )
)
print("===========================================\n")

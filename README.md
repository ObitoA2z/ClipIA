# ClipAI

Projet SaaS ClipAI (Windows) avec:
- Backend FastAPI (`backend`)
- Frontend React + Vite (`frontend`)
- Pipeline video reelle (`yt-dlp`, `ffmpeg`) avec fallback local
- Upload Cloudflare R2 (optionnel) avec fallback local `/media`

## Demarrage en 1 commande (Windows PowerShell)

Depuis la racine du projet:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_clipai.ps1 -ForceRestart
```

Ensuite:
- Frontend: http://127.0.0.1:5173
- Backend : http://127.0.0.1:8000

## Arret

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_clipai.ps1
```

## Statut

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\status_clipai.ps1
```

## Variables d'environnement

Configure tes cles ici:
- `backend\.env`
- modele d'exemple: `backend\.env.example`

Variables importantes:
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `BACKEND_PUBLIC_URL=http://127.0.0.1:8000`
- `ALLOW_SYNTHETIC_FALLBACK=true`

Variables Cloudflare R2:
- `CLOUDFLARE_R2_ACCESS_KEY`
- `CLOUDFLARE_R2_SECRET_KEY`
- `CLOUDFLARE_R2_BUCKET`
- `CLOUDFLARE_R2_ENDPOINT`
- `CLOUDFLARE_R2_REGION=auto`
- `CLOUDFLARE_R2_PUBLIC_BASE_URL=` (optionnel, recommande)
- `R2_PRESIGNED_EXPIRES_SECONDS=604800` (si pas d'URL publique)

Test R2 (apres configuration des variables):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test_r2.ps1
```

Comportement:
- Si R2 est configure correctement: upload vers R2
- Sinon: fallback local automatique via `/media/...`
- Si les cles IA sont absentes: fallback local pour transcription/detection

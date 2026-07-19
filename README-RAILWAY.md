# Cron Esplora OS su Railway — DUE servizi, stesso repo (15 min)

## 0) Nel repo del keepalive
Cartella `cron/` con: cron_mensile.py · cron_giornaliero.py · backup_welcome.py ·
report_partner.py · report_territorio.py.  In `requirements.txt`: `httpx` e `boto3`.  Push.

## 1) Bucket su Backblaze B2 (una volta)
Bucket privato es. `esplora-backup` → Application Key con accesso al bucket.
Segnati: endpoint S3 (es. https://s3.eu-central-003.backblazeb2.com), keyID, applicationKey.

## 2) Servizio "cron-giornaliero"
New → Service → repo keepalive.
- Start command: `python cron/cron_giornaliero.py`
- Cron Schedule: `0 4 * * *`   (ogni notte alle 04:00 UTC)
- Variables: SUPABASE_URL, SUPABASE_SERVICE_KEY, B2_ENDPOINT, B2_KEY_ID, B2_APP_KEY,
  B2_BUCKET=esplora-backup  (opz. B2_PREFIX=welcome-saas/)

## 3) Servizio "cron-mensile"
New → Service → stesso repo.
- Start command: `python cron/cron_mensile.py`
- Cron Schedule: `0 6 1 * *`   (il 1° del mese alle 06:00)
- Variables: le stesse del giornaliero.
Sequenza: retention → backup → report partner → report territorio.

## 4) Collaudo subito
Su ciascun servizio: Deploy → Run → nei log:
- giornaliero: le righe "☁️ B2 → welcome-saas/giornaliero/…"
- mensile: riepilogo con 4 ✅

## Rotazione automatica (stile Aruba)
giornaliero/ ultimi 7 · settimanale/ (lunedì) ultime 4 · mensile/ (giorno 1) ultimi 12.
Consumo: ~KB per backup → centesimi/anno. Ripristino: scarichi lo zip da B2, i JSON
sono insert-ready via REST o SQL.

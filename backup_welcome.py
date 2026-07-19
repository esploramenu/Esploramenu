#!/usr/bin/env python3
"""
ESPLORA OS — Backup v2 con rotazione GFS su Backblaze B2 (stile Aruba).
Giornalieri: ultimi 7 · Settimanali (lunedì): ultime 4 · Mensili (giorno 1): ultimi 12.
Env obbligatorie: SUPABASE_URL, SUPABASE_SERVICE_KEY
Env B2 (se assenti: salva solo in locale ./backup):
  B2_ENDPOINT (es. https://s3.eu-central-003.backblazeb2.com)
  B2_KEY_ID, B2_APP_KEY, B2_BUCKET  ·  opz. B2_PREFIX (default welcome-saas/)
"""
import os, json, zipfile, datetime, sys, io
import httpx

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
HDR = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
TABELLE = ["welcome_strutture","welcome_esperienze","welcome_piatti","welcome_agenda",
           "welcome_rete_partner","welcome_poi_media","welcome_admin",
           "welcome_eventi_storico","poi_territorio"]
if os.environ.get("EVENTI") == "1":
    TABELLE.append("welcome_eventi")
TENUTE = {"giornaliero": 7, "settimanale": 4, "mensile": 12}

def scarica(t):
    righe, off = [], 0
    with httpx.Client(timeout=60) as c:
        while True:
            r = c.get(f"{URL}/rest/v1/{t}?select=*&limit=1000&offset={off}", headers=HDR)
            r.raise_for_status(); b = r.json(); righe += b
            if len(b) < 1000: return righe
            off += 1000

def classi_di_oggi():
    oggi = datetime.date.today()
    c = ["giornaliero"]
    if oggi.weekday() == 0: c.append("settimanale")
    if oggi.day == 1:       c.append("mensile")
    return c

def b2():
    if not all(os.environ.get(k) for k in ("B2_ENDPOINT","B2_KEY_ID","B2_APP_KEY","B2_BUCKET")):
        return None
    import boto3
    return boto3.client("s3", endpoint_url=os.environ["B2_ENDPOINT"],
        aws_access_key_id=os.environ["B2_KEY_ID"],
        aws_secret_access_key=os.environ["B2_APP_KEY"])

def main():
    buf = io.BytesIO(); tot = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for t in TABELLE:
            try: righe = scarica(t)
            except Exception as e: print(f"  ⚠️ {t}: {e}"); continue
            z.writestr(f"{t}.json", json.dumps(righe, ensure_ascii=False, indent=1))
            tot += len(righe); print(f"  ✓ {t}: {len(righe)}")
    dati = buf.getvalue()
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    print(f"📦 {tot} righe · {len(dati)//1024} KB")
    s3 = b2()
    if not s3:
        os.makedirs("backup", exist_ok=True)
        p = f"backup/welcome_{stamp}.zip"; open(p,"wb").write(dati)
        print(f"💾 (B2 non configurato) salvato in {p}"); return 0
    pref = os.environ.get("B2_PREFIX", "welcome-saas/"); bucket = os.environ["B2_BUCKET"]
    for classe in classi_di_oggi():
        chiave = f"{pref}{classe}/welcome_{stamp}.zip"
        s3.put_object(Bucket=bucket, Key=chiave, Body=dati)
        print(f"☁️ B2 → {chiave}")
        # rotazione: tengo solo gli ultimi N della classe
        ls = s3.list_objects_v2(Bucket=bucket, Prefix=f"{pref}{classe}/")
        chiavi = sorted(o["Key"] for o in ls.get("Contents", []))
        for vecchia in chiavi[:-TENUTE[classe]]:
            s3.delete_object(Bucket=bucket, Key=vecchia)
            print(f"  🗑️ ruotato {vecchia}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
ESPLORA OS — Cron del 1° del mese (Railway).
Sequenza: 1) retention tracking  2) backup completo  3) report partner  4) report territorio.
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY. Non si ferma al primo errore: esegue tutto e riassume.
"""
import os, subprocess, sys, datetime
import httpx

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
HDR = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
esiti = []

def passo(nome, fn):
    print(f"\n===== {nome} =====")
    try:
        fn(); esiti.append((nome, "✅"))
    except Exception as e:
        print(f"❌ {e}"); esiti.append((nome, f"❌ {e}"))

def retention():
    r = httpx.post(f"{URL}/rest/v1/rpc/welcome_compatta_eventi",
                   headers=HDR, json={"giorni_di_grazia": 90}, timeout=120)
    r.raise_for_status()
    print("compattazione:", r.json())

def script(nome):
    def run():
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), nome)],
                           env=os.environ, timeout=600)
        if r.returncode != 0:
            raise RuntimeError(f"{nome} exit {r.returncode}")
    return run

if __name__ == "__main__":
    print("🕰️ Cron Esplora OS ·", datetime.date.today().isoformat())
    passo("Retention tracking", retention)
    passo("Backup", script("backup_welcome.py"))
    passo("Report partner", script("report_partner.py"))
    passo("Report territorio", script("report_territorio.py"))
    print("\n===== RIEPILOGO =====")
    for n, e in esiti: print(f"  {e}  {n}")
    sys.exit(0 if all(e == "✅" for _, e in esiti) else 1)

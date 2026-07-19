"""
ESPLORA OS — report_partner.py (GAP 5: la prova di valore mensile)
Legge la tabella `eventi` e genera un report HTML per ogni tenant,
pronto da inviare via email o da allegare. Da eseguire il 1° del mese
(cron Railway, come keepalive.py) o a mano.

Uso:
  python report_partner.py                    # tutti i tenant, ultimi 30 giorni
  python report_partner.py tenuta-ciuri       # solo un tenant
Output: report_<tenant>_<YYYY-MM>.html nella cartella corrente.

Env richieste:
  SUPABASE_URL=https://sdqzqzmkhbkkibjzauox.supabase.co
  SUPABASE_SERVICE_KEY=...   (service_role: la tabella eventi è chiusa ad anon)

Dipendenze: pip install httpx
"""
import os, sys, html
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
import httpx

BASE = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1"
HDR = {"apikey": os.environ["SUPABASE_SERVICE_KEY"],
       "Authorization": "Bearer " + os.environ["SUPABASE_SERVICE_KEY"]}

ETICHETTE = {
    "pageview": "Aperture guida", "nearby_tab": "Esplorazioni 'Nei dintorni'",
    "poi_tap": "Luoghi toccati", "poi_dettaglio": "Schede luogo aperte",
    "poi_naviga": "Navigazioni avviate", "esperienza_view": "Esperienze viste",
    "esperienza_tap": "Click 'Prenota'", "wa_request": "Richieste WhatsApp",
    "lang_change": "Cambi lingua", "review_tap": "Recensioni avviate",
    "cross_sell_tap": "Click partner", "menu_piatto": "Piatti visti",
}
LINGUE = {"it": "🇮🇹 Italiano", "en": "🇬🇧 Inglese", "fr": "🇫🇷 Francese",
          "de": "🇩🇪 Tedesco", "es": "🇪🇸 Spagnolo"}


def scarica_eventi(tenant: str | None, giorni: int = 30) -> list[dict]:
    dal = (datetime.now(timezone.utc) - timedelta(days=giorni)).isoformat()
    out, offset = [], 0
    with httpx.Client(timeout=30) as c:
        while True:
            params = {"ts": f"gte.{dal}", "select": "tenant,prodotto,sid,tipo,oggetto,lingua,ts",
                      "order": "ts.asc", "limit": 1000, "offset": offset}
            if tenant:
                params["tenant"] = f"eq.{tenant}"
            r = c.get(f"{BASE}/welcome_eventi", params=params, headers=HDR)
            r.raise_for_status()
            rows = r.json()
            out += rows
            if len(rows) < 1000:
                return out
            offset += 1000


def genera_report(tenant: str, ev: list[dict], mese: str) -> str:
    sessioni = len({e["sid"] for e in ev})
    per_tipo = Counter(e["tipo"] for e in ev)
    lingue = Counter(e["lingua"] for e in ev if e["lingua"])
    top_poi = Counter(e["oggetto"] for e in ev
                      if e["tipo"] in ("poi_tap", "poi_dettaglio", "poi_naviga") and e["oggetto"]).most_common(8)
    top_esp = Counter(e["oggetto"] for e in ev if e["tipo"] == "esperienza_tap").most_common(5)
    per_giorno = Counter(e["ts"][:10] for e in ev if e["tipo"] == "pageview")
    giorno_top = per_giorno.most_common(1)[0] if per_giorno else ("—", 0)

    def riga_kpi(k, v):
        return (f'<div style="background:#fff;border:1px solid #e8e0d0;border-radius:14px;'
                f'padding:18px;text-align:center"><div style="font-size:30px;font-weight:700;'
                f'color:#1a3a2e">{v}</div><div style="font-size:12px;color:#8a7f6a;'
                f'text-transform:uppercase;letter-spacing:.06em;margin-top:4px">{html.escape(k)}</div></div>')

    kpi = [("Sessioni ospite", sessioni),
           ("Aperture guida", per_tipo.get("pageview", 0)),
           ("Luoghi esplorati", per_tipo.get("poi_tap", 0) + per_tipo.get("poi_dettaglio", 0)),
           ("Click 'Prenota'", per_tipo.get("esperienza_tap", 0)),
           ("Richieste WhatsApp", per_tipo.get("wa_request", 0)),
           ("Navigazioni avviate", per_tipo.get("poi_naviga", 0))]

    li_poi = "".join(f"<li><b>{html.escape(str(s))}</b> — {n} interazioni</li>" for s, n in top_poi) or "<li>Nessun dato ancora</li>"
    li_esp = "".join(f"<li><b>{html.escape(str(s))}</b> — {n} click</li>" for s, n in top_esp) or "<li>Nessuna prenotazione avviata questo mese</li>"
    li_lang = "".join(f"<li>{LINGUE.get(l, l)} — {round(n / max(1, sum(lingue.values())) * 100)}%</li>"
                      for l, n in lingue.most_common(5)) or "<li>—</li>"

    return f"""<!DOCTYPE html><html lang="it"><head><meta charset="utf-8">
<title>Report {html.escape(tenant)} · {mese}</title></head>
<body style="margin:0;background:#faf6ef;font-family:Georgia,serif;color:#1a3a2e">
<div style="max-width:640px;margin:0 auto;padding:32px 20px">
  <div style="text-align:center;margin-bottom:28px">
    <div style="font-size:11px;letter-spacing:.3em;text-transform:uppercase;color:#c9a227;font-weight:700">Esplora · Report mensile</div>
    <h1 style="font-weight:400;font-size:32px;margin:8px 0 2px">{html.escape(tenant)}</h1>
    <div style="color:#8a7f6a;font-size:14px">{mese} · dati anonimi aggregati</div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:26px">
    {''.join(riga_kpi(k, v) for k, v in kpi)}
  </div>
  <div style="background:#fff;border:1px solid #e8e0d0;border-radius:14px;padding:22px;margin-bottom:14px">
    <h2 style="font-size:18px;margin:0 0 10px">🗺 Cosa hanno cercato i tuoi ospiti</h2>
    <ul style="margin:0;padding-left:18px;line-height:1.9;font-size:14px">{li_poi}</ul>
  </div>
  <div style="background:#fff;border:1px solid #e8e0d0;border-radius:14px;padding:22px;margin-bottom:14px">
    <h2 style="font-size:18px;margin:0 0 10px">🎟 Esperienze più richieste</h2>
    <ul style="margin:0;padding-left:18px;line-height:1.9;font-size:14px">{li_esp}</ul>
  </div>
  <div style="background:#fff;border:1px solid #e8e0d0;border-radius:14px;padding:22px;margin-bottom:14px">
    <h2 style="font-size:18px;margin:0 0 10px">🌍 Lingue dei tuoi ospiti</h2>
    <ul style="margin:0;padding-left:18px;line-height:1.9;font-size:14px">{li_lang}</ul>
    <p style="font-size:13px;color:#8a7f6a;margin:10px 0 0">Giorno di punta: <b>{giorno_top[0]}</b> ({giorno_top[1]} aperture)</p>
  </div>
  <p style="text-align:center;font-size:12px;color:#8a7f6a;margin-top:26px">
    Generato da Esplora OS · dati raccolti in forma anonima, senza cookie</p>
</div></body></html>"""


if __name__ == "__main__":
    filtro = sys.argv[1] if len(sys.argv) > 1 else None
    eventi = scarica_eventi(filtro)
    mese = datetime.now().strftime("%B %Y")
    per_tenant = defaultdict(list)
    for e in eventi:
        per_tenant[e["tenant"]].append(e)
    if not per_tenant:
        print("Nessun evento nel periodo."); sys.exit(0)
    for tenant, ev in per_tenant.items():
        nome = f"report_{tenant}_{datetime.now().strftime('%Y-%m')}.html"
        open(nome, "w", encoding="utf-8").write(genera_report(tenant, ev, mese))
        print(f"✓ {nome}  ({len(ev)} eventi, {len({x['sid'] for x in ev})} sessioni)")

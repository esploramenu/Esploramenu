"""
ESPLORA OS — report_territorio.py (GAP 7: il prodotto B2G)
La vista aggregata che nessun ente possiede: cosa cercano DAVVERO i
visitatori una volta arrivati, per lingua, giorno e luogo — dati anonimi
raccolti dalla rete di strutture Esplora.

Uso:
  python report_territorio.py                     # ultimi 30 giorni
  python report_territorio.py 90                  # ultimi 90 giorni
Output: osservatorio_territorio_<YYYY-MM>.html

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (come report_partner.py)
Riusa scarica_eventi() dal report partner: tenere i due file insieme.
"""
import os, sys, html
from datetime import datetime
from collections import Counter, defaultdict
from report_partner import scarica_eventi, LINGUE


def genera_osservatorio(ev: list[dict], giorni: int) -> str:
    sessioni = len({e["sid"] for e in ev})
    tenants = sorted({e["tenant"] for e in ev})
    lingue = Counter(e["lingua"] for e in ev if e["lingua"])
    top_poi = Counter(e["oggetto"] for e in ev
                      if e["tipo"] in ("poi_tap", "poi_dettaglio", "poi_naviga") and e["oggetto"]).most_common(12)
    top_tab = Counter(e["oggetto"] for e in ev if e["tipo"] == "nearby_tab").most_common(6)
    intenzione = Counter(e["tipo"] for e in ev)
    per_giorno = Counter(e["ts"][:10] for e in ev if e["tipo"] == "pageview")
    per_tenant = defaultdict(lambda: {"sess": set(), "ev": 0})
    for e in ev:
        per_tenant[e["tenant"]]["sess"].add(e["sid"]); per_tenant[e["tenant"]]["ev"] += 1

    # trend settimanale semplice (barre testuali, niente dipendenze)
    giorni_ord = sorted(per_giorno.items())
    mx = max((n for _, n in giorni_ord), default=1)
    trend = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;font-size:12px;margin:2px 0">'
        f'<span style="width:74px;color:#8a7f6a">{g[5:]}</span>'
        f'<span style="display:inline-block;height:10px;border-radius:5px;background:#c9a227;'
        f'width:{max(3, round(n / mx * 100))}%"></span><b>{n}</b></div>'
        for g, n in giorni_ord[-21:]) or "<i>—</i>"

    def blocco(titolo, corpo):
        return (f'<div style="background:#fff;border:1px solid #e8e0d0;border-radius:14px;'
                f'padding:22px;margin-bottom:14px"><h2 style="font-size:17px;margin:0 0 12px">'
                f'{titolo}</h2>{corpo}</div>')

    li = lambda pairs, suff="": "".join(
        f"<li><b>{html.escape(str(k))}</b> — {n}{suff}</li>" for k, n in pairs) or "<li>—</li>"

    righe_tenant = "".join(
        f"<tr><td style='padding:6px 10px'>{html.escape(t)}</td>"
        f"<td style='padding:6px 10px;text-align:right'>{len(d['sess'])}</td>"
        f"<td style='padding:6px 10px;text-align:right'>{d['ev']}</td></tr>"
        for t, d in sorted(per_tenant.items(), key=lambda x: -len(x[1]["sess"])))

    kpi = [("Sessioni visitatore", sessioni), ("Strutture in rete", len(tenants)),
           ("Luoghi esplorati", intenzione.get("poi_tap",0)+intenzione.get("poi_dettaglio",0)),
           ("Navigazioni verso i luoghi", intenzione.get("poi_naviga", 0)),
           ("Intenzioni di prenotazione", intenzione.get("esperienza_tap", 0)),
           ("Interazioni totali", len(ev))]
    kpi_html = "".join(
        f'<div style="background:#fff;border:1px solid #e8e0d0;border-radius:14px;padding:18px;text-align:center">'
        f'<div style="font-size:28px;font-weight:700;color:#1a3a2e">{v}</div>'
        f'<div style="font-size:11px;color:#8a7f6a;text-transform:uppercase;letter-spacing:.05em;margin-top:4px">{k}</div></div>'
        for k, v in kpi)

    tot_l = max(1, sum(lingue.values()))
    li_lang = "".join(f"<li>{LINGUE.get(l, l)} — <b>{round(n/tot_l*100)}%</b></li>" for l, n in lingue.most_common(6)) or "<li>—</li>"

    return f"""<!DOCTYPE html><html lang="it"><head><meta charset="utf-8">
<title>Osservatorio del Territorio · {datetime.now().strftime('%B %Y')}</title></head>
<body style="margin:0;background:#faf6ef;font-family:Georgia,serif;color:#1a3a2e">
<div style="max-width:680px;margin:0 auto;padding:34px 20px">
  <div style="text-align:center;margin-bottom:26px">
    <div style="font-size:11px;letter-spacing:.3em;text-transform:uppercase;color:#c9a227;font-weight:700">Esplora OS · Osservatorio del Territorio</div>
    <h1 style="font-weight:400;font-size:30px;margin:8px 0 2px">Cosa cercano i visitatori, davvero</h1>
    <div style="color:#8a7f6a;font-size:13px">Ultimi {giorni} giorni · dati anonimi aggregati dalla rete di strutture ricettive</div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:22px">{kpi_html}</div>
  {blocco('🗺 I luoghi più desiderati del territorio', f'<ol style="margin:0;padding-left:20px;line-height:1.9;font-size:14px">{li(top_poi, " interazioni")}</ol>')}
  {blocco('🌍 Da dove vengono (lingua di navigazione)', f'<ul style="margin:0;padding-left:18px;line-height:1.9;font-size:14px">{li_lang}</ul>')}
  {blocco('🧭 Cosa cercano (categorie esplorate)', f'<ul style="margin:0;padding-left:18px;line-height:1.9;font-size:14px">{li(top_tab)}</ul>')}
  {blocco('📈 Andamento giornaliero (aperture guida)', trend)}
  {blocco('🏨 La rete', f'<table style="width:100%;border-collapse:collapse;font-size:14px"><tr style="color:#8a7f6a;font-size:11px;text-transform:uppercase"><th style="text-align:left;padding:6px 10px">Struttura</th><th style="text-align:right;padding:6px 10px">Sessioni</th><th style="text-align:right;padding:6px 10px">Interazioni</th></tr>{righe_tenant}</table>')}
  <p style="text-align:center;font-size:12px;color:#8a7f6a;margin-top:24px">
    Nessun dato personale raccolto · metodologia disponibile su richiesta · esploratrapani.it</p>
</div></body></html>"""


if __name__ == "__main__":
    giorni = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    eventi = scarica_eventi(None, giorni)
    if not eventi:
        print("Nessun evento nel periodo."); sys.exit(0)
    nome = f"osservatorio_territorio_{datetime.now().strftime('%Y-%m')}.html"
    open(nome, "w", encoding="utf-8").write(genera_osservatorio(eventi, giorni))
    print(f"✓ {nome}  ({len(eventi)} eventi, {len({e['sid'] for e in eventi})} sessioni, "
          f"{len({e['tenant'] for e in eventi})} strutture)")

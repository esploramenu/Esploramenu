#!/usr/bin/env python3
"""ESPLORA OS — Cron GIORNALIERO (Railway, 04:00): solo il backup con rotazione GFS."""
import subprocess, sys, os, datetime
print("🌙 Backup giornaliero ·", datetime.date.today().isoformat())
r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "backup_welcome.py")],
                   env=os.environ, timeout=600)
sys.exit(r.returncode)

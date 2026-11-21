#!/usr/bin/env python3
"""Refresh the complete public file inventory after intentional website changes."""
import hashlib
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.git','.venv','__pycache__','.pytest_cache','build','dist','.cache','.firecrawl','.browser-artifacts'}
records=[]
for root,dirs,files in os.walk(ROOT):
    dirs[:]=[d for d in dirs if d not in EXCLUDED and not d.endswith('.egg-info')]
    for name in sorted(files):
        p=Path(root)/name
        if p==ROOT/'manifest.json':continue
        records.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
manifest={'schema_version':1,'snapshot_date':'2026-11-21','hash_algorithm':'sha256','scope':'Complete public portfolio and web gallery; excludes environments, caches and this manifest itself. Original six-map snapshot is preserved in outputs and sources/snapshot-provenance.json.','files':sorted(records,key=lambda r:r['path'])}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f"Inventoried {len(records)} files.")

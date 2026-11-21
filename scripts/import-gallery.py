#!/usr/bin/env python3
"""Publish web derivatives of generated renders; never copy raw election data."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
RASTER = {'.png', '.jpg', '.jpeg', '.webp'}
EXCLUDE = {'raw', 'vendor', 'screenshots', 'dogfood-output', 'header-review', 'manual-numeric-review', 'fragment-context-review', '__pycache__', 'qa', 'assets', 'slides', 'reference'}
STATES = ['Alabama','Alaska','Arkansas','Florida','Georgia','Kansas','Louisiana','Mississippi','North Carolina','Pennsylvania','South Carolina','Tennessee','Texas','Virginia','Wisconsin','Wyoming']

def humanize(value):
    value = re.sub(r'(?<=\D)-(?=\d{4}(?:-|$))', ' ', value)
    value = value.replace('_', ' ').replace('-', ' ')
    value = re.sub(r'\b(cd|hd|sd)(\d+)\b', lambda m: m[1].upper() + ' ' + str(int(m[2])), value, flags=re.I)
    value = re.sub(r'\b(us|vap|gop|nyt|al02)\b',lambda m:m[0].upper(),value,flags=re.I)
    return value[0].upper() + value[1:] if value else value

def clean(text):
    return re.sub(r'/(?:home|Users)/[\w.-]+/[^\s\)\]"\'`]+', '[local source path]', str(text))

def category(path):
    text = str(path).lower()
    if text.startswith('political-map-studio'): return 'Design studies'
    if any(s in text for s in ['scenario','counterfactual','figures-win']): return 'Scenarios'
    if any(s in text for s in ['crosswalk','quality','audit','comparison-chart','age-matrice','demographic','racial','electorate']): return 'Analysis'
    if any(s in text for s in ['turnout','voters']): return 'Turnout'
    if any(s in text for s in ['swing','shift','realignment','change']): return 'Electoral change'
    if any(s in text for s in ['design-alternatives','original-broadsheet']): return 'Design studies'
    return 'Election results'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    args=parser.parse_args(); archive=args.archive.resolve()
    candidates=sorted(p for p in (archive/'outputs').rglob('*') if p.is_file() and p.suffix.lower() in RASTER)
    candidates += sorted(p for p in (archive/'political-map-studio'/'output').rglob('*') if p.is_file() and p.suffix.lower() in RASTER)
    # Published original broadsheet is an additional render absent from the main archive.
    candidates += sorted((ROOT/'outputs').rglob('*.png'))
    records=[];excluded=[];collections={};seen={};duplicates=[]
    for path in candidates:
        local=path.is_relative_to(ROOT)
        rel=path.relative_to(ROOT if local else archive)
        if any(part in EXCLUDE for part in rel.parts):
            excluded.append({'path':str(rel),'reason':'Raw source or non-publication support image'});continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen:
            duplicates.append({'path':str(rel),'same_as':seen[digest]});continue
        seen[digest]=str(rel)
        slug=rel.parts[1] if rel.parts[0]=='outputs' else 'political-map-studio'
        bundle=(ROOT if local else archive)/'outputs'/slug
        if slug not in collections:
            spec_path=bundle/'map_spec.json'
            spec=json.loads(spec_path.read_text()) if spec_path.exists() else {}
            title=spec.get('title') or humanize(slug)
            title=re.sub(r'Alabama2026','Alabama 2026',title)
            notes=[]
            for name in ['README.md','ANALYSIS.md','SOURCES.md','COMPLETENESS.md']:
                f=bundle/name
                if f.exists():notes.append(f'{name}\n\n'+clean(f.read_text()))
            credit='This map was created using data from the Redistricting Data Hub.' if any(s in '\n'.join(notes).lower() for s in ['redistricting data hub','vest','rdh']) else ''
            collections[slug]={'id':slug,'title':title,'notes':'\n\n'.join(notes),'credit':credit,'claim':('Illustrative studio design example; not verified election results.' if slug == 'political-map-studio' else clean(spec.get('claim','')))}
        col=collections[slug]
        tokens=str(rel).lower()
        state=next((s for s in STATES if tokens.startswith('outputs/'+s.lower().replace(' ','-')+'-')),None)
        if slug.startswith(('southern-','alabama-mississippi-')):state='Multiple states'
        if slug.startswith(('huntsville-','madison-')):state='Alabama'
        if slug.startswith('cook-'):state='Multiple states'
        if not state:state='Other'
        years=sorted(set(re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',str(rel))))
        name=humanize(path.stem)
        parent=path.parent.name
        if re.fullmatch(r'(?:governor|cd\d+|hd\d+|sd\d+|us-senate|[\w-]+-(?:result|swing))',path.stem) or len(name)<22:
            name=humanize(path.stem)+' · '+col['title']
        variant=' / '.join(humanize(s) for s in rel.parts[2:-1])
        records.append({'id':digest[:16],'title':name,'collection':slug,'state':state,'years':years,'category':category(rel),'source_path':str(rel),'source_sha256':digest,'source_bytes':path.stat().st_size,'variant':variant,'image':f'assets/maps/{digest[:16]}.webp','thumbnail':f'assets/thumbs/{digest[:16]}.webp','_path':path})
    for directory in ['assets/maps','assets/thumbs','data']:(ROOT/directory).mkdir(parents=True,exist_ok=True)
    def convert(record):
        path=record.pop('_path')
        with Image.open(path) as source:
            im=ImageOps.exif_transpose(source).convert('RGB')
            record['original_width'],record['original_height']=im.size
            full=im.copy();full.thumbnail((3000,3000),Image.Resampling.LANCZOS)
            record['width'],record['height']=full.size
            target=ROOT/record['image'];thumb=ROOT/record['thumbnail']
            if not target.exists():full.save(target,'WEBP',quality=90,method=4)
            if not thumb.exists():
                im.thumbnail((760,760),Image.Resampling.LANCZOS);im.save(thumb,'WEBP',quality=83,method=4)
        return record
    with ThreadPoolExecutor(max_workers=6) as pool:records=list(pool.map(convert,records))
    active_names = {m['id'] + '.webp' for m in records}
    for directory in ['assets/maps', 'assets/thumbs']:
        for derivative in (ROOT / directory).glob('*.webp'):
            if derivative.name not in active_names:
                derivative.unlink()
    # Put the latest statewide and regional work ahead of district series.
    preferred=['southern-nine-state-2026-midterm-clean','alabama-2026-jackson-meeting-revised','alabama-2017-senate-special-election','kansas-2016-2024-relative-partisan-swing','tennessee-2016-2024-presidential-swing','alabama-1992-2024-presidential-realignment']
    records.sort(key=lambda r:(preferred.index(r['collection']) if r['collection'] in preferred else len(preferred),r['collection'],r['source_path']))
    data={'schema_version':1,'updated':'2026-11-21','scope':'Unique generated raster renders from publication output collections and studio exports. Includes maps, design variants and companion charts. Duplicate bytes and SVG alternatives are collapsed; raw scans, vendor assets and browser captures are excluded. Web images are resized derivatives; original source fingerprints are retained.','collections':list(collections.values()),'images':records}
    (ROOT/'data/gallery.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/gallery.js').write_text('window.ELECTION_ARCHIVE = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    report={'eligible_rasters':len(candidates)-len(excluded),'unique_images':len(records),'collections':len(collections),'excluded':excluded,'identical_duplicates':duplicates,'duplicate_count':len(duplicates),'svg_alternates_not_copied':sum(1 for _ in (archive/'outputs').rglob('*.svg'))}
    (ROOT/'data/import-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"Imported {len(records)} images in {len(collections)} collections; {len(duplicates)} identical duplicates collapsed, {len(excluded)} source/support images excluded.")

if __name__=='__main__':main()

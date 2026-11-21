"""Regression checks for replacing published images without stale previews or links."""
import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]


def importer():
    spec=importlib.util.spec_from_file_location('gallery_import',ROOT/'scripts/import-gallery.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_changed_source_replaces_both_previews_and_preserves_shared_map_id(tmp_path,monkeypatch):
    archive=tmp_path/'archive'
    source=archive/'outputs/alabama-2026-test/map.png'
    source.parent.mkdir(parents=True)
    site=tmp_path/'site';site.mkdir()
    Image.new('RGB',(30,20),'red').save(source)
    module=importer();monkeypatch.setattr(module,'ROOT',site)
    monkeypatch.setattr('sys.argv',['import-gallery.py','--archive',str(archive)])
    module.main()
    first=json.loads((site/'data/gallery.json').read_text())['images'][0]
    first_bytes={key:(site/first[key]).read_bytes() for key in ['image','thumbnail']}
    Image.new('RGB',(30,20),'blue').save(source)
    module.main()
    second=json.loads((site/'data/gallery.json').read_text())['images'][0]
    assert second['id']==first['id']
    assert second['source_sha256']!=first['source_sha256']
    assert second['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
    for key in ['image','thumbnail']:
        assert second[key]==first[key]
        assert (site/second[key]).read_bytes()!=first_bytes[key]
    assert len(list((site/'assets/maps').glob('*.webp')))==1


def test_known_broken_studio_intermediate_is_accounted_for_and_completed_example_remains(tmp_path,monkeypatch):
    archive=tmp_path/'archive'
    studio=archive/'political-map-studio/output';studio.mkdir(parents=True)
    Image.new('RGB',(30,20),'white').save(studio/'browser-verified.png')
    Image.new('RGB',(30,20),'blue').save(studio/'browser-verified-insets.png')
    site=tmp_path/'site';site.mkdir()
    module=importer();monkeypatch.setattr(module,'ROOT',site)
    monkeypatch.setattr('sys.argv',['import-gallery.py','--archive',str(archive)])
    module.main()
    images=json.loads((site/'data/gallery.json').read_text())['images']
    assert len(images)==1
    assert images[0]['source_path'].endswith('browser-verified-insets.png')
    report=json.loads((site/'data/import-report.json').read_text())
    assert len(report['excluded'])==1
    assert 'empty inset' in report['excluded'][0]['reason']

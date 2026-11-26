"""A live release portal must serve actual artifacts, not a pretend web sanitizer."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def test_portal_never_asks_to_upload_sensitive_documents():
    root = Path(__file__).resolve().parents[1]
    html = (root / 'site/index.html').read_text()
    assert '<input type="file"' not in html
    assert 'processed locally' in html
    assert '%%DEB_FILE%%' in html
    assert 'confidentiality clearance' in html


def test_generated_portal_assets_and_digests(tmp_path):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / 'public'
    subprocess.run(['bash', str(root/'scripts/build_live_site.sh'), str(output)],
                   cwd=root, capture_output=True, check=True)
    manifest = json.loads((output/'release.json').read_text())
    assert manifest['status'] == 'human_review_required'
    for category in ('debian', 'wheel', 'source'):
        entry = manifest[category]
        path = output / entry['url'].lstrip('/')
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
        if path.suffix in ('.zip', '.whl'):
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None
    page = (output/'index.html').read_text()
    assert '%%' not in page
    assert manifest['debian']['name'] in page
    assert (output/'downloads/SHA256SUMS').is_file()


def test_release_builder_excludes_private_project_files(tmp_path):
    root = Path(__file__).resolve().parents[1]
    target = tmp_path/'dist'
    subprocess.run(['bash', str(root/'scripts/build_live_site.sh'), str(target)],
                   cwd=root, capture_output=True, check=True)
    archive = target/'downloads'/f"office-sanitizer-{json.loads((target/'release.json').read_text())['version']}-source.zip"
    with zipfile.ZipFile(archive) as z:
        assert all(not n.endswith('.key') and '__pycache__' not in n for n in z.namelist())

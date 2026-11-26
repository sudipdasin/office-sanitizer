"""Offline distribution must install without network and remain deterministic."""
import hashlib
from pathlib import Path
import zipfile
from scripts.build_wheel_offline import build_wheel


def test_offline_wheel_deterministic(tmp_path):
    root = Path(__file__).resolve().parents[1]
    a = build_wheel(root, tmp_path / 'a')
    b = build_wheel(root, tmp_path / 'b')
    assert hashlib.sha256(a.read_bytes()).digest() == hashlib.sha256(b.read_bytes()).digest()
    with zipfile.ZipFile(a) as z:
        assert z.testzip() is None
        assert any(name.endswith('.dist-info/RECORD') for name in z.namelist())
        assert not any('__pycache__' in name or '.key' in name for name in z.namelist())


def test_offline_wheel_contains_all_entrypoints(tmp_path):
    wheel = build_wheel(Path(__file__).resolve().parents[1], tmp_path)
    with zipfile.ZipFile(wheel) as z:
        entry = next(name for name in z.namelist() if name.endswith('.dist-info/entry_points.txt'))
        text = z.read(entry).decode()
        assert all(name in text for name in (
            'office-sanitizer = ', 'office-sanitizer-gui = ', 'office-sanitizer-update = '))

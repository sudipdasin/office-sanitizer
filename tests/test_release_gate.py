"""Adversarial publishing tests: generated output is never silently replaced."""
import os
import zipfile
from unittest.mock import patch
from office_sanitizer.core import sanitize
from office_sanitizer.security import validate_package
from test_core import fixture


def test_independent_verification_called_before_publication(tmp_path):
    src, dst = tmp_path/'a.docx', tmp_path/'clean.docx'
    fixture(src)
    from office_sanitizer.verify import Verification
    with patch('office_sanitizer.verify.verify_output', return_value=Verification()):
        r = sanitize(src, dst)
    assert r.status == 'failed' and not dst.exists()
    assert not list(tmp_path.glob('.office-sanitizer-*'))


def test_racing_output_does_not_get_replaced(tmp_path):
    src, dst = tmp_path/'a.docx', tmp_path/'clean.docx'
    fixture(src)
    real_link = os.link
    def racing_link(a, b):
        dst.write_bytes(b'other process output')
        return real_link(a, b)
    with patch('office_sanitizer.core.os.link', side_effect=racing_link):
        r = sanitize(src, dst)
    assert r.status == 'failed' and dst.read_bytes() == b'other process output'
    assert not list(tmp_path.glob('.office-sanitizer-*'))


def test_large_xml_rejected_before_transformation(tmp_path):
    src, dst = tmp_path/'a.docx', tmp_path/'clean.docx'
    fixture(src)
    with zipfile.ZipFile(src, 'a', zipfile.ZIP_STORED) as z:
        z.writestr('word/big.xml', b'A' * (32 * 1024 * 1024 + 1))
    r = sanitize(src, dst)
    assert r.status == 'failed' and not dst.exists()


def test_valid_package_still_publishes(tmp_path):
    src, dst = tmp_path/'a.docx', tmp_path/'clean.docx'
    fixture(src)
    r = sanitize(src, dst)
    assert r.verified and dst.exists()
    with zipfile.ZipFile(dst) as z:
        validate_package(z)

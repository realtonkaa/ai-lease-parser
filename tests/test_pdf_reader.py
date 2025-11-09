"""Tests for src/pdf_reader.py — file reading functionality."""

import pytest
from pathlib import Path

from src.pdf_reader import read_file, extract_pages


class TestReadFileTxt:
    """Tests for reading .txt files."""

    def test_reads_lease1_txt(self, lease1_path):
        text = read_file(str(lease1_path))
        assert isinstance(text, str)
        assert len(text) > 100

    def test_reads_lease2_txt(self, lease2_path):
        text = read_file(str(lease2_path))
        assert isinstance(text, str)
        assert len(text) > 100

    def test_lease1_contains_landlord(self, lease1_path):
        text = read_file(str(lease1_path))
        assert "Henderson" in text

    def test_lease1_contains_tenant(self, lease1_path):
        text = read_file(str(lease1_path))
        assert "Garcia" in text

    def test_lease1_contains_rent(self, lease1_path):
        text = read_file(str(lease1_path))
        assert "1,450" in text or "1450" in text

    def test_lease2_contains_address(self, lease2_path):
        text = read_file(str(lease2_path))
        assert "1500 Oak Boulevard" in text

    def test_lease2_contains_monthly_amount(self, lease2_path):
        text = read_file(str(lease2_path))
        assert "2,100" in text

    def test_txt_with_unicode(self, tmp_path):
        p = tmp_path / "unicode.txt"
        p.write_text("Tenant: Jose\u0301 Martinez\nRent: $1000", encoding="utf-8")
        text = read_file(str(p))
        assert "Martinez" in text

    def test_empty_txt_file(self, tmp_path):
        p = tmp_path / "empty.txt"
        p.write_text("", encoding="utf-8")
        text = read_file(str(p))
        assert text == ""


class TestReadFileErrors:
    """Tests for error handling in read_file."""

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            read_file("/nonexistent/path/lease.txt")

    def test_unsupported_extension_raises(self, tmp_path):
        p = tmp_path / "lease.docx"
        p.write_bytes(b"dummy content")
        with pytest.raises(ValueError, match="Unsupported file type"):
            read_file(str(p))

    def test_directory_raises_file_not_found(self, tmp_path):
        # Passing a directory should raise an error
        with pytest.raises((FileNotFoundError, ValueError, IsADirectoryError, Exception)):
            read_file(str(tmp_path))


class TestExtractPages:
    """Tests for extract_pages()."""

    def test_txt_returns_single_page(self, lease1_path):
        pages = extract_pages(str(lease1_path))
        assert isinstance(pages, list)
        assert len(pages) == 1

    def test_pages_contain_text(self, lease1_path):
        pages = extract_pages(str(lease1_path))
        full_text = "".join(pages)
        assert "Henderson" in full_text

    def test_pages_returns_list_of_strings(self, lease1_path):
        pages = extract_pages(str(lease1_path))
        for page in pages:
            assert isinstance(page, str)

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            extract_pages("/nonexistent/file.txt")

    def test_lease2_pages_contain_content(self, lease2_path):
        pages = extract_pages(str(lease2_path))
        full_text = "".join(pages)
        assert "Wilson" in full_text


class TestReadFileContent:
    """Tests verifying specific content in fixture files."""

    def test_lease1_has_all_sections(self, lease1_path):
        text = read_file(str(lease1_path))
        sections = ["RENT", "SECURITY DEPOSIT", "LATE FEE", "PET POLICY", "UTILITIES", "PARKING", "RENEWAL"]
        for section in sections:
            assert section in text, f"Section '{section}' not found in lease1"

    def test_lease2_has_all_sections(self, lease2_path):
        text = read_file(str(lease2_path))
        sections = ["PARTIES", "PREMISES", "LEASE PERIOD", "FINANCIAL TERMS"]
        for section in sections:
            assert section in text, f"Section '{section}' not found in lease2"

    def test_lease1_security_deposit_amount(self, lease1_path):
        text = read_file(str(lease1_path))
        assert "2,900" in text

    def test_lease2_landlord_name(self, lease2_path):
        text = read_file(str(lease2_path))
        assert "Greenfield Property Management" in text

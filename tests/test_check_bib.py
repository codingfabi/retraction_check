import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retraction_check.check_bib import (
    parse_bib_file,
    download_retraction_watch_csv,
    build_retraction_lookup,
    fuzzy_title_match,
    is_retracted,
    check_entry,
    BibEntry
)


class TestParseBibFile(unittest.TestCase):
    
    @patch('builtins.open', new_callable=mock_open, read_data='@article{test,\ntitle={Test Title},\nauthor={Test Author}\n}')
    @patch('bibtexparser.load')
    def test_parse_valid_bib_file(self, mock_load, mock_file):
        mock_db = MagicMock()
        mock_db.entries = [{'title': 'Test Title', 'author': 'Test Author'}]
        mock_load.return_value = mock_db
        
        result = parse_bib_file('test.bib')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'Test Title')
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_parse_file_not_found(self, mock_file):
        result = parse_bib_file('nonexistent.bib')
        self.assertEqual(result, [])
    
    @patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'test'))
    def test_parse_unicode_decode_error(self, mock_file):
        result = parse_bib_file('invalid_encoding.bib')
        self.assertEqual(result, [])
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('bibtexparser.load')
    def test_parse_empty_bib_file(self, mock_load, mock_file):
        mock_db = MagicMock()
        mock_db.entries = []
        mock_load.return_value = mock_db
        
        result = parse_bib_file('empty.bib')
        self.assertEqual(result, [])


class TestDownloadRetractionWatchCSV(unittest.TestCase):
    
    @patch('requests.get')
    def test_download_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = 'Title,OriginalPaperDOI\nTest Paper,10.1234/test'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = download_retraction_watch_csv()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['Title'], 'Test Paper')
    
    @patch('requests.get')
    def test_download_network_error(self, mock_get):
        mock_get.side_effect = Exception('Network error')
        
        result = download_retraction_watch_csv()
        self.assertEqual(result, [])
    
    @patch('requests.get')
    def test_download_missing_columns(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = 'WrongColumn\nTest Value'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = download_retraction_watch_csv()
        self.assertEqual(result, [])


class TestBuildRetractionLookup(unittest.TestCase):
    
    def test_build_lookup_with_valid_data(self):
        csv_rows = [
            {'Title': 'Test Paper 1', 'OriginalPaperDOI': '10.1234/test1'},
            {'Title': 'Test Paper 2', 'OriginalPaperDOI': '10.1234/test2'},
            {'Title': '', 'OriginalPaperDOI': ''}  # Empty row
        ]
        
        titles, dois = build_retraction_lookup(csv_rows)
        
        self.assertEqual(len(titles), 2)
        self.assertEqual(len(dois), 2)
        self.assertIn('Test Paper 1', titles)
        self.assertIn('10.1234/test1', dois)
    
    def test_build_lookup_with_empty_data(self):
        csv_rows = []
        
        titles, dois = build_retraction_lookup(csv_rows)
        
        self.assertEqual(len(titles), 0)
        self.assertEqual(len(dois), 0)


class TestFuzzyTitleMatch(unittest.TestCase):
    
    def test_fuzzy_match_exact(self):
        titles = {'Test Paper Title'}
        result = fuzzy_title_match('Test Paper Title', titles)
        self.assertTrue(result)
    
    def test_fuzzy_match_similar(self):
        titles = {'Test Paper Title'}
        result = fuzzy_title_match('Test Paper Titl', titles)
        self.assertTrue(result)
    
    def test_fuzzy_match_no_match(self):
        titles = {'Machine Learning Applications in Healthcare'}
        result = fuzzy_title_match('Quantum Computing Algorithms', titles)
        self.assertFalse(result)
    
    def test_fuzzy_match_empty_title(self):
        titles = {'Test Paper Title'}
        result = fuzzy_title_match('', titles)
        self.assertFalse(result)


class TestIsRetracted(unittest.TestCase):
    
    def setUp(self):
        self.titles = {'Retracted Paper Title'}
        self.dois = {'10.1234/retracted'}
    
    def test_doi_match(self):
        entry: BibEntry = {'title': 'Some Title', 'doi': '10.1234/retracted'}
        result = is_retracted(entry, self.titles, self.dois)
        self.assertEqual(result, 'doi')
    
    def test_fuzzy_title_match(self):
        entry: BibEntry = {'title': 'Retracted Paper Title', 'doi': ''}
        result = is_retracted(entry, self.titles, self.dois)
        self.assertEqual(result, 'fuzzy')
    
    def test_no_match(self):
        entry: BibEntry = {'title': 'Completely Different Research Topic', 'doi': '10.1234/clean'}
        result = is_retracted(entry, self.titles, self.dois)
        self.assertIsNone(result)
    
    def test_invalid_entry(self):
        # Test with a malformed entry that could cause exceptions
        entry = None
        result = is_retracted(entry, self.titles, self.dois)
        self.assertIsNone(result)


class TestCheckEntry(unittest.TestCase):
    
    @patch('retraction_check.check_bib.download_retraction_watch_csv')
    @patch('retraction_check.check_bib.build_retraction_lookup')
    def test_check_entry_with_provided_lookup(self, mock_build, mock_download):
        titles = {'Retracted Paper'}
        dois = {'10.1234/retracted'}
        entry: BibEntry = {'title': 'Retracted Paper', 'doi': ''}
        
        result = check_entry(entry, titles, dois)
        
        # Should not call download or build since lookup is provided
        mock_download.assert_not_called()
        mock_build.assert_not_called()
        self.assertEqual(result, 'fuzzy')
    
    @patch('retraction_check.check_bib.download_retraction_watch_csv')
    @patch('retraction_check.check_bib.build_retraction_lookup')
    def test_check_entry_without_lookup(self, mock_build, mock_download):
        mock_download.return_value = []
        mock_build.return_value = (set(), set())
        entry: BibEntry = {'title': 'Clean Paper', 'doi': ''}
        
        result = check_entry(entry)
        
        # Should call download and build since lookup is not provided
        mock_download.assert_called_once()
        mock_build.assert_called_once()
        self.assertIsNone(result)


class TestCheckBibFileEndToEnd(unittest.TestCase):
    """End-to-end tests for the complete workflow"""
    
    @patch('retraction_check.check_bib.download_retraction_watch_csv')
    @patch('builtins.open', new_callable=mock_open, read_data='@article{test,\ntitle={Test Paper},\ndoi={10.1234/test}\n}')
    @patch('bibtexparser.load')
    def test_check_bib_file_no_retractions(self, mock_load, mock_file, mock_download):
        # Mock bib file parsing
        mock_db = MagicMock()
        mock_db.entries = [{'title': 'Test Paper', 'doi': '10.1234/test'}]
        mock_load.return_value = mock_db
        
        # Mock CSV download with no matching retractions
        mock_download.return_value = [
            {'Title': 'Different Paper', 'OriginalPaperDOI': '10.1234/different'}
        ]
        
        # This should run without errors
        from retraction_check.check_bib import check_bib_file
        try:
            check_bib_file('test.bib')
        except Exception as e:
            self.fail(f"check_bib_file raised an exception: {e}")
    
    @patch('retraction_check.check_bib.download_retraction_watch_csv')
    @patch('builtins.open', new_callable=mock_open, read_data='@article{test,\ntitle={Retracted Paper},\ndoi={10.1234/retracted}\n}')
    @patch('bibtexparser.load')
    def test_check_bib_file_with_retractions(self, mock_load, mock_file, mock_download):
        # Mock bib file parsing
        mock_db = MagicMock()
        mock_db.entries = [{'title': 'Retracted Paper', 'doi': '10.1234/retracted'}]
        mock_load.return_value = mock_db
        
        # Mock CSV download with matching retraction
        mock_download.return_value = [
            {'Title': 'Retracted Paper', 'OriginalPaperDOI': '10.1234/retracted'}
        ]
        
        # This should run without errors and find the retraction
        from retraction_check.check_bib import check_bib_file
        try:
            check_bib_file('test.bib')
        except Exception as e:
            self.fail(f"check_bib_file raised an exception: {e}")
    
    @patch('retraction_check.check_bib.download_retraction_watch_csv')
    def test_check_bib_file_nonexistent_file(self, mock_download):
        # Mock CSV download
        mock_download.return_value = []
        
        # Test with a file that doesn't exist
        from retraction_check.check_bib import check_bib_file
        try:
            check_bib_file('nonexistent_file.bib')
        except Exception as e:
            self.fail(f"check_bib_file should handle nonexistent files gracefully: {e}")


if __name__ == '__main__':
    unittest.main()

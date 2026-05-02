import pytest
from unittest.mock import patch
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from documents.models import Document, DocumentChunk
from documents.services.pipeline import process_document


class TestPipeline(TestCase):

    def _create_document(self, content=b"Test content for pipeline."):
        uploaded_file = SimpleUploadedFile(
            "test.txt", content, content_type="text/plain"
        )
        return Document.objects.create(
            title="Test Document", file=uploaded_file, status='pending'
        )

    @patch('documents.services.pipeline.embed_texts')
    def test_pipeline_creates_chunks(self, mock_embed):
        mock_embed.return_value = [[0.0] * 384] * 10
        doc = self._create_document(
            b"Django is a framework.\n\npgvector adds vector search.\n\nCelery handles async tasks.\n\n"
        )
        process_document(doc.id)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'done')
        self.assertGreater(DocumentChunk.objects.filter(document=doc).count(), 0)

    @patch('documents.services.pipeline.embed_texts')
    def test_failed_embed_rolls_back(self, mock_embed):
        mock_embed.side_effect = Exception("Embedding service down")
        doc = self._create_document()
        with self.assertRaises(Exception):
            process_document(doc.id)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'failed')
        self.assertEqual(DocumentChunk.objects.filter(document=doc).count(), 0)

    @patch('documents.services.pipeline.embed_texts')
    def test_empty_file_fails_gracefully(self, mock_embed):
        mock_embed.return_value = []
        doc = self._create_document(b"   ")
        with self.assertRaises((ValueError, Exception)):
            process_document(doc.id)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'failed')


class TestParser(TestCase):

    def test_txt_extraction(self):
        from documents.services.parser import extract_text
        f = SimpleUploadedFile("test.txt", b"Hello world", content_type="text/plain")
        result = extract_text(f)
        self.assertIn("Hello world", result)

    def test_unsupported_format_raises(self):
        from documents.services.parser import extract_text
        f = SimpleUploadedFile("test.xyz", b"some bytes", content_type="application/octet-stream")
        with self.assertRaises(ValueError):
            extract_text(f)

    def test_csv_extraction(self):
        from documents.services.parser import extract_text
        csv_content = b"name,age,city\nAyush,22,Delhi\nRohan,25,Mumbai"
        f = SimpleUploadedFile("data.csv", csv_content, content_type="text/plain")
        result = extract_text(f)
        self.assertIn("Ayush", result)
        self.assertIn("Delhi", result)


class TestUploadSerializer(TestCase):

    def test_rejects_file_over_limit(self):
        from documents.serializers import DocumentUploadSerializer
        large_file = SimpleUploadedFile(
            "big.pdf", b"x" * (11 * 1024 * 1024), content_type="application/pdf"
        )
        serializer = DocumentUploadSerializer(data={'title': 'Big file', 'file': large_file})
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)

    def test_requires_file_or_text(self):
        from documents.serializers import DocumentUploadSerializer
        serializer = DocumentUploadSerializer(data={'title': 'Nothing'})
        self.assertFalse(serializer.is_valid())

    def test_valid_text_upload(self):
        from documents.serializers import DocumentUploadSerializer
        serializer = DocumentUploadSerializer(data={
            'title': 'Text upload',
            'text': 'This is some valid document text content.'
        })
        self.assertTrue(serializer.is_valid())

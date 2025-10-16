import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from app.main import app
from app.models.newsletter_sample import NewsletterSampleResponse


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "is_active": True
    }


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    mock = Mock()
    return mock


class TestNewsletterUpload:
    """Test newsletter upload endpoints"""
    
    def test_upload_newsletter_text(self, client, mock_user, mock_supabase):
        """Test uploading newsletter via direct text input"""
        with patch("app.api.dependencies.get_current_active_user", return_value=mock_user), \
             patch("app.core.database.get_supabase", return_value=mock_supabase):
            
            # Mock Supabase response
            mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "sample-id",
                "user_id": "test-user-id",
                "title": "Test Newsletter",
                "content": "This is a test newsletter content with enough text to pass validation.",
                "created_at": datetime.now().isoformat()
            }]
            
            response = client.post(
                "/api/newsletters/upload",
                json={
                    "title": "Test Newsletter",
                    "content": "This is a test newsletter content with enough text to pass validation."
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "Test Newsletter"
            assert "content" in data
    
    def test_upload_newsletter_markdown(self, client, mock_user, mock_supabase):
        """Test uploading newsletter with markdown format"""
        with patch("app.api.dependencies.get_current_active_user", return_value=mock_user), \
             patch("app.core.database.get_supabase", return_value=mock_supabase):
            
            # Mock Supabase response
            mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "sample-id",
                "user_id": "test-user-id",
                "title": "Markdown Newsletter",
                "content": "# Heading\n\nThis is markdown content.",
                "created_at": datetime.now().isoformat()
            }]
            
            response = client.post(
                "/api/newsletters/upload",
                json={
                    "title": "Markdown Newsletter",
                    "file_content": "# Heading\n\nThis is markdown content.",
                    "file_format": "md"
                }
            )
            
            assert response.status_code == 201
    
    def test_upload_newsletter_html(self, client, mock_user, mock_supabase):
        """Test uploading newsletter with HTML format"""
        with patch("app.api.dependencies.get_current_active_user", return_value=mock_user), \
             patch("app.core.database.get_supabase", return_value=mock_supabase):
            
            # Mock Supabase response
            mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "sample-id",
                "user_id": "test-user-id",
                "title": "HTML Newsletter",
                "content": "This is HTML content.",
                "created_at": datetime.now().isoformat()
            }]
            
            response = client.post(
                "/api/newsletters/upload",
                json={
                    "title": "HTML Newsletter",
                    "file_content": "<h1>Heading</h1><p>This is HTML content.</p>",
                    "file_format": "html"
                }
            )
            
            assert response.status_code == 201
    
    def test_upload_newsletter_no_content(self, client, mock_user, mock_supabase):
        """Test uploading newsletter without content should fail"""
        with patch("app.api.dependencies.get_current_active_user", return_value=mock_user), \
             patch("app.core.database.get_supabase", return_value=mock_supabase):
            
            response = client.post(
                "/api/newsletters/upload",
                json={
                    "title": "Empty Newsletter"
                }
            )
            
            assert response.status_code == 400
    
    def test_upload_newsletter_short_content(self, client, mock_user, mock_supabase):
        """Test uploading newsletter with too short content should fail"""
        with patch("app.api.dependencies.get_current_active_user", return_value=mock_user), \
             patch("app.core.database.get_supabase", return_value=mock_supabase):
            
            response = client.post(
                "/api/newsletters/upload",
                json={
                    "title": "Short Newsletter",
                    "content": "Short"
                }
            )
            
            assert response.status_code == 400
    
    def test_get_newsletter_samples(self, client, mock_user, mock_supabase):
        """Test getting all newsletter samples"""
        with patch("app.api.dependencies.get_current_active_user", return_value=mock_user), \
             patch("app.core.database.get_supabase", return_value=mock_supabase):
            
            # Mock Supabase response
            mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
                {
                    "id": "sample-1",
                    "user_id": "test-user-id",
                    "title": "Sample 1",
                    "content": "Content 1",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "sample-2",
                    "user_id": "test-user-id",
                    "title": "Sample 2",
                    "content": "Content 2",
                    "created_at": datetime.now().isoformat()
                }
            ]
            
            response = client.get("/api/newsletters/samples")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
    
    def test_delete_newsletter_sample(self, client, mock_user, mock_supabase):
        """Test deleting a newsletter sample"""
        with patch("app.api.dependencies.get_current_active_user", return_value=mock_user), \
             patch("app.core.database.get_supabase", return_value=mock_supabase):
            
            # Mock Supabase responses
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
                "id": "sample-id",
                "user_id": "test-user-id"
            }]
            
            mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
                "id": "sample-id"
            }]
            
            response = client.delete("/api/newsletters/samples/sample-id")
            
            assert response.status_code == 204
    
    def test_delete_nonexistent_sample(self, client, mock_user, mock_supabase):
        """Test deleting a non-existent newsletter sample should fail"""
        with patch("app.api.dependencies.get_current_active_user", return_value=mock_user), \
             patch("app.core.database.get_supabase", return_value=mock_supabase):
            
            # Mock Supabase response - no sample found
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
            
            response = client.delete("/api/newsletters/samples/nonexistent-id")
            
            assert response.status_code == 404


class TestFileUpload:
    """Test file upload endpoint"""
    
    def test_upload_txt_file(self, client, mock_user, mock_supabase):
        """Test uploading a .txt file"""
        with patch("app.api.dependencies.get_current_active_user", return_value=mock_user), \
             patch("app.core.database.get_supabase", return_value=mock_supabase):
            
            # Mock Supabase response
            mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{
                "id": "sample-id",
                "user_id": "test-user-id",
                "title": "test.txt",
                "content": "This is a test file content.",
                "created_at": datetime.now().isoformat()
            }]
            
            files = {"file": ("test.txt", b"This is a test file content.", "text/plain")}
            response = client.post("/api/newsletters/upload-file", files=files)
            
            assert response.status_code == 201
    
    def test_upload_invalid_file_format(self, client, mock_user, mock_supabase):
        """Test uploading an invalid file format should fail"""
        with patch("app.api.dependencies.get_current_active_user", return_value=mock_user), \
             patch("app.core.database.get_supabase", return_value=mock_supabase):
            
            files = {"file": ("test.pdf", b"PDF content", "application/pdf")}
            response = client.post("/api/newsletters/upload-file", files=files)
            
            assert response.status_code == 400
            assert "Only .txt, .md, and .html files are supported" in response.json()["detail"]

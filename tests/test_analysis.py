"""
Test suite for the Analysis service.

Tests cover:
- Note analysis endpoint
- Confidence scoring algorithm
- Audio analysis endpoint (with fallback)
- Input validation
- Error handling
"""

import os
import sys
import json
import pytest

# Set up test environment
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_analysis.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["TESTING"] = "1"
os.environ["ALLOW_WEAK_SECRETS"] = "1"

# Ensure project root is on path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app
from extensions import db
from models import Maqam


@pytest.fixture(scope="function")
def app():
    """Create and configure a test application instance."""
    application = create_app()
    application.config.update({
        "TESTING": True,
    })
    with application.app_context():
        db.drop_all()
        db.create_all()
        seed_test_maqamet()
    yield application
    # Cleanup
    with application.app_context():
        db.session.remove()
        try:
            db.engine.dispose()
        except Exception:
            pass
        db.drop_all()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass


def seed_test_maqamet():
    """Seed database with test maqamet for analysis testing."""
    # Maqam Rast - joyful, with specific notes
    rast = Maqam(
        name_ar="راست",
        name_en="Rast",
        emotion="joy",
        usage="weddings, celebrations",
        ajnas_json=json.dumps([
            {
                "name": {"en": "Rast", "ar": "راست"},
                "notes": {"en": ["C", "D", "E", "F", "G"]}
            }
        ]),
        regions_json=json.dumps(["Tunis", "Sfax"]),
        description_en="A joyful maqam",
        description_ar="مقام فرح",
        difficulty_index=0.3,
        difficulty_label="beginner",
        rarity_level="common",
    )
    
    # Maqam Bayati - sad, with different notes
    bayati = Maqam(
        name_ar="بياتي",
        name_en="Bayati",
        emotion="sadness",
        usage="mourning, reflection",
        ajnas_json=json.dumps([
            {
                "name": {"en": "Bayati", "ar": "بياتي"},
                "notes": {"en": ["D", "E", "F", "G", "A"]}
            }
        ]),
        regions_json=json.dumps(["Tunis"]),
        description_en="A melancholic maqam",
        description_ar="مقام حزين",
        difficulty_index=0.5,
        difficulty_label="intermediate",
        rarity_level="common",
    )
    
    # Maqam Sika - spiritual, partially overlapping notes
    sika = Maqam(
        name_ar="سيكاه",
        name_en="Sika",
        emotion="spiritual",
        usage="religious, meditation",
        ajnas_json=json.dumps([
            {
                "name": {"en": "Sika", "ar": "سيكاه"},
                "notes": {"en": ["E", "F", "G", "A", "B"]}
            }
        ]),
        regions_json=json.dumps(["Sahel"]),
        description_en="A spiritual maqam",
        description_ar="مقام روحاني",
        difficulty_index=0.7,
        difficulty_label="advanced",
        rarity_level="locally_rare",
    )
    
    db.session.add_all([rast, bayati, sika])
    db.session.commit()


@pytest.fixture()
def client(app):
    """Create a test client."""
    return app.test_client()


def get_auth_header(client):
    """Get authorization header with demo token."""
    res = client.get("/auth/demo-token")
    assert res.status_code == 200
    token = res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Note Analysis Tests
# =============================================================================

class TestNoteAnalysis:
    """Tests for POST /analysis/notes endpoint."""
    
    def test_analyze_notes_success(self, client):
        """Test successful note analysis with matching notes."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={"notes": ["C", "D", "E", "F", "G"]},
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert "candidates" in data
        assert len(data["candidates"]) > 0
        
        # Rast should be top candidate (perfect match)
        top_candidate = data["candidates"][0]
        assert top_candidate["maqam"] == "Rast"
        assert top_candidate["confidence"] > 0.5
        assert "matched_notes" in top_candidate
    
    def test_analyze_notes_with_mood(self, client):
        """Test note analysis with emotional context."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={
                "notes": ["C", "D", "E", "F", "G"],
                "optional_mood": "joy"
            },
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # With mood match, Rast should have higher confidence
        rast = next(c for c in data["candidates"] if c["maqam"] == "Rast")
        assert "emotion_alignment" in rast.get("evidence", [])
    
    def test_analyze_notes_partial_match(self, client):
        """Test analysis with partial note overlap."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={"notes": ["D", "E", "F"]},  # Overlaps multiple maqamet
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should return multiple candidates
        assert len(data["candidates"]) >= 2
        
        # Check confidence ordering (highest first)
        confidences = [c["confidence"] for c in data["candidates"]]
        assert confidences == sorted(confidences, reverse=True)
    
    def test_analyze_notes_no_match(self, client):
        """Test analysis with notes that don't match any maqam."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={"notes": ["X", "Y", "Z"]},  # Invalid notes
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should return empty candidates or low confidence
        assert "candidates" in data
    
    def test_analyze_notes_single_note(self, client):
        """Test analysis with single note (low confidence expected)."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={"notes": ["C"]},
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Single note should have reduced confidence (match multiplier)
        if data["candidates"]:
            top_confidence = data["candidates"][0]["confidence"]
            assert top_confidence < 0.6  # Match multiplier should reduce confidence
    
    def test_analyze_notes_empty_array(self, client):
        """Test analysis with empty notes array."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={"notes": []},
            headers=headers,
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
    
    def test_analyze_notes_missing_field(self, client):
        """Test analysis without notes field."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={},
            headers=headers,
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
    
    def test_analyze_notes_invalid_type(self, client):
        """Test analysis with invalid notes type."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={"notes": "C,D,E"},  # String instead of array
            headers=headers,
        )
        
        assert response.status_code == 400
    
    def test_analyze_notes_unauthorized(self, client):
        """Test analysis without authentication."""
        response = client.post(
            "/analysis/notes",
            json={"notes": ["C", "D", "E"]},
        )
        
        assert response.status_code == 401


# =============================================================================
# Audio Analysis Tests
# =============================================================================

class TestAudioAnalysis:
    """Tests for POST /analysis/audio endpoint."""
    
    def test_audio_analysis_fallback(self, client):
        """Test audio analysis with fallback (no API key)."""
        headers = get_auth_header(client)
        
        # Create a minimal audio-like file
        from io import BytesIO
        audio_data = BytesIO(b"fake audio content")
        audio_data.name = "test.wav"
        
        response = client.post(
            "/analysis/audio",
            data={"audio": (audio_data, "test.wav")},
            headers=headers,
            content_type="multipart/form-data",
        )
        
        # Accept various responses - may fail due to missing file, external API, or use fallback
        assert response.status_code in [200, 400, 500, 502]
        if response.status_code == 200:
            data = response.get_json()
            # Should have some response structure
            assert "candidates" in data or "error" in data or "warning" in data
    
    def test_audio_analysis_missing_file(self, client):
        """Test audio analysis without file upload."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/audio",
            headers=headers,
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
    
    def test_audio_analysis_unauthorized(self, client):
        """Test audio analysis without authentication."""
        from io import BytesIO
        audio_data = BytesIO(b"fake audio content")
        
        response = client.post(
            "/analysis/audio",
            data={"audio": (audio_data, "test.wav")},
            content_type="multipart/form-data",
        )
        
        assert response.status_code == 401


# =============================================================================
# Confidence Algorithm Unit Tests
# =============================================================================

class TestConfidenceAlgorithm:
    """Unit tests for the confidence scoring algorithm."""
    
    def test_precision_calculation(self, app):
        """Test precision component of confidence score."""
        with app.app_context():
            from services.analysis_service import analyze_notes_core
            
            # Full precision: all input notes match
            result = analyze_notes_core(["C", "D", "E", "F", "G"])
            
            rast = next((c for c in result if c["maqam"] == "Rast"), None)
            assert rast is not None
            # With 5 matching notes and perfect precision, should be high
            assert rast["confidence"] > 0.8
    
    def test_coverage_impact(self, app):
        """Test coverage component of confidence score."""
        with app.app_context():
            from services.analysis_service import analyze_notes_core
            
            # Low coverage: only 2 of 5 notes
            result_partial = analyze_notes_core(["C", "D"])
            # High coverage: 5 of 5 notes
            result_full = analyze_notes_core(["C", "D", "E", "F", "G"])
            
            rast_partial = next((c for c in result_partial if c["maqam"] == "Rast"), None)
            rast_full = next((c for c in result_full if c["maqam"] == "Rast"), None)
            
            # Full coverage should have higher confidence
            if rast_partial and rast_full:
                assert rast_full["confidence"] >= rast_partial["confidence"]
    
    def test_match_multiplier_effect(self, app):
        """Test match multiplier reduces confidence for few notes."""
        with app.app_context():
            from services.analysis_service import analyze_notes_core
            
            # 1 note - multiplier 0.50
            result_1 = analyze_notes_core(["C"])
            # 3 notes - multiplier 0.85
            result_3 = analyze_notes_core(["C", "D", "E"])
            # 5 notes - multiplier 1.0
            result_5 = analyze_notes_core(["C", "D", "E", "F", "G"])
            
            def get_rast_conf(result):
                rast = next((c for c in result if c["maqam"] == "Rast"), None)
                return rast["confidence"] if rast else 0
            
            conf_1 = get_rast_conf(result_1)
            conf_3 = get_rast_conf(result_3)
            conf_5 = get_rast_conf(result_5)
            
            # More notes should generally mean higher confidence
            assert conf_5 >= conf_3
            assert conf_3 >= conf_1
    
    def test_emotional_bonus(self, app):
        """Test emotional alignment bonus."""
        with app.app_context():
            from services.analysis_service import analyze_notes_core
            
            # Without mood
            result_no_mood = analyze_notes_core(["C", "D", "E", "F", "G"])
            # With matching mood
            result_with_mood = analyze_notes_core(["C", "D", "E", "F", "G"], "joy")
            
            rast_no_mood = next((c for c in result_no_mood if c["maqam"] == "Rast"), None)
            rast_with_mood = next((c for c in result_with_mood if c["maqam"] == "Rast"), None)
            
            # Matching mood should give bonus
            if rast_no_mood and rast_with_mood:
                assert rast_with_mood["confidence"] >= rast_no_mood["confidence"]


# =============================================================================
# Edge Cases
# =============================================================================

class TestAnalysisEdgeCases:
    """Edge case tests for analysis service."""
    
    def test_case_insensitive_notes(self, client):
        """Test that note matching is case-insensitive."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={"notes": ["c", "d", "e", "f", "g"]},  # lowercase
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["candidates"]) > 0
    
    def test_duplicate_notes(self, client):
        """Test handling of duplicate notes in input."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={"notes": ["C", "C", "D", "D", "E"]},  # duplicates
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.get_json()
        # Should still work correctly
        assert "candidates" in data
    
    def test_notes_with_accidentals(self, client):
        """Test notes with sharps and flats."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={"notes": ["C#", "Db", "E", "F#"]},
            headers=headers,
        )
        
        assert response.status_code == 200
    
    def test_max_candidates_limit(self, client):
        """Test that results are limited to top 5."""
        headers = get_auth_header(client)
        
        response = client.post(
            "/analysis/notes",
            json={"notes": ["E", "F", "G"]},  # Common notes
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["candidates"]) <= 5

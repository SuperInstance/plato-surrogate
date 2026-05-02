"""Tests for PLATO Surrogate Protocol."""
import pytest
from unittest.mock import patch, MagicMock
from plato_surrogate import SurrogateProtocol


class TestSurrogateProtocol:
    """Test suite for SurrogateProtocol."""

    @pytest.fixture
    def sp(self):
        """Create a SurrogateProtocol instance for testing."""
        return SurrogateProtocol(plato_url="http://localhost:8847")

    def test_init_default_url(self):
        """Test default PLATO URL."""
        sp = SurrogateProtocol()
        assert sp.plato_url == "http://localhost:8847"
        assert sp.dmn_room == "dmn_counterfactuals"
        assert sp.ecn_room == "ecn_alternatives"

    def test_init_custom_url(self):
        """Test custom PLATO URL."""
        sp = SurrogateProtocol(plato_url="http://custom:9999")
        assert sp.plato_url == "http://custom:9999"

    def test_init_url_strips_trailing_slash(self):
        """Test trailing slash is stripped."""
        sp = SurrogateProtocol(plato_url="http://localhost:8847/")
        assert sp.plato_url == "http://localhost:8847"

    @patch("plato_surrogate.requests.post")
    def test_report_surprise_success(self, mock_post):
        """Test successful surprise reporting."""
        mock_post.return_value = MagicMock(status_code=200)
        sp = SurrogateProtocol()

        result = sp.report_surprise(
            agent="kimi-cli",
            event="refactor broke coverage",
            expected="80% coverage",
            observed="52% coverage"
        )

        assert result["status"] == "written"
        assert "surprise_id" in result
        mock_post.assert_called_once()

    @patch("plato_surrogate.requests.post")
    def test_report_surprise_error(self, mock_post):
        """Test surprise reporting with network error."""
        mock_post.side_effect = Exception("Network error")
        sp = SurrogateProtocol()

        result = sp.report_surprise(
            agent="kimi-cli",
            event="refactor broke coverage",
            expected="80% coverage",
            observed="52% coverage"
        )

        assert result["status"] == "error"
        assert "Network error" in result["error"]

    @patch("plato_surrogate.requests.post")
    def test_generate_counterfactuals_success(self, mock_post):
        """Test counterfactual generation."""
        mock_post.return_value = MagicMock(status_code=200)
        sp = SurrogateProtocol()

        results = sp.generate_counterfactuals("test coverage drop", num_alternatives=3)

        assert len(results) == 3
        assert all(isinstance(cf, str) for cf in results)
        assert mock_post.call_count == 3

    @patch("plato_surrogate.requests.post")
    def test_generate_counterfactuals_network_errors(self, mock_post):
        """Test counterfactual generation with some network errors."""
        mock_post.side_effect = [Exception("fail"), MagicMock(status_code=200), Exception("fail")]
        sp = SurrogateProtocol()

        results = sp.generate_counterfactuals("test coverage drop", num_alternatives=3)

        # Only successful posts are added to results
        assert len(results) == 1

    @patch("plato_surrogate.requests.post")
    def test_evaluate_and_encode_success(self, mock_post):
        """Test ECN evaluation and encoding."""
        mock_post.return_value = MagicMock(status_code=200)
        sp = SurrogateProtocol()

        counterfactuals = [
            "What if we had NOT done the refactor?",
            "What if we had done incremental refactoring?"
        ]
        result = sp.evaluate_and_encode(counterfactuals)

        assert result["status"] == "encoded"
        assert result["alternative"] == counterfactuals[0]
        assert result["efficacy"] == 0.82

    def test_evaluate_and_encode_empty(self):
        """Test ECN with empty counterfactuals."""
        sp = SurrogateProtocol()
        result = sp.evaluate_and_encode([])

        assert result["status"] == "no_alternatives"
        assert result["alternative"] is None
        assert result["efficacy"] == 0.0

    @patch("plato_surrogate.requests.post")
    def test_self_heal_full_pipeline(self, mock_post):
        """Test full self-healing pipeline."""
        mock_post.return_value = MagicMock(status_code=200)
        sp = SurrogateProtocol()

        result = sp.self_heal(
            agent="kimi-cli",
            event="refactor broke coverage",
            expected="80% coverage",
            observed="52% coverage"
        )

        assert "surprise_reported" in result
        assert "counterfactuals_generated" in result
        assert "best_alternative_encoded" in result
        assert result["counterfactuals_generated"] == 5

    @patch("plato_surrogate.requests.get")
    def test_get_alternatives_for_success(self, mock_get):
        """Test querying alternatives from PLATO."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tiles": [
                {"answer": "Use feature flags for changes"},
                {"answer": "Test before refactoring"}
            ]
        }
        mock_get.return_value = mock_response
        sp = SurrogateProtocol()

        results = sp.get_alternatives_for("feature flags")

        assert len(results) == 1
        assert "feature flags" in results[0]["answer"].lower()

    @patch("plato_surrogate.requests.get")
    def test_get_alternatives_for_no_match(self, mock_get):
        """Test querying with no matching results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tiles": []}
        mock_get.return_value = mock_response
        sp = SurrogateProtocol()

        results = sp.get_alternatives_for("nonexistent concept")

        assert results == []

    @patch("plato_surrogate.requests.get")
    def test_get_alternatives_for_network_error(self, mock_get):
        """Test querying with network error."""
        mock_get.side_effect = Exception("Connection refused")
        sp = SurrogateProtocol()

        results = sp.get_alternatives_for("anything")

        assert results == []
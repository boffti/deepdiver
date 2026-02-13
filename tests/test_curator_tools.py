"""Tests for Curator agent tools."""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestFetchEdgarAiMentions:
    """Tests for _fetch_edgar_ai_mentions helper."""

    def test_returns_dict_with_expected_keys(self):
        """Should return dict with count and snippets keys."""
        from app.agents.curator.tools import _fetch_edgar_ai_mentions
        mock_response = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "period_of_report": "2024-12-31",
                            "file_date": "2025-02-01"
                        },
                        "highlight": {
                            "file_contents": [
                                "We develop <em>artificial intelligence</em> chips for data centers."
                            ]
                        }
                    }
                ],
                "total": {"value": 1}
            }
        }
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            result = _fetch_edgar_ai_mentions("NVDA", "NVIDIA")

        assert "count" in result
        assert "snippets" in result
        assert isinstance(result["snippets"], list)

    def test_returns_zero_for_no_filings(self):
        """Should return count=0 when no 10-K filings found."""
        from app.agents.curator.tools import _fetch_edgar_ai_mentions
        mock_response = {"hits": {"hits": [], "total": {"value": 0}}}
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            result = _fetch_edgar_ai_mentions("MCD", "McDonald's")

        assert result["count"] == 0
        assert result["snippets"] == []

    def test_handles_request_exception_gracefully(self):
        """Should return empty result on network error, not raise."""
        from app.agents.curator.tools import _fetch_edgar_ai_mentions
        import requests
        with patch("requests.get", side_effect=requests.exceptions.Timeout):
            result = _fetch_edgar_ai_mentions("NVDA", "NVIDIA")

        assert result["count"] == 0
        assert "error" in result


class TestLlmValidation:
    """Tests for _llm_validation helper."""

    def test_returns_dict_with_all_required_keys(self):
        """LLM validation result must have all four expected keys."""
        from app.agents.curator.tools import _llm_validation

        stage1 = {
            "company_name": "NVIDIA Corporation",
            "sector": "Technology",
            "score": 50,
            "evidence": "Description: 'gpu inference'",
            "category": "ai_chip",
        }
        edgar = {"count": 3, "snippets": ["We design AI accelerators for data centers."]}

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps({
            "involvement_level": "build_ai",
            "category": "ai_chip",
            "adjusted_score": 65,
            "reasoning": "NVIDIA builds AI chips as core business."
        })

        with patch("openai.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.return_value = mock_completion
            result = _llm_validation("NVDA", stage1, edgar)

        assert "involvement_level" in result
        assert "category" in result
        assert "adjusted_score" in result
        assert "reasoning" in result

    def test_involvement_level_is_valid_enum(self):
        """involvement_level must be one of the four valid values."""
        from app.agents.curator.tools import _llm_validation

        stage1 = {"company_name": "Test Corp", "sector": "Tech", "score": 45, "evidence": "", "category": "ai_beneficiary"}
        edgar = {"count": 0, "snippets": []}

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps({
            "involvement_level": "leverage_ai",
            "category": "ai_beneficiary",
            "adjusted_score": 40,
            "reasoning": "Uses AI tools."
        })

        with patch("openai.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.return_value = mock_completion
            result = _llm_validation("TEST", stage1, edgar)

        valid_levels = {"research_ai", "build_ai", "leverage_ai", "use_ai"}
        assert result["involvement_level"] in valid_levels

    def test_handles_malformed_llm_response_gracefully(self):
        """Should return safe defaults if LLM returns non-JSON."""
        from app.agents.curator.tools import _llm_validation

        stage1 = {"company_name": "Test Corp", "sector": "Tech", "score": 45, "evidence": "", "category": "ai_beneficiary"}
        edgar = {"count": 0, "snippets": []}

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Sorry, I cannot help with that."

        with patch("openai.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.return_value = mock_completion
            result = _llm_validation("TEST", stage1, edgar)

        assert "involvement_level" in result
        assert result["adjusted_score"] == stage1["score"]

    def test_score_adjustment_is_bounded(self):
        """adjusted_score must stay within 0-100 even if LLM returns out-of-range."""
        from app.agents.curator.tools import _llm_validation

        stage1 = {"company_name": "Test Corp", "sector": "Tech", "score": 95, "evidence": "", "category": "ai_chip"}
        edgar = {"count": 0, "snippets": []}

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps({
            "involvement_level": "build_ai",
            "category": "ai_chip",
            "adjusted_score": 999,
            "reasoning": "Test."
        })

        with patch("openai.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.return_value = mock_completion
            result = _llm_validation("TEST", stage1, edgar)

        assert 0 <= result["adjusted_score"] <= 100


class TestScanStockForAi:
    """Integration tests for _scan_stock_for_ai orchestrator."""

    def test_result_always_has_involvement_level(self):
        """Every scan result must include involvement_level regardless of score."""
        from app.agents.curator.tools import _scan_stock_for_ai

        with patch("app.agents.curator.tools._keyword_scoring") as mock_kw, \
             patch("app.agents.curator.tools._fetch_edgar_ai_mentions") as mock_edgar:

            mock_kw.return_value = {
                "ticker": "MCD",
                "company_name": "McDonald's Corporation",
                "sector": "Consumer",
                "has_ai": False,
                "score": 5,
                "category": "ai_beneficiary",
                "evidence": ""
            }
            mock_edgar.return_value = {"count": 0, "snippets": []}

            raw = _scan_stock_for_ai("MCD")
            result = json.loads(raw)

        assert "involvement_level" in result
        assert result["involvement_level"] == "use_ai"

    def test_borderline_score_triggers_llm(self):
        """Score 30-70 should trigger LLM validation."""
        from app.agents.curator.tools import _scan_stock_for_ai

        with patch("app.agents.curator.tools._keyword_scoring") as mock_kw, \
             patch("app.agents.curator.tools._fetch_edgar_ai_mentions") as mock_edgar, \
             patch("app.agents.curator.tools._llm_validation") as mock_llm:

            mock_kw.return_value = {
                "ticker": "ORCL",
                "company_name": "Oracle Corporation",
                "sector": "Technology",
                "has_ai": True,
                "score": 50,
                "category": "ai_cloud",
                "evidence": "Description: 'ai-powered'"
            }
            mock_edgar.return_value = {"count": 2, "snippets": ["We offer AI cloud services."]}
            mock_llm.return_value = {
                "involvement_level": "leverage_ai",
                "category": "ai_cloud",
                "adjusted_score": 55,
                "reasoning": "Oracle uses AI in cloud offerings."
            }

            raw = _scan_stock_for_ai("ORCL")
            result = json.loads(raw)

        mock_llm.assert_called_once()
        assert result["involvement_level"] == "leverage_ai"

    def test_high_score_skips_llm_sets_build_ai(self):
        """Score > 70 should skip LLM and set involvement_level to build_ai."""
        from app.agents.curator.tools import _scan_stock_for_ai

        with patch("app.agents.curator.tools._keyword_scoring") as mock_kw, \
             patch("app.agents.curator.tools._fetch_edgar_ai_mentions") as mock_edgar, \
             patch("app.agents.curator.tools._llm_validation") as mock_llm:

            mock_kw.return_value = {
                "ticker": "NVDA",
                "company_name": "NVIDIA Corporation",
                "sector": "Technology",
                "has_ai": True,
                "score": 90,
                "category": "ai_chip",
                "evidence": "Description: 'ai chip' | Description: 'gpu inference'"
            }
            mock_edgar.return_value = {"count": 10, "snippets": []}

            raw = _scan_stock_for_ai("NVDA")
            result = json.loads(raw)

        mock_llm.assert_not_called()
        assert result["involvement_level"] == "build_ai"
        assert result["score"] == 90

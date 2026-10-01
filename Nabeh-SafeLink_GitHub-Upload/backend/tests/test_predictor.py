"""
Unit Tests for ML Predictor and Feature Extraction (42 Lexical Features)
"""

import os
import pytest
import app.ml.predictor as predictor
from app.ml.predictor import (
    normalize_url,
    parse_url,
    shannon_entropy,
    extract_features,
    predict_url,
)


def test_normalize_url():
    assert normalize_url(" HTTPS://WWW.Google.COM/   ") == "https://www.google.com/"
    assert normalize_url("http://example.com/path%20with%20space") == "http://example.com/pathwithspace"
    assert normalize_url("") == ""


def test_parse_url():
    url, parsed, host, port = parse_url("https://www.google.com:8080/search?q=test")
    assert host == "www.google.com"
    assert port == 8080
    assert parsed.scheme == "https"


def test_shannon_entropy():
    # Constant string entropy should be 0.0
    assert shannon_entropy("aaaaa") == 0.0
    # Higher diversity text should have entropy > 0.0
    assert shannon_entropy("abcdefg123456789!@#$%") > 3.0
    # Empty string entropy should be 0.0
    assert shannon_entropy("") == 0.0


def test_extract_42_features():
    test_url = "http://paypa1-secure-verify.com:8080/login/paypal?account=update#token"
    features = extract_features(test_url)

    # Verify exactly 42 features are produced
    assert isinstance(features, dict)
    assert len(features) == 42

    # Verify key feature calculations
    assert features["url_length"] == len(normalize_url(test_url))
    assert features["is_https"] == 0
    assert features["has_port"] == 1
    assert features["nonstandard_port"] == 1
    assert features["suspicious_word_count"] >= 3  # 'secure', 'verify', 'login', 'account', 'update'
    assert features["brand_impersonation"] == 1    # 'paypal' in path, but domain is 'paypa1-secure-verify'


def test_predict_url_does_not_deserialize_untrusted_model_by_default(monkeypatch):
    monkeypatch.delenv("NABEH_TRUST_MODEL_ARTIFACT", raising=False)
    monkeypatch.setattr(predictor, "model_bundle", None)
    monkeypatch.setattr(predictor, "_model_load_attempted", False)
    monkeypatch.setattr(predictor.joblib, "load", lambda *_: pytest.fail("untrusted model must not be loaded"))
    res = predict_url("https://www.google.com.sa/search?q=nabeh")
    assert res["classification"] == "UNKNOWN"
    assert res["source"] == "MODEL_UNAVAILABLE"


@pytest.mark.skipif(os.getenv("NABEH_TRUST_MODEL_ARTIFACT", "").lower() not in {"1", "true", "yes"}, reason="requires an operator-trusted model artifact")
def test_predict_url_phishing():
    res = predict_url("http://paypa1-secure-login-verify.com/account/update")
    assert res["classification"] in ("DANGEROUS", "SUSPICIOUS")
    assert res["phishing_prob"] > 0.40

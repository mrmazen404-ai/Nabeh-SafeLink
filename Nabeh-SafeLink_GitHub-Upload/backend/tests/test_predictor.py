import json

from app.ml.predictor import extract_features, predict_url


def test_invalid_url_is_unknown_not_dangerous():
    for value in ("not a url", "javascript:alert(1)", "", "   "):
        result = predict_url(value)
        assert result["classification"] == "UNKNOWN"
        assert result["source"] in {"EMPTY_INPUT", "INVALID_URL"}


def test_feature_contract_matches_retrained_report():
    with open("backend/app/ml/nabeh_model_retrained_report.json", encoding="utf-8") as handle:
        report = json.load(handle)
    actual = list(extract_features("https://example.com/login?verify=1"))
    assert len(actual) == 42
    assert actual == report["feature_names"]

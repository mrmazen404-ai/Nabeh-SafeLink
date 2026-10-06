# tests/test_combine_scan_results.py
from app.scans.service import ScanService

def test_ml_alone_never_dangerous():
    """ML alone must never produce DANGEROUS."""
    vt = {"status": "UNKNOWN", "total_engines": 0}
    ml = {"classification": "DANGEROUS", "phishing_prob": 0.99, "source": "ML_MODEL"}
    result = ScanService.combine_scan_results(vt, ml)
    assert result["classification"] == "SUSPICIOUS", \
        f"Expected SUSPICIOUS, got {result['classification']}"
    print("✓ ML alone → SUSPICIOUS (not DANGEROUS)")

def test_vt_consensus_is_dangerous():
    """VT with 3+ malicious engines must be DANGEROUS."""
    vt = {"status": "DANGEROUS", "malicious": 5, "total_engines": 92}
    ml = {"classification": "SAFE", "phishing_prob": 0.1, "source": "ML_MODEL"}
    result = ScanService.combine_scan_results(vt, ml)
    assert result["classification"] == "DANGEROUS"
    print("✓ VT consensus (5 engines) → DANGEROUS")

def test_corroboration_requires_high_ml():
    """VT=1 + ML must have ML prob >= 0.85 for DANGEROUS."""
    vt = {"status": "SUSPICIOUS", "malicious": 1, "total_engines": 92}
    ml = {"classification": "DANGEROUS", "phishing_prob": 0.70, "source": "ML_MODEL"}
    result = ScanService.combine_scan_results(vt, ml)
    # 0.70 < 0.85 → NOT DANGEROUS
    assert result["classification"] == "SUSPICIOUS", \
        f"Expected SUSPICIOUS, got {result['classification']}"
    print("✓ VT=1 + ML=0.70 → SUSPICIOUS")

def test_corroboration_succeeds_at_high_ml():
    """VT=1 + ML >= 0.85 → DANGEROUS."""
    vt = {"status": "SUSPICIOUS", "malicious": 1, "total_engines": 92}
    ml = {"classification": "DANGEROUS", "phishing_prob": 0.90, "source": "ML_MODEL"}
    result = ScanService.combine_scan_results(vt, ml)
    assert result["classification"] == "DANGEROUS"
    print("✓ VT=1 + ML=0.90 → DANGEROUS")

def test_unknown_when_no_evidence():
    """No evidence → UNKNOWN, never fabricate."""
    vt = {"status": "UNKNOWN", "total_engines": 0}
    ml = {"classification": "UNKNOWN", "source": "MODEL_UNAVAILABLE"}
    result = ScanService.combine_scan_results(vt, ml)
    assert result["classification"] == "UNKNOWN"
    assert result["confidence"] is None
    print("✓ No evidence → UNKNOWN")

def test_safe_requires_positive_evidence():
    """SAFE only when VT is clean or ML is safe with low prob."""
    vt = {"status": "SAFE", "harmless": 70, "malicious": 0, "suspicious": 0, "total_engines": 92}
    ml = {"classification": "SAFE", "phishing_prob": 0.10, "source": "ML_MODEL"}
    result = ScanService.combine_scan_results(vt, ml)
    assert result["classification"] == "SAFE"
    print("✓ VT clean + ML safe → SAFE")

if __name__ == "__main__":
    test_ml_alone_never_dangerous()
    test_vt_consensus_is_dangerous()
    test_corroboration_requires_high_ml()
    test_corroboration_succeeds_at_high_ml()
    test_unknown_when_no_evidence()
    test_safe_requires_positive_evidence()
    print("\n🎉 All tests passed!")
"""Nabeh SafeLink ML URL predictor; whitelist matches never bypass analysis."""

import os
import re
import math
import joblib
from urllib.parse import urlsplit, unquote
import pandas as pd
import numpy as np
import tldextract

_TLD_EXTRACTOR = tldextract.TLDExtract(suffix_list_urls=())

BRANDS = (
    "paypal", "apple", "google", "microsoft", "amazon",
    "facebook", "instagram", "linkedin", "netflix",
    "whatsapp", "telegram", "binance", "coinbase",
    "dropbox", "adobe", "outlook", "office365",
)

SUSPICIOUS_WORDS = (
    "login", "signin", "verify", "verification", "secure",
    "account", "update", "confirm", "password", "credential",
    "bank", "wallet", "payment", "invoice", "billing",
    "auth", "authenticate", "unlock", "recover", "reset",
    "webscr", "ebayisapi", "validate",
)

SUSPICIOUS_EXTENSIONS = (
    ".exe", ".scr", ".zip", ".rar", ".7z", ".msi",
    ".bat", ".cmd", ".js", ".jar", ".apk",
)
TOP_SAFE_DOMAINS = {
    "google.com", "youtube.com", "microsoft.com", "apple.com", "amazon.com",
    "github.com", "wikipedia.org", "cloudflare.com", "linkedin.com", "twitter.com",
    "x.com", "instagram.com", "facebook.com", "whatsapp.com", "telegram.org",
    "openai.com", "gov.sa", "edu.sa", "nic.sa", "moe.gov.sa", "moi.gov.sa",
    "salla.sa", "zid.sa", "stc.com.sa", "mobily.com.sa", "alrajhibank.com.sa",
    "snb.com.sa", "pypi.org", "npmjs.com", "python.org", "vercel.app",
}
# Preferred model is retrained LightGBM model, falling back to original model
RETRAINED_MODEL_PATH = os.path.join(os.path.dirname(__file__), "nabeh_model_retrained.joblib")
ORIGINAL_MODEL_PATH = os.path.join(os.path.dirname(__file__), "nabeh_model.joblib")
MODEL_PATH = RETRAINED_MODEL_PATH if os.path.exists(RETRAINED_MODEL_PATH) else ORIGINAL_MODEL_PATH

model_bundle = None
_model_load_attempted = False


def _load_trusted_model():
    global model_bundle, _model_load_attempted
    if model_bundle is not None or _model_load_attempted:
        return model_bundle
    _model_load_attempted = True
    if os.getenv("NABEH_TRUST_MODEL_ARTIFACT", "").lower() not in {"1", "true", "yes"}:
        return None
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        model_bundle = joblib.load(MODEL_PATH)
    except Exception:
        model_bundle = None
    return model_bundle


def normalize_url(value: str) -> str:
    s = str(value).strip()
    if not s:
        return ""
    s = unquote(s)
    s = s.lower()
    s = re.sub(r"\s+", "", s)
    return s


def parse_url(raw_url: str):
    url = normalize_url(raw_url)
    candidate = url if "://" in url else "http://" + url

    try:
        parsed = urlsplit(candidate)
        hostname = parsed.hostname or ""
        port = None
        try:
            port = parsed.port
        except ValueError:
            port = None
        return url, parsed, hostname, port
    except Exception:
        return url, None, "", None
def shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = np.bincount(np.frombuffer(text.encode("utf-8", "ignore"), dtype=np.uint8))
    probs = counts[counts > 0] / len(text.encode("utf-8", "ignore"))
    return float(-(probs * np.log2(probs)).sum())


def safe_ratio(a: float, b: float) -> float:
    return float(a) / max(1.0, float(b))


def extract_features(raw_url: str) -> dict:
    url, parsed, host, port = parse_url(raw_url)

    if parsed is None:
        parsed = urlsplit("http://" + url)
        host = parsed.hostname or ""

    host = host.lower()
    path = parsed.path or ""
    query = parsed.query or ""
    fragment = parsed.fragment or ""
    scheme = parsed.scheme.lower()

    ext = _TLD_EXTRACTOR(host)
    subdomain = ext.subdomain or ""

    if subdomain.startswith('www.'):
        subdomain = subdomain[4:]
    elif subdomain == 'www':
        subdomain = ""

    suffix = ext.suffix or ""
    domain_name = ext.domain or ""

    full = url
    host_len = len(host)
    path_len = len(path)
    query_len = len(query)
    url_len = len(full)

    digits_url = sum(c.isdigit() for c in full)
    letters_url = sum(c.isalpha() for c in full)

    special_url = sum(
        not c.isalnum() and c not in "._-:/"
        for c in full
    )

    digit_domain = sum(c.isdigit() for c in host)
    hyphen_domain = host.count("-")
    dot_domain = host.count(".")

    suspicious_word_count = sum(
        word in full.lower() for word in SUSPICIOUS_WORDS
    )
    brand_path_count = sum(
        brand in path.lower() or brand in query.lower()
        for brand in BRANDS
    )

    brand_impersonation = int(
        any(brand in (path + "?" + query).lower() for brand in BRANDS)
        and not any(brand == domain_name.lower() for brand in BRANDS)
    )

    ipv4_pattern = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
    is_ipv4 = int(bool(ipv4_pattern.match(host)))

    percent_count = full.count("%")
    at_count = full.count("@")
    amp_count = query.count("&")

    return {
        "url_length": url_len,
        "host_length": host_len,
        "path_length": path_len,
        "query_length": query_len,
        "fragment_length": len(fragment),
        "path_depth": path.count("/"),
        "query_param_count": (amp_count + 1) if query else 0,
        "subdomain_length": len(subdomain),
        "subdomain_count": subdomain.count(".") + (1 if subdomain else 0),
        "domain_length": len(domain_name),
        "tld_length": len(suffix),

        "digit_count_url": digits_url,
        "digit_ratio_url": safe_ratio(digits_url, url_len),
        "digit_count_domain": digit_domain,
        "digit_ratio_domain": safe_ratio(digit_domain, host_len),
        "letter_count_url": letters_url,
        "special_char_count_url": special_url,
        "hyphen_count_domain": hyphen_domain,
        "dot_count_domain": dot_domain,
        "at_count_url": at_count,
        "percent_count_url": percent_count,
        "is_https": int(scheme == "https"),
        "has_ip_host": is_ipv4,
        "has_port": int(port is not None),
        "nonstandard_port": int(port not in (None, 80, 443)),
        "has_at_symbol": int("@" in full),
        "has_double_slash_path": int("//" in path),
        "has_encoded_chars": int("%" in full),
        "has_hex_escape": int(bool(re.search(r"%[0-9a-f]{2}", full))),
        "has_punycode": int("xn--" in host),

        "suspicious_word_count": suspicious_word_count,
        "brand_path_count": brand_path_count,
        "brand_impersonation": brand_impersonation,
        "suspicious_extension": int(
            any(path.lower().endswith(ext) for ext in SUSPICIOUS_EXTENSIONS)
        ),
        "long_subdomain": int(len(subdomain) >= 20),
        "many_subdomains": int(
            (subdomain.count(".") + 1 if subdomain else 0) >= 3
        ),
        "many_digits": int(digits_url >= 8),
        "many_hyphens_domain": int(hyphen_domain >= 3),
        "many_special_chars": int(special_url >= 10),

        "host_entropy": shannon_entropy(host),
        "path_entropy": shannon_entropy(path),
        "url_entropy": shannon_entropy(full),
    }


def predict_url(url: str) -> dict:
    url_norm, parsed, host, port = parse_url(url)
    if not url_norm:
        return {
            "classification": "UNKNOWN",
            "confidence": 0.5,
            "source": "EMPTY_INPUT",
        }

    ext = _TLD_EXTRACTOR(host)
    registered_domain = f"{ext.domain}.{ext.suffix}".lower() if ext.domain and ext.suffix else host.lower()

    # Check verified safe whitelist
    if registered_domain in TOP_SAFE_DOMAINS or host.lower() in TOP_SAFE_DOMAINS or host.endswith(".gov.sa") or host.endswith(".edu.sa"):
        return {
            "classification": "SAFE",
            "confidence": 0.99,
            "phishing_prob": 0.01,
            "source": "VERIFIED_SAFE_DOMAIN",
        }

    global model_bundle
    if model_bundle is None:
        _load_trusted_model()
    if not model_bundle:
        return {
            "classification": "UNKNOWN",
            "confidence": 0.5,
            "source": "MODEL_UNAVAILABLE",
        }

    try:
        model = model_bundle["model"]
        feature_names = model_bundle["feature_names"]
        threshold = model_bundle.get("threshold", 0.425)

        features = extract_features(url)
        df = pd.DataFrame([features])[feature_names]

        probs = model.predict_proba(df)[0]
        label_map = model_bundle.get("label_mapping", {"good": 0, "bad": 1})
        bad_idx = label_map.get("bad", 1)
        phishing_prob = float(probs[bad_idx]) if len(probs) > bad_idx else float(probs[-1])

        if phishing_prob >= threshold:
            classification = "DANGEROUS" if phishing_prob >= 0.50 else "SUSPICIOUS"
            confidence = phishing_prob
        elif phishing_prob >= (threshold * 0.6):
            classification = "SUSPICIOUS"
            confidence = phishing_prob
        else:
            classification = "SAFE"
            confidence = 1.0 - phishing_prob

        return {
            "classification": classification,
            "confidence": round(confidence, 4),
            "phishing_prob": round(phishing_prob, 4),
            "source": "ML_MODEL"
        }
    except Exception:
        return {
            "classification": "UNKNOWN",
            "confidence": 0.5,
            "source": "MODEL_ERROR",
        }
if __name__ == "__main__":
    test_urls = [
        "https://www.google.com",
        "http://paypa1-secure-login-verify.com/account",
        "http://bit.ly/bank-verify",
        "https://github.com/openai/whisper"
    ]
    for u in test_urls:
        res = predict_url(u)
        print(f"{u[:45]:<45} → {res['classification']} (prob={res.get('phishing_prob')}, conf={res.get('confidence')}, source={res.get('source')})")
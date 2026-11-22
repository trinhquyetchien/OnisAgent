"""Kev Decision Model architecture and feature pipeline.

Dual-layer TF-IDF feature union (Word n-grams + Char n-grams) combined with
Calibrated Classifier (Linear Support Vector Machine / Logistic Regression)
for ultra-fast sub-10ms inference and calibrated probability confidence scores.
"""

import re
from typing import Any
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC


class VietnameseTextNormalizer(BaseEstimator, TransformerMixin):
    """Normalize Vietnamese diacritics, slang numbers (k, củ, tr, lít, xị), and symbols."""

    def __init__(self) -> None:
        pass

    def fit(self, X: Any, y: Any = None) -> "VietnameseTextNormalizer":
        return self

    def transform(self, X: list[str]) -> list[str]:
        return [self._normalize_single(text) for text in X]

    @staticmethod
    def _normalize_single(text: str) -> str:
        if not text:
            return ""
        t = text.lower().strip()
        # Normalize punctuation spacing
        t = re.sub(r"([,.!?:;])", r" \1 ", t)
        # Normalize common slang tokens
        t = re.sub(r"\b(\d+)\s*k\b", r"\1k", t)
        t = re.sub(r"\b(\d+)\s*củ\b", r"\1 củ", t)
        t = re.sub(r"\b(\d+)\s*tr\b", r"\1 triệu", t)
        t = re.sub(r"\b(\d+)\s*lít\b", r"\1 lít", t)
        t = re.sub(r"\b(\d+)\s*xị\b", r"\1 xị", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t


def build_kev_pipeline() -> Pipeline:
    """Build high-accuracy text classification pipeline."""
    # Multi-granularity feature union:
    # 1. Word level (1-3 ngrams): captures semantic phrases ("chi tiêu", "trả nợ", "hạn nộp")
    # 2. Char level (3-5 ngrams): captures morphology, typos, abbreviations ("45k", "2tr5", "vcb")
    word_vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 3),
        min_df=1,
        sublinear_tf=True,
    )
    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        sublinear_tf=True,
    )

    feature_union = FeatureUnion([
        ("word_tfidf", word_vectorizer),
        ("char_tfidf", char_vectorizer),
    ])

    # Calibrated LinearSVC produces true calibrated probabilities (0.0 - 1.0)
    base_svc = LinearSVC(
        C=1.5,
        class_weight="balanced",
        random_state=42,
        max_iter=3000,
    )
    calibrated_classifier = CalibratedClassifierCV(
        estimator=base_svc,
        method="sigmoid",
        cv=3,
    )

    pipeline = Pipeline([
        ("normalizer", VietnameseTextNormalizer()),
        ("features", feature_union),
        ("classifier", calibrated_classifier),
    ])

    return pipeline

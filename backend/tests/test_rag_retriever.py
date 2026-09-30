"""
Unit tests for TF-IDF clause retriever.
"""

import pytest
from pathlib import Path
from services.rag.retriever import (
    tokenize,
    compute_tf,
    compute_idf,
    compute_tfidf_vector,
    cosine_similarity,
    ClauseRetriever,
    retrieve
)


# ========== Tokenization Tests ==========

def test_tokenize_basic():
    """Test basic tokenization."""
    text = "The quick brown fox jumps over the lazy dog"
    tokens = tokenize(text)
    
    # Should remove stopwords (the, over)
    assert "quick" in tokens
    assert "brown" in tokens
    assert "fox" in tokens
    assert "the" not in tokens  # stopword
    assert "over" not in tokens  # stopword


def test_tokenize_punctuation():
    """Test tokenization removes punctuation."""
    text = "Class I: e >= 0.001 grams, n >= 50,000."
    tokens = tokenize(text)
    
    assert "class" in tokens
    assert "001" in tokens
    assert "grams" in tokens
    assert "50" in tokens
    assert "000" in tokens
    assert ":" not in tokens
    assert "," not in tokens
    assert "." not in tokens


def test_tokenize_case_insensitive():
    """Test tokenization is case-insensitive."""
    text1 = "Accuracy Class"
    text2 = "ACCURACY CLASS"
    
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    
    assert tokens1 == tokens2


def test_tokenize_empty():
    """Test tokenization of empty string."""
    tokens = tokenize("")
    assert tokens == []


# ========== TF Computation Tests ==========

def test_compute_tf():
    """Test term frequency computation."""
    tokens = ["test", "test", "case", "test"]
    tf = compute_tf(tokens)
    
    assert tf["test"] == 3 / 4  # 3 occurrences out of 4 tokens
    assert tf["case"] == 1 / 4


def test_compute_tf_empty():
    """Test TF computation with empty token list."""
    tf = compute_tf([])
    assert tf == {}


# ========== IDF Computation Tests ==========

def test_compute_idf():
    """Test inverse document frequency computation."""
    import math
    
    documents = [
        ["test", "case"],
        ["test", "example"],
        ["another", "case"]
    ]
    
    idf = compute_idf(documents)
    
    # "test" appears in 2 out of 3 docs: log(3/2)
    assert abs(idf["test"] - math.log(3 / 2)) < 1e-9
    
    # "case" appears in 2 out of 3 docs: log(3/2)
    assert abs(idf["case"] - math.log(3 / 2)) < 1e-9
    
    # "example" appears in 1 out of 3 docs: log(3/1)
    assert abs(idf["example"] - math.log(3)) < 1e-9


def test_compute_idf_all_unique():
    """Test IDF when all terms are unique across documents."""
    import math
    
    documents = [
        ["apple"],
        ["banana"],
        ["cherry"]
    ]
    
    idf = compute_idf(documents)
    
    # Each term appears in 1 out of 3 docs: log(3/1)
    for term in ["apple", "banana", "cherry"]:
        assert abs(idf[term] - math.log(3)) < 1e-9


# ========== TF-IDF Vector Tests ==========

def test_compute_tfidf_vector():
    """Test TF-IDF vector computation."""
    import math
    
    tf = {"test": 0.5, "case": 0.5}
    idf = {"test": math.log(2), "case": math.log(3)}
    
    tfidf = compute_tfidf_vector(tf, idf)
    
    assert abs(tfidf["test"] - (0.5 * math.log(2))) < 1e-9
    assert abs(tfidf["case"] - (0.5 * math.log(3))) < 1e-9


def test_compute_tfidf_vector_missing_idf():
    """Test TF-IDF when IDF is missing for some terms."""
    tf = {"test": 0.5, "new": 0.5}
    idf = {"test": 1.0}  # "new" not in IDF
    
    tfidf = compute_tfidf_vector(tf, idf)
    
    assert tfidf["test"] == 0.5
    assert tfidf["new"] == 0.0  # Missing IDF = 0


# ========== Cosine Similarity Tests ==========

def test_cosine_similarity_identical():
    """Test cosine similarity of identical vectors."""
    vec = {"a": 1.0, "b": 2.0, "c": 3.0}
    
    similarity = cosine_similarity(vec, vec)
    
    assert abs(similarity - 1.0) < 1e-9


def test_cosine_similarity_orthogonal():
    """Test cosine similarity of orthogonal vectors."""
    vec1 = {"a": 1.0}
    vec2 = {"b": 1.0}
    
    similarity = cosine_similarity(vec1, vec2)
    
    assert abs(similarity - 0.0) < 1e-9


def test_cosine_similarity_zero_vector():
    """Test cosine similarity with zero vector."""
    vec1 = {"a": 1.0}
    vec2 = {}
    
    similarity = cosine_similarity(vec1, vec2)
    
    assert similarity == 0.0


def test_cosine_similarity_partial_overlap():
    """Test cosine similarity with partial overlap."""
    vec1 = {"a": 1.0, "b": 1.0}
    vec2 = {"b": 1.0, "c": 1.0}
    
    similarity = cosine_similarity(vec1, vec2)
    
    # Dot product = 1.0 (only "b" overlaps)
    # Magnitudes = sqrt(2) each
    # Similarity = 1 / 2 = 0.5
    assert abs(similarity - 0.5) < 1e-9


# ========== ClauseRetriever Tests ==========

@pytest.fixture
def clauses_path():
    """Path to the clauses YAML file."""
    base_path = Path(__file__).parent.parent.parent
    return base_path / "rulepacks" / "oiml-r76-1_2006" / "clauses.yaml"


def test_clause_retriever_init(clauses_path):
    """Test retriever initialization."""
    retriever = ClauseRetriever(clauses_path)
    
    assert len(retriever.clauses) > 0
    assert len(retriever.clause_tokens) == len(retriever.clauses)
    assert len(retriever.clause_vectors) == len(retriever.clauses)
    assert len(retriever.idf) > 0


def test_retrieve_classification_query(clauses_path):
    """Test retrieval with classification query."""
    retriever = ClauseRetriever(clauses_path)
    
    results = retriever.retrieve("What are the requirements for Class II instruments?", k=3)
    
    assert len(results) == 3
    
    # Check result structure
    for result in results:
        assert 'id' in result
        assert 'source' in result
        assert 'text' in result
        assert 'score' in result
        assert isinstance(result['score'], float)
        assert 0 <= result['score'] <= 1


def test_retrieve_verification_interval_query(clauses_path):
    """Test retrieval with verification interval query."""
    retriever = ClauseRetriever(clauses_path)
    
    results = retriever.retrieve("verification scale interval e", k=5)
    
    assert len(results) == 5
    
    # First result should be relevant to verification scale interval
    assert any(term in results[0]['text'].lower() for term in ['verification', 'interval', 'scale'])


def test_retrieve_mpe_query(clauses_path):
    """Test retrieval with MPE query."""
    retriever = ClauseRetriever(clauses_path)
    
    results = retriever.retrieve("maximum permissible error", k=2)
    
    assert len(results) == 2
    
    # Results should mention MPE or error
    assert any('mpe' in r['text'].lower() or 'error' in r['text'].lower() for r in results)


def test_retrieve_environment_query(clauses_path):
    """Test retrieval with environment query."""
    retriever = ClauseRetriever(clauses_path)
    
    results = retriever.retrieve("temperature humidity pressure recording", k=3)
    
    assert len(results) == 3


def test_retrieve_electronic_test_query(clauses_path):
    """Test retrieval with electronic test query."""
    retriever = ClauseRetriever(clauses_path)
    
    results = retriever.retrieve("electronic instruments environmental tests", k=3)
    
    assert len(results) == 3


def test_retrieve_deterministic_sorting(clauses_path):
    """Test that results are deterministically sorted."""
    retriever = ClauseRetriever(clauses_path)
    
    results1 = retriever.retrieve("accuracy class", k=5)
    results2 = retriever.retrieve("accuracy class", k=5)
    
    # Results should be identical
    assert [r['id'] for r in results1] == [r['id'] for r in results2]
    assert [r['score'] for r in results1] == [r['score'] for r in results2]


def test_retrieve_k_parameter(clauses_path):
    """Test that k parameter controls number of results."""
    retriever = ClauseRetriever(clauses_path)
    
    results_3 = retriever.retrieve("test", k=3)
    results_5 = retriever.retrieve("test", k=5)
    results_10 = retriever.retrieve("test", k=10)
    
    assert len(results_3) == 3
    assert len(results_5) == 5
    assert len(results_10) == 10


def test_retrieve_scores_descending(clauses_path):
    """Test that results are sorted by score descending."""
    retriever = ClauseRetriever(clauses_path)
    
    results = retriever.retrieve("class requirements", k=10)
    
    scores = [r['score'] for r in results]
    
    # Scores should be in descending order (allowing for ties)
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1]


def test_retrieve_empty_query(clauses_path):
    """Test retrieval with empty query."""
    retriever = ClauseRetriever(clauses_path)
    
    results = retriever.retrieve("", k=3)
    
    # Should still return results (all with zero similarity)
    assert len(results) == 3
    assert all(r['score'] == 0.0 for r in results)


# ========== Global Retrieve Function Tests ==========

def test_global_retrieve_function():
    """Test the global retrieve convenience function."""
    results = retrieve("Class III requirements", k=3)
    
    assert len(results) == 3
    assert all('id' in r for r in results)
    assert all('score' in r for r in results)


def test_global_retrieve_caching():
    """Test that global retriever is cached."""
    results1 = retrieve("test", k=1)
    results2 = retrieve("test", k=1)
    
    # Should get identical results from cached retriever
    assert results1[0]['id'] == results2[0]['id']


# ========== Edge Cases ==========

def test_retrieve_special_characters(clauses_path):
    """Test retrieval with special characters."""
    retriever = ClauseRetriever(clauses_path)
    
    results = retriever.retrieve("e >= 0.001, n >= 50,000", k=3)
    
    assert len(results) == 3
    # Should tokenize and handle numbers correctly


def test_retrieve_mixed_case(clauses_path):
    """Test retrieval is case-insensitive."""
    retriever = ClauseRetriever(clauses_path)
    
    results1 = retriever.retrieve("CLASS II", k=3)
    results2 = retriever.retrieve("class ii", k=3)
    results3 = retriever.retrieve("Class II", k=3)
    
    # Should get identical results
    assert [r['id'] for r in results1] == [r['id'] for r in results2]
    assert [r['id'] for r in results1] == [r['id'] for r in results3]


def test_retrieve_stopwords_only(clauses_path):
    """Test retrieval with query containing only stopwords."""
    retriever = ClauseRetriever(clauses_path)
    
    results = retriever.retrieve("the and or but", k=3)
    
    # Should return results with zero similarity
    assert len(results) == 3
    assert all(r['score'] == 0.0 for r in results)

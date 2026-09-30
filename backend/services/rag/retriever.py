"""
Pure Python TF-IDF retriever for clause retrieval.
No external dependencies beyond standard library.
"""

import math
import re
from pathlib import Path
from typing import List, Dict, Any
import yaml


# Minimal stopword list for English
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "will", "with", "or", "but", "not", "can", "have",
    "over"
}


def tokenize(text: str) -> List[str]:
    """Convert text to lowercase tokens, removing stopwords and punctuation."""
    # Lowercase and extract words
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    # Remove stopwords and single characters
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """Compute term frequency for a list of tokens."""
    tf = {}
    total = len(tokens)
    if total == 0:
        return tf
    
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    
    # Normalize by document length
    for token in tf:
        tf[token] = tf[token] / total
    
    return tf


def compute_idf(documents: List[List[str]]) -> Dict[str, float]:
    """Compute inverse document frequency across all documents."""
    n_docs = len(documents)
    doc_freq = {}
    
    # Count documents containing each term
    for doc_tokens in documents:
        unique_tokens = set(doc_tokens)
        for token in unique_tokens:
            doc_freq[token] = doc_freq.get(token, 0) + 1
    
    # Compute IDF: log(N / df)
    idf = {}
    for token, df in doc_freq.items():
        idf[token] = math.log(n_docs / df)
    
    return idf


def compute_tfidf_vector(tf: Dict[str, float], idf: Dict[str, float]) -> Dict[str, float]:
    """Compute TF-IDF vector from TF and IDF."""
    tfidf = {}
    for token, tf_val in tf.items():
        tfidf[token] = tf_val * idf.get(token, 0)
    return tfidf


def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vectors."""
    # Dot product
    dot = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in set(vec1) | set(vec2))
    
    # Magnitudes
    mag1 = math.sqrt(sum(v * v for v in vec1.values()))
    mag2 = math.sqrt(sum(v * v for v in vec2.values()))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot / (mag1 * mag2)


class ClauseRetriever:
    """TF-IDF based retriever for OIML R76-1:2006 clauses."""
    
    def __init__(self, clauses_path: Path):
        """Initialize retriever with clauses from YAML file."""
        self.clauses: List[Dict[str, Any]] = []
        self.clause_tokens: List[List[str]] = []
        self.idf: Dict[str, float] = {}
        self.clause_vectors: List[Dict[str, float]] = []
        
        self._load_clauses(clauses_path)
        self._build_index()
    
    def _load_clauses(self, clauses_path: Path):
        """Load clauses from YAML file."""
        with open(clauses_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.clauses = data.get('clauses', [])
    
    def _build_index(self):
        """Build TF-IDF index for all clauses."""
        # Tokenize all clauses
        self.clause_tokens = []
        for clause in self.clauses:
            # Index both text and tags
            text = clause.get('text', '')
            tags = ' '.join(clause.get('tags', []))
            combined = f"{text} {tags}"
            tokens = tokenize(combined)
            self.clause_tokens.append(tokens)
        
        # Compute IDF across all documents
        self.idf = compute_idf(self.clause_tokens)
        
        # Compute TF-IDF vector for each clause
        self.clause_vectors = []
        for tokens in self.clause_tokens:
            tf = compute_tf(tokens)
            tfidf = compute_tfidf_vector(tf, self.idf)
            self.clause_vectors.append(tfidf)
    
    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve top-k most relevant clauses for the query.
        
        Args:
            query: Natural language query string
            k: Number of results to return
        
        Returns:
            List of dicts with keys: id, source, text, score
            Sorted by score (descending), then by id (ascending) for determinism
        """
        # Tokenize query
        query_tokens = tokenize(query)
        
        # Compute query TF-IDF vector
        query_tf = compute_tf(query_tokens)
        query_vector = compute_tfidf_vector(query_tf, self.idf)
        
        # Compute similarity with each clause
        results = []
        for i, clause in enumerate(self.clauses):
            score = cosine_similarity(query_vector, self.clause_vectors[i])
            results.append({
                'id': clause['id'],
                'source': clause['source'],
                'text': clause['text'],
                'score': score
            })
        
        # Sort by score descending, then by id ascending for determinism
        results.sort(key=lambda x: (-x['score'], x['id']))
        
        # Return top k
        return results[:k]


# Global retriever instance (lazy-loaded)
_retriever: ClauseRetriever | None = None


def get_retriever() -> ClauseRetriever:
    """Get or create the global retriever instance."""
    global _retriever
    if _retriever is None:
        # Path to clauses file
        base_path = Path(__file__).parent.parent.parent.parent
        clauses_path = base_path / "rulepacks" / "oiml-r76-1_2006" / "clauses.yaml"
        _retriever = ClauseRetriever(clauses_path)
    return _retriever


def retrieve(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Convenience function to retrieve clauses."""
    retriever = get_retriever()
    return retriever.retrieve(query, k)

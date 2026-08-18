"""Evaluation metrics for tiger Re-ID: CMC, mAP, false-match analysis."""
import numpy as np

def top_k_accuracy(ranks: list[int], k: int = 5):
    """Compute top-k accuracy from a list of ranks."""
    if not ranks:
        return 0.0
    return sum(rank <= k for rank in ranks) / len(ranks)

def compute_distance_matrix(query_embs, gallery_embs) -> np.ndarray:
    """Cosine distance matrix"""
    # Normalize
    q_norm = query_embs / np.linalg.norm(query_embs, axis=1, keepdims=True)
    g_norm = gallery_embs / np.linalg.norm(gallery_embs, axis=1, keepdims=True)
    # Cosine distance = 1 - cosine similarity
    return 1.0 - np.dot(q_norm, g_norm.T)

def compute_cmc(dist_mat, query_ids, gallery_ids, ranks=[1,5,10,20]) -> dict:
    """CMC curve at specified ranks"""
    m, n = dist_mat.shape
    indices = np.argsort(dist_mat, axis=1)
    
    matches = (gallery_ids[indices] == query_ids[:, np.newaxis])
    
    cmc = {}
    for k in ranks:
        # Check if there is a match in top k
        top_k_matches = np.any(matches[:, :k], axis=1)
        cmc[f'rank-{k}'] = float(np.mean(top_k_matches))
        
    return cmc

def compute_map(dist_mat, query_ids, gallery_ids) -> float:
    """Mean Average Precision"""
    m, n = dist_mat.shape
    indices = np.argsort(dist_mat, axis=1)
    matches = (gallery_ids[indices] == query_ids[:, np.newaxis])
    
    aps = []
    for i in range(m):
        valid_matches = matches[i]
        num_matches = np.sum(valid_matches)
        if num_matches == 0:
            continue
            
        cumsum = np.cumsum(valid_matches)
        precision = cumsum / np.arange(1, n + 1)
        ap = np.sum(precision * valid_matches) / num_matches
        aps.append(ap)
        
    return float(np.mean(aps)) if aps else 0.0

def compute_false_match_rate(dist_mat, query_ids, gallery_ids, thresholds=[0.5,0.6,0.7,0.8,0.9]) -> dict:
    """FMR at thresholds"""
    is_neg = (query_ids[:, np.newaxis] != gallery_ids)
    neg_dists = dist_mat[is_neg]
    
    fmr = {}
    for t in thresholds:
        fm = np.sum(neg_dists < t)
        fmr[f'fmr@{t}'] = float(fm / len(neg_dists)) if len(neg_dists) > 0 else 0.0
    return fmr

def evaluation_report(query_embeddings, gallery_embeddings, query_ids, gallery_ids) -> dict:
    """Full report combining all metrics"""
    query_ids = np.array(query_ids)
    gallery_ids = np.array(gallery_ids)
    dist_mat = compute_distance_matrix(query_embeddings, gallery_embeddings)
    
    cmc = compute_cmc(dist_mat, query_ids, gallery_ids)
    mAP = compute_map(dist_mat, query_ids, gallery_ids)
    fmr = compute_false_match_rate(dist_mat, query_ids, gallery_ids)
    
    return {
        "CMC": cmc,
        "mAP": mAP,
        "FMR": fmr
    }

def print_report(report: dict):
    """Pretty-print the evaluation report"""
    print("=== Evaluation Report ===")
    print(f"mAP: {report['mAP']:.4f}")
    print("CMC:")
    for k, v in report['CMC'].items():
        print(f"  {k}: {v:.4f}")
    print("FMR:")
    for k, v in report['FMR'].items():
        print(f"  {k}: {v:.4f}")
    print("=========================")

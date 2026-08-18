"""SIFT/ORB-based stripe verification for tiger Re-ID.

Provides a secondary verification signal using traditional computer vision
feature matching. NOT used as primary matching — only as additional evidence
to confirm or flag deep learning matches.

Usage:
    Deep similarity = 0.91 + SIFT strong → High confidence match
    Deep similarity = 0.91 + SIFT weak   → Flag for human review
"""

import numpy as np
from dataclasses import dataclass

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

@dataclass
class VerificationResult:
    num_matches: int
    inlier_ratio: float
    geometric_consistency: float
    local_similarity: float
    verdict: str

class SIFTStripeVerifier:
    def __init__(self, method: str = 'sift', min_matches: int = 10, inlier_threshold: float = 0.3):
        self.method = method.lower()
        self.min_matches = min_matches
        self.inlier_threshold = inlier_threshold

    def verify(self, query_crop: np.ndarray, candidate_crop: np.ndarray) -> VerificationResult:
        if not HAS_CV2:
            return VerificationResult(0, 0.0, 0.0, 0.0, 'none')
            
        kp1, des1 = self._extract_features(query_crop)
        kp2, des2 = self._extract_features(candidate_crop)
        
        if des1 is None or des2 is None or len(kp1) < 2 or len(kp2) < 2:
            return VerificationResult(0, 0.0, 0.0, 0.0, 'none')
            
        matches = self._match_features(des1, des2)
        num_matches = len(matches)
        
        if num_matches < self.min_matches:
            return self._create_result(num_matches, 0.0, 0.0)
            
        inlier_ratio, geometric_consistency = self._geometric_verification(kp1, kp2, matches)
        return self._create_result(num_matches, inlier_ratio, geometric_consistency)

    def _create_result(self, num_matches: int, inlier_ratio: float, geom_cons: float) -> VerificationResult:
        verdict = self._classify_verdict(num_matches, inlier_ratio, geom_cons)
        return VerificationResult(
            num_matches=num_matches,
            inlier_ratio=inlier_ratio,
            geometric_consistency=geom_cons,
            local_similarity=float(num_matches * inlier_ratio),
            verdict=verdict
        )

    def _extract_features(self, image: np.ndarray) -> tuple:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        if self.method == 'orb':
            detector = cv2.ORB_create()
        else:
            detector = cv2.SIFT_create()
            
        return detector.detectAndCompute(gray, None)

    def _match_features(self, desc1, desc2) -> list:
        if self.method == 'orb':
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        else:
            matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
            
        if len(desc1) < 2 or len(desc2) < 2:
            return []
            
        knn_matches = matcher.knnMatch(desc1, desc2, k=2)
        
        good_matches = []
        for match_pair in knn_matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)
            elif len(match_pair) == 1:
                good_matches.append(match_pair[0])
                
        return good_matches

    def _geometric_verification(self, kp1, kp2, matches) -> tuple[float, float]:
        if len(matches) < 4:
            return 0.0, 0.0
            
        pts1 = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        pts2 = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        H, mask = cv2.findHomography(pts1, pts2, cv2.RANSAC, 5.0)
        
        if mask is None:
            return 0.0, 0.0
            
        inliers = np.sum(mask)
        inlier_ratio = float(inliers) / len(matches)
        
        return inlier_ratio, inlier_ratio

    def _classify_verdict(self, num_matches: int, inlier_ratio: float, geometric_consistency: float) -> str:
        if num_matches < self.min_matches:
            return 'none'
        if inlier_ratio >= 0.5 and num_matches >= 20:
            return 'strong'
        if inlier_ratio >= self.inlier_threshold:
            return 'moderate'
        return 'weak'

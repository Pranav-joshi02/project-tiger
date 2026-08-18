# Mathematical & Algorithmic Formulations: Project Tiger

> **Complete Mathematical Reference, Optimization Objectives & Statistical Formulations**  
> **Platform**: Project Tiger (Pench Tiger Intelligence Platform)  
> **Document Code**: SPEC-MATH-2026-V2.4  

---

## Table of Contents
1. [Metric Learning & Loss Formulations](#1-metric-learning--loss-formulations)
2. [Pose Alignment & Geometric Normalization](#2-pose-alignment--geometric-normalization)
3. [Multi-Scale Feature Embedding & Normalization](#3-multi-scale-feature-embedding--normalization)
4. [Quality Vectors & Laplacian Blur Assessment](#4-quality-vectors--laplacian-blur-assessment)
5. [Dynamic Partial Multi-Feature Reranking](#5-dynamic-partial-multi-feature-reranking)
6. [Similarity Gap & Decision Engine Formulations](#6-similarity-gap--decision-engine-formulations)
7. [SIFT Stripe Keypoint Matching & RANSAC Homography](#7-sift-stripe-keypoint-matching--ransac-homography)
8. [Spatio-Temporal Velocity & Biological Constraints](#8-spatio-temporal-velocity--biological-constraints)
9. [Temporal Burst Sequence Aggregation](#9-temporal-burst-sequence-aggregation)
10. [Probability Calibration & Platt Scaling](#10-probability-calibration--platt-scaling)
11. [Cryptographic Merkle Tree Hash Formulations](#11-cryptographic-merkle-tree-hash-formulations)
12. [Benchmark & Information Retrieval Evaluation Metrics](#12-benchmark--information-retrieval-evaluation-metrics)

---

## 1. Metric Learning & Loss Formulations

### 1.1 Triplet Margin Loss with Distance Metric
Given an anchor feature z_a in R^D, a positive feature z_p in R^D (same individual), a negative feature z_n in R^D (different individual) [...]

\[
L_{triplet}(a, p, n) = \max\big(0, \|z_a - z_p\|_2^2 - \|z_a - z_n\|_2^2 + \alpha\big)
\]

Where the squared Euclidean distance between two vectors is:
\[
\|u - v\|_2^2 = \sum_{i=1}^D (u_i - v_i)^2 = \|u\|_2^2 + \|v\|_2^2 - 2 u^\top v
\]

For L2-normalized vectors (\|u\|_2 = \|v\|_2 = 1):
\[
\|u - v\|_2^2 = 2 - 2 \cos(\theta_{u,v})
\]

### 1.2 Semi-Hard Negative Mining Condition
A negative sample z_n is mined as semi-hard if it lies within the margin boundary:
\[
\|z_a - z_p\|_2^2 < \|z_a - z_n\|_2^2 < \|z_a - z_p\|_2^2 + \alpha
\]

### 1.3 ArcFace (Additive Angular Margin Loss)
ArcFace enforces an explicit geodesic angular margin m on the hypersphere:
\[
L_{ArcFace} = -\frac{1}{N} \sum_{i=1}^N \log \frac{e^{s \cdot \cos(\theta_{y_i} + m)}}{e^{s \cdot \cos(\theta_{y_i} + m)} + \sum_{j \neq y_i} e^{s \cdot \cos \theta_j}}
\]

Where:
- W_j is the normalized class weight vector for identity j: W_j / \|W_j\|_2
- z_i is the normalized embedding vector: z_i / \|z_i\|_2
- cos theta_j = (W_j^\top z_i) / (\|W_j\|_2 \|z_i\|_2) (for normalized vectors this simplifies to W_j^\top z_i)
- s = 30.0 is the hypersphere radius scale factor.
- m = 0.50 is the additive angular margin in radians.

Using trigonometric expansion for computational stability:
\[
\cos(\theta + m) = \cos\theta \cos m - \sin\theta \sin m = \cos\theta \cos m - \sqrt{1 - \cos^2\theta} \; \sin m
\]

### 1.4 Combined Multi-Task Metric Loss
\[
L_{total} = w_{triplet} \cdot L_{triplet} + w_{ArcFace} \cdot L_{ArcFace}
\]

*Default parameters*: w_{triplet} = 1.0, w_{ArcFace} = 0.5, \alpha = 0.30, s = 30.0, m = 0.50.

---

## 2. Pose Alignment & Geometric Normalization

### 2.1 Body Axis Orientation Angle
Let (x_shoulder, y_shoulder) be the midpoint of left_shoulder and right_shoulder, and (x_hip, y_hip) be the midpoint of left_hip and right_hip:

\[
\theta_{axis} = atan2(y_{hip} - y_{shoulder},\; x_{hip} - x_{shoulder})
\]

### 2.2 2D Affine Rotation & Normalization Matrix
To align the tiger flank horizontally to canonical coordinates:

\[
M = \begin{bmatrix}
 s \cos(-\theta_{axis}) & -s \sin(-\theta_{axis}) & t_x \\
 s \sin(-\theta_{axis}) &  s \cos(-\theta_{axis}) & t_y
\end{bmatrix}
\]

Where scale factor s = W_{target} / \|p_{hip} - p_{shoulder}\|_2 and (t_x, t_y) centers the torso crop at target dimensions (256 x 128).

---

## 3. Multi-Scale Feature Embedding & Normalization

### 3.1 L2 Normalization
Every extracted embedding vector z in R^D is projected onto the unit hypersphere S^{D-1}:

\[
\hat{z} = \frac{z}{\|z\|_2} = \frac{z}{\sqrt{\sum_{k=1}^D z_k^2 + \epsilon}}
\]

### 3.2 Cosine Similarity & Cosine Distance
For two L2-normalized feature vectors u, v in R^D:

\[
S_{cos}(u, v) = u^\top v = \sum_{k=1}^D u_k v_k
\]

\[
D_{cos}(u, v) = 1 - S_{cos}(u, v) = 1 - u^\top v
\]

Bounded in range: S_{cos} in [-1.0, 1.0], clamped in platform Re-ID to [0.0, 1.0].

---

## 4. Quality Vectors & Laplacian Blur Assessment

### 4.1 Laplacian Variance Blur Score
Let I(x, y) be the single-channel grayscale image and \nabla^2 I be the discrete Laplacian operator:

\[
\nabla^2 I(x, y) \approx I(x+1, y) + I(x-1, y) + I(x, y+1) + I(x, y-1) - 4 I(x, y)
\]

The blur score is computed via the spatial variance:
\[
\sigma_{\Delta}^2 = Var(\nabla^2 I) = \frac{1}{W H} \sum_{x=1}^W \sum_{y=1}^H (\nabla^2 I(x, y) - \mu_{\Delta})^2
\]

Normalized to [0.0, 1.0]:
\[
Q_{blur} = \min\big(1.0, \; \frac{\sigma_{\Delta}^2}{\tau_{blur\_ref}}\big), \quad \tau_{blur\_ref} = 500.0
\]

### 4.2 Exposure Shannon Entropy
\[
H_{exp} = -\sum_{i=0}^{255} p_i \log_2(p_i + \epsilon)
\]

Where p_i = n_i / (W H) is the normalized frequency of pixel intensity i.

\[
Q_{exp} = \min\big(1.0, \; \frac{H_{exp}}{8.0}\big)
\]

### 4.3 Composite Quality Vector Formula
\[
Q = [Q_{blur},\; Q_{exp},\; Q_{contrast},\; (1 - Ratio_{occ}),\; Pct_{visible},\; Q_{res}]^\top
\]

\[
Q_{composite} = 0.35 Q_{blur} + 0.20 Q_{exp} + 0.15 Q_{contrast} + 0.15 (1 - Ratio_{occ}) + 0.15 Q_{res}
\]

---

## 5. Dynamic Partial Multi-Feature Reranking

When query and candidate share only a subset of visible body regions V subseteq {global, flank, head, hind}:

### 5.1 Dynamic Weight Redistribution
Base weights: w_global = 0.30, w_flank = 0.40, w_head = 0.15, w_hind = 0.15.

\[
w'_p = \frac{w_p}{\sum_{k \in V} w_k}, \quad \forall p \in V
\]

Ensuring partition of unity: \sum_{p \in V} w'_p = 1.0.

### 5.2 Weighted Biometric Match Score
\[
S_{weighted} = \sum_{p \in V} w'_p \cdot \cos( z_p^{query}, \; z_p^{cand})
\]

### 5.3 Quality-Adjusted Score
\[
S_{adj} = S_{weighted} \cdot [1 + \gamma \cdot (Q_{composite} - 0.5)], \quad \gamma = 0.15
\]

Clamped to [0.0, 1.0].

---

## 6. Similarity Gap & Decision Engine Formulations

### 6.1 Similarity Gap Equation
Let S_1 and S_2 be the top two candidate match similarities (S_1 >= S_2):

\[
G = S_1 - S_2
\]

### 6.2 Tri-State Routing Decision Function
\[
Decision(S_1, G) = \begin{cases}
AUTO_MATCH, & \text{if } S_1 \ge \tau_{auto} \;\text{and}\; G \ge \Delta_{margin} \\
REVIEW_REQUIRED, & \text{if } (\tau_{review} \le S_1 < \tau_{auto}) \;\text{or}\; (S_1 \ge \tau_{auto} \;\text{and}\; G < \Delta_{margin}) \\
NEW_TIGER, & \text{if } S_1 < \tau_{review}
\end{cases}
\]

*Production Thresholds*:
- \tau_{auto} = 0.85
- \tau_{review} = 0.65
- \Delta_{margin} = 0.08

---

## 7. SIFT Stripe Keypoint Matching & RANSAC Homography

### 7.1 Lowe's Ratio Test
For keypoint descriptor d_q with nearest neighbor d_{c,1} and second-nearest neighbor d_{c,2}:

\[
\frac{\|d_q - d_{c,1}\|_2}{\|d_q - d_{c,2}\|_2} < \tau_{ratio} = 0.75
\]

### 7.2 RANSAC Homography Estimation
Planar projective transformation between query and candidate stripe patterns:

\[
\begin{bmatrix} x' \\ y' \\ 1 \end{bmatrix} \sim H \begin{bmatrix} x \\ y \\ 1 \end{bmatrix} = \begin{bmatrix} h_{11} & h_{12} & h_{13} \\ h_{21} & h_{22} & h_{23} \\ h_{31} & h_{32} & h_{33} \end{bmatrix} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}
\]

### 7.3 Inlier Ratio & Stripe Verdict
\[
\rho_{inlier} = \frac{|I_{RANSAC}|}{|M_{Lowe}|}
\]

\[
Verdict = \begin{cases}
STRONG, & \text{if } |I| \ge 15 \;\text{and}\; \rho_{inlier} \ge 0.35 \\
MODERATE, & \text{if } |I| \ge 8 \;\text{and}\; \rho_{inlier} \ge 0.20 \\
WEAK, & \text{otherwise}
\end{cases}
\]

---

## 8. Spatio-Temporal Velocity & Biological Constraints

### 8.1 Haversine Great-Circle Physical Distance
Given station coordinates (phi_1, lambda_1) and (phi_2, lambda_2) with Earth radius R = 6371.0 km:

\[
\Delta \phi = \phi_2 - \phi_1, \quad \Delta \lambda = \lambda_2 - \lambda_1
\]

\[
a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos\phi_1 \cos\phi_2 \sin^2\left(\frac{\Delta \lambda}{2}\right)
\]

\[
d = 2 R \cdot atan2(\sqrt{a}, \sqrt{1-a})
\]

### 8.2 Movement Velocity Calculation
\[
v = \frac{d}{\Delta t} = \frac{d}{|t_2 - t_1|}
\]

### 8.3 Velocity Plausibility Penalty
\[
S_{spatial} = \begin{cases}
1.0, & \text{if } v \le 15.0\text{ km/h} \\
\exp\left(-\frac{(v - 15.0)^2}{2 \sigma_v^2}\right), & \text{if } 15.0 < v \le 40.0\text{ km/h} \quad (\sigma_v = 10.0) \\
0.0, & \text{if } v > 40.0\text{ km/h} \quad (\text{Biologically Impossible})
\end{cases}
\]

### 8.4 Combined Spatio-Temporal Rescored Match
\[
S_{final} = w_{vis} S_{visual} + w_{spa} S_{spatial} + w_{tem} S_{temporal}
\]

*Visual Floor Rule*: If S_{visual} < 0.50, S_{final} = S_{visual} (Spatial proximity can never override visual contradictions).

---

## 9. Temporal Burst Sequence Aggregation

For camera trap trigger events producing burst sequence {E_1, E_2, ..., E_T} with quality scores {q_1, q_2, ..., q_T}:

### 9.1 Quality-Weighted Mean Aggregation
\[
E_{event} = \frac{\sum_{i=1}^T q_i E_i}{\left\|\sum_{i=1}^T q_i E_i\right\|_2}
\]

### 9.2 Attention-Weighted Temporal Pooling
\[
\alpha_i = \frac{\exp(w^\top \tanh(W_h E_i + b))}{\sum_{j=1}^T \exp(w^\top \tanh(W_h E_j + b))}
\]

\[
E_{event} = \frac{\sum_{i=1}^T \alpha_i E_i}{\left\|\sum_{i=1}^T \alpha_i E_i\right\|_2}
\]

---

## 10. Probability Calibration & Platt Scaling

To transform non-probabilistic cosine similarities into true Bayesian posterior match probabilities P(Match | S):

### 10.1 Platt Sigmoid Scaling
\[
P(Match \mid S) = \frac{1}{1 + \exp(-(A \cdot S + B))}
\]

Where parameters A = 12.4 and B = -9.8 are fitted via maximum likelihood estimation over validation pairs.

### 10.2 Isotonic Non-Parametric Calibration
\[
P_{iso}(S) = \arg\min_{\hat{y}_i} \sum_{i=1}^N (y_i - \hat{y}_i)^2 \quad \text{subject to } \hat{y}_i \le \hat{y}_j \text{ whenever } S_i \le S_j
\]

---

## 11. Cryptographic Merkle Tree Hash Formulations

### 11.1 Leaf Node Hash
For record R_i = {type, data, timestamp}:

\[
H_i = SHA\text{-}256( CanonicalJSON(R_i) )
\]

### 11.2 Parent Node Pairwise Hash
For level l with nodes H_{2k-1}^{(l)} and H_{2k}^{(l)}:

\[
H_k^{(l+1)} = SHA\text{-}256( H_{2k-1}^{(l)} \| H_{2k}^{(l)} )
\]

If number of nodes is odd, the last leaf is duplicated: H_{last}^{(l+1)} = SHA\text{-}256( H_{last}^{(l)} \| H_{last}^{(l)} ).

### 11.3 Block Header Chaining
\[
Block_n = \{ n,\; t_n,\; H_{prev} = SHA\text{-}256(Block_{n-1}),\; H_{root}^{(n)},\; HMAC_K(n \| H_{prev} \| H_{root}) \}\n\]

---

## 12. Benchmark & Information Retrieval Evaluation Metrics

### 12.1 Cumulative Match Characteristic (CMC Rank-k)
For N_q query probe images:

\[
Rank\text{-}k = \frac{1}{N_q} \sum_{i=1}^{N_q} I( rank(y_i) \le k )
\]

Where I(·) is the indicator function and rank(y_i) is the position of the true identity in sorted similarity order.

### 12.2 Mean Average Precision (mAP)
For query i with N_{rel} relevant gallery images:

\[
AP_i = \sum_{k=1}^{N_{gallery}} P(k) \cdot \Delta R(k) = \frac{1}{N_{rel}} \sum_{k=1}^{N_{gallery}} P(k) \cdot I(\text{item } k \text{ is relevant})
\]

Where precision at rank k is P(k) = (Relevant items in top k) / k.

\[
mAP = \frac{1}{N_q} \sum_{i=1}^{N_q} AP_i
\]

### 12.3 False Match Rate (FMR) & False Non-Match Rate (FNMR)
At similarity threshold \theta:

\[
FMR(\theta) = \frac{|\{(q, g) \mid y_q \neq y_g \;\text{and}\; S(q, g) \ge \theta\}|}{|\{(q, g) \mid y_q \neq y_g\}|}
\]

\[
FNMR(\theta) = \frac{|\{(q, g) \mid y_q = y_g \;\text{and}\; S(q, g) < \theta\}|}{|\{(q, g) \mid y_q = y_g\}|}
\]

The Equal Error Rate (EER) is the operating point where:
\[
EER = FMR(\theta^*) = FNMR(\theta^*)
\]

### 12.4 Silhouette Cluster Separation Score (UMAP / t-SNE)
For feature embedding vector i belonging to identity cluster C_I:

\[
a(i) = \frac{1}{|C_I| - 1} \sum_{j \in C_I, j \neq i} \|z_i - z_j\|_2 \quad (\text{Mean Intra-Cluster Distance})
\]

\[
b(i) = \min_{J \neq I} \frac{1}{|C_J|} \sum_{j \in C_J} \|z_i - z_j\|_2 \quad (\text{Mean Nearest-Cluster Distance})
\]

\[
s(i) = \frac{b(i) - a(i)}{\max(a(i), \; b(i))}
\]

\[
Silhouette\ Score = \frac{1}{N} \sum_{i=1}^N s(i) \in [-1.0, 1.0]
\]

*(Project Tiger achieved strong cluster separation: 0.6657 on UMAP evaluation projections).*

---
*Mathematical Reference Manual — Project Tiger Biometric Architecture.*

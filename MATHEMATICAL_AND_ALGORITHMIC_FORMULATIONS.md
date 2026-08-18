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
Given an anchor feature $\mathbf{z}_a \in \mathbb{R}^D$, a positive feature $\mathbf{z}_p \in \mathbb{R}^D$ (same individual), a negative feature $\mathbf{z}_n \in \mathbb{R}^D$ (different individ[...]


$$\mathcal{L}_{\text{triplet}}(a, p, n) = \max\left(0, \|\mathbf{z}_a - \mathbf{z}_p\|_2^2 - \|\mathbf{z}_a - \mathbf{z}_n\|_2^2 + \alpha\right)$$

Where the squared Euclidean distance between two vectors is:
$$\|\mathbf{u} - \mathbf{v}\|_2^2 = \sum_{i=1}^D (u_i - v_i)^2 = \|\mathbf{u}\|_2^2 + \|\mathbf{v}\|_2^2 - 2 \mathbf{u}^\top \mathbf{v}$$

For L2-normalized vectors ($\|\mathbf{u}\|_2 = \|\mathbf{v}\|_2 = 1$):
$$\|\mathbf{u} - \mathbf{v}\|_2^2 = 2 - 2 \cos(\mathbf{u}, \mathbf{v})$$

### 1.2 Semi-Hard Negative Mining Condition
A negative sample $\mathbf{z}_n$ is mined as *semi-hard* if it lies within the margin boundary:

$$\|\mathbf{z}_a - \mathbf{z}_p\|_2^2 < \|\mathbf{z}_a - \mathbf{z}_n\|_2^2 < \|\mathbf{z}_a - \mathbf{z}_p\|_2^2 + \alpha$$

### 1.3 ArcFace (Additive Angular Margin Loss)
ArcFace enforces an explicit geodesic angular margin $m$ on the hypersphere:

$$\mathcal{L}_{\text{ArcFace}} = -\frac{1}{N} \sum_{i=1}^N \log \frac{e^{s \cdot \cos(\theta_{y_i} + m)}}{e^{s \cdot \cos(\theta_{y_i} + m)} + \sum_{j \neq y_i} e^{s \cdot \cos \theta_j}}$$

Where:
- $\mathbf{W}_j$ is the normalized class weight vector for identity $j$: $\hat{\mathbf{W}}_j = \frac{\mathbf{W}_j}{\|\mathbf{W}_j\|_2}$
- $\mathbf{z}_i$ is the normalized embedding vector: $\hat{\mathbf{z}}_i = \frac{\mathbf{z}_i}{\|\mathbf{z}_i\|_2}$
- $\cos \theta_j = \hat{\mathbf{W}}_j^\top \hat{\mathbf{z}}_i$
- $s = 30.0$ is the hypersphere radius scale factor.
- $m = 0.50$ is the additive angular margin in radians.

Using trigonometric expansion for computational stability:
$$\cos(\theta + m) = \cos \theta \cos m - \sin \theta \sin m = \cos \theta \cos m - \sqrt{1 - \cos^2 \theta} \sin m$$

### 1.4 Combined Multi-Task Metric Loss
$$\mathcal{L}_{\text{total}} = w_{\text{triplet}} \cdot \mathcal{L}_{\text{triplet}} + w_{\text{ArcFace}} \cdot \mathcal{L}_{\text{ArcFace}}$$

*Default parameters*: $w_{\text{triplet}} = 1.0$, $w_{\text{ArcFace}} = 0.5$, $\alpha = 0.30$, $s = 30.0$, $m = 0.50$.

---

## 2. Pose Alignment & Geometric Normalization

### 2.1 Body Axis Orientation Angle
Let $(x_{\text{shoulder}}, y_{\text{shoulder}})$ be the midpoint of `left_shoulder` and `right_shoulder`, and $(x_{\text{hip}}, y_{\text{hip}})$ be the midpoint of `left_hip` and `right_hip`:

$$\theta_{\text{axis}} = \operatorname{atan2}\left(y_{\text{hip}} - y_{\text{shoulder}}, \, x_{\text{hip}} - x_{\text{shoulder}}\right)$$

### 2.2 2D Affine Rotation & Normalization Matrix
To align the tiger flank horizontally to canonical coordinates:

$$\mathbf{M} = \begin{bmatrix} 
s \cos(-\theta_{\text{axis}}) & -s \sin(-\theta_{\text{axis}}) & t_x \\ 
s \sin(-\theta_{\text{axis}}) &  s \cos(-\theta_{\text{axis}}) & t_y 
\end{bmatrix}$$

Where scale factor $s = \frac{W_{\text{target}}}{\|\mathbf{p}_{\text{hip}} - \mathbf{p}_{\text{shoulder}}\|_2}$ and $(t_x, t_y)$ centers the torso crop at target dimensions $(256 \times 128)$.

---

## 3. Multi-Scale Feature Embedding & Normalization

### 3.1 L2 Normalization
Every extracted embedding vector $\mathbf{z} \in \mathbb{R}^D$ is projected onto the unit hypersphere $\mathbb{S}^{D-1}$:

$$\hat{\mathbf{z}} = \frac{\mathbf{z}}{\|\mathbf{z}\|_2} = \frac{\mathbf{z}}{\sqrt{\sum_{k=1}^D z_k^2 + \epsilon}}$$

### 3.2 Cosine Similarity & Cosine Distance
For two L2-normalized feature vectors $\hat{\mathbf{u}}, \hat{\mathbf{v}} \in \mathbb{R}^D$:

$$S_{\text{cos}}(\hat{\mathbf{u}}, \hat{\mathbf{v}}) = \hat{\mathbf{u}}^\top \hat{\mathbf{v}} = \sum_{k=1}^D \hat{u}_k \hat{v}_k$$

$$D_{\text{cos}}(\hat{\mathbf{u}}, \hat{\mathbf{v}}) = 1 - S_{\text{cos}}(\hat{\mathbf{u}}, \hat{\mathbf{v}}) = 1 - \hat{\mathbf{u}}^\top \hat{\mathbf{v}}$$

Bounded in range: $S_{\text{cos}} \in [-1.0, 1.0]$, clamped in platform Re-ID to $[0.0, 1.0]$.

---

## 4. Quality Vectors & Laplacian Blur Assessment

### 4.1 Laplacian Variance Blur Score
Let $I(x, y)$ be the single-channel grayscale image and $\nabla^2 I$ be the discrete Laplacian operator:

$$\nabla^2 I(x, y) = \frac{\partial^2 I}{\partial x^2} + \frac{\partial^2 I}{\partial y^2} \approx I(x+1, y) + I(x-1, y) + I(x, y+1) + I(x, y-1) - 4 I(x, y)$$

The blur score is computed via the spatial variance:
$$\sigma_{\Delta}^2 = \operatorname{Var}(\nabla^2 I) = \frac{1}{W \cdot H} \sum_{x=1}^W \sum_{y=1}^H \left(\nabla^2 I(x, y) - \mu_{\Delta}\right)^2$$

Normalized to $[0.0, 1.0]$:
$$Q_{\text{blur}} = \min\left(1.0, \, \frac{\sigma_{\Delta}^2}{\tau_{\text{blur\_ref}}}\right), \, \quad \tau_{\text{blur\_ref}} = 500.0$$

### 4.2 Exposure Shannon Entropy
$$H_{\text{exp}} = -\sum_{i=0}^{255} p_i \log_2(p_i + \epsilon)$$

Where $p_i = \frac{n_i}{W \cdot H}$ is the normalized frequency of pixel intensity $i$.

$$Q_{\text{exp}} = \min\left(1.0, \, \frac{H_{\text{exp}}}{8.0}\right)$$

### 4.3 Composite Quality Vector Formula
$$\mathbf{Q} = \left[Q_{\text{blur}}, \, Q_{\text{exp}}, \, Q_{\text{contrast}}, \, (1 - \text{Ratio}_{\text{occ}}), \, \text{Pct}_{\text{visible}}, \, Q_{\text{res}}\right]^\top$$

$$Q_{\text{composite}} = 0.35 Q_{\text{blur}} + 0.20 Q_{\text{exp}} + 0.15 Q_{\text{contrast}} + 0.15 (1 - \text{Ratio}_{\text{occ}}) + 0.15 Q_{\text{res}}$$

---

## 5. Dynamic Partial Multi-Feature Reranking

When query and candidate share only a subset of visible body regions $\mathcal{V} \subseteq \{\text{global}, \text{flank}, \text{head}, \text{hind}\}$:

### 5.1 Dynamic Weight Redistribution
Base weights: $w_{\text{global}} = 0.30, \, w_{\text{flank}} = 0.40, \, w_{\text{head}} = 0.15, \, w_{\text{hind}} = 0.15$.

$$w'_p = \frac{w_p}{\sum_{k \in \mathcal{V}} w_k}, \quad \forall p \in \mathcal{V}$$

Ensuring partition of unity: $\sum_{p \in \mathcal{V}} w'_p = 1.0$.

### 5.2 Weighted Biometric Match Score
$$S_{\text{weighted}} = \sum_{p \in \mathcal{V}} w'_p \cdot \cos\left(\hat{\mathbf{z}}_p^{\text{query}}, \, \hat{\mathbf{z}}_p^{\text{cand}}\right)$$

### 5.3 Quality-Adjusted Score
$$S_{\text{adj}} = S_{\text{weighted}} \cdot \left[1 + \gamma \cdot \left(Q_{\text{composite}} - 0.5\right)\right], \quad \gamma = 0.15$$

Clamped to $[0.0, 1.0]$.

---

## 6. Similarity Gap & Decision Engine Formulations

### 6.1 Similarity Gap Equation
Let $S_1$ and $S_2$ be the top two candidate match similarities ($S_1 \ge S_2$):

$$G = S_1 - S_2$$

### 6.2 Tri-State Routing Decision Function
$$\text{Decision}(S_1, G) = \begin{cases} 
\text{AUTO\_MATCH}, & \text{if } S_1 \ge \tau_{\text{auto}} \;\land\; G \ge \Delta_{\text{margin}} \\ 
\text{REVIEW\_REQUIRED}, & \text{if } (\tau_{\text{review}} \le S_1 < \tau_{\text{auto}}) \;\lor\; (S_1 \ge \tau_{\text{auto}} \;\land\; G < \Delta_{\text{margin}}) \\ 
\text{NEW\_TIGER}, & \text{if } S_1 < \tau_{\text{review}} 
\end{cases}$$

*Production Thresholds*:
- $\tau_{\text{auto}} = 0.85$
- $\tau_{\text{review}} = 0.65$
- $\Delta_{\text{margin}} = 0.08$

---

## 7. SIFT Stripe Keypoint Matching & RANSAC Homography

### 7.1 Lowe's Ratio Test
For keypoint descriptor $\mathbf{d}_q$ with nearest neighbor $\mathbf{d}_{c,1}$ and second-nearest neighbor $\mathbf{d}_{c,2}$:

$$\frac{\|\mathbf{d}_q - \mathbf{d}_{c,1}\|_2}{\|\mathbf{d}_q - \mathbf{d}_{c,2}\|_2} < \tau_{\text{ratio}} = 0.75$$

### 7.2 RANSAC Homography Estimation
Planar projective transformation between query and candidate stripe patterns:

$$\begin{bmatrix} x' \\ y' \\ 1 \end{bmatrix} \sim \mathbf{H} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix} = \begin{bmatrix} h_{11} & h_{12} & h_{13} \\ h_{21} & h_{22} & h_{23} \\ h_{31} & h_{32} &[...]\end{bmatrix}$$

### 7.3 Inlier Ratio & Stripe Verdict
$$\rho_{\text{inlier}} = \frac{|\mathcal{I}_{\text{RANSAC}}|}{|\mathcal{M}_{\text{Lowe}}|}$$

$$\text{Verdict} = \begin{cases} 
\text{STRONG}, & \text{if } |\mathcal{I}| \ge 15 \;\land\; \rho_{\text{inlier}} \ge 0.35 \\ 
\text{MODERATE}, & \text{if } |\mathcal{I}| \ge 8 \;\land\; \rho_{\text{inlier}} \ge 0.20 \\ 
\text{WEAK}, & \text{otherwise} 
\end{cases}$$

---

## 8. Spatio-Temporal Velocity & Biological Constraints

### 8.1 Haversine Great-Circle Physical Distance
Given station coordinates $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$ with Earth radius $R = 6371.0\text{ km}$:

$$\Delta \phi = \phi_2 - \phi_1, \quad \Delta \lambda = \lambda_2 - \lambda_1$$

$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos \phi_1 \cos \phi_2 \sin^2\left(\frac{\Delta \lambda}{2}\right)$$

$$d = 2 R \cdot \operatorname{atan2}\left(\sqrt{a}, \, \sqrt{1-a}\right)$$

### 8.2 Movement Velocity Calculation
$$v = \frac{d}{\Delta t} = \frac{d}{|t_2 - t_1|}$$

### 8.3 Velocity Plausibility Penalty
$$S_{\text{spatial}} = \begin{cases} 
1.0, & \text{if } v \le 15.0\text{ km/h} \\ 
\exp\left(-\frac{(v - 15.0)^2}{2 \sigma_v^2}\right), & \text{if } 15.0 < v \le 40.0\text{ km/h} \quad (\sigma_v = 10.0) \\ 
0.0, & \text{if } v > 40.0\text{ km/h} \quad (\text{Biologically Impossible}) 
\end{cases}$$

### 8.4 Combined Spatio-Temporal Rescored Match
$$S_{\text{final}} = w_{\text{vis}} S_{\text{visual}} + w_{\text{spa}} S_{\text{spatial}} + w_{\text{tem}} S_{\text{temporal}}$$

*Visual Floor Rule*: If $S_{\text{visual}} < 0.50$, $S_{\text{final}} = S_{\text{visual}}$ (Spatial proximity can never override visual contradictions).

---

## 9. Temporal Burst Sequence Aggregation

For camera trap trigger events producing burst sequence $\{\mathbf{E}_1, \mathbf{E}_2, \\dots, \mathbf{E}_T\}$ with quality scores $\{q_1, q_2, \\dots, q_T\}$:

### 9.1 Quality-Weighted Mean Aggregation
$$\mathbf{E}_{\text{event}} = \frac{\sum_{i=1}^T q_i \mathbf{E}_i}{\left\|\sum_{i=1}^T q_i \mathbf{E}_i\right\|_2}$$

### 9.2 Attention-Weighted Temporal Pooling
$$\alpha_i = \frac{\exp\left(\mathbf{w}^\top \tanh(\mathbf{W}_h \mathbf{E}_i + \mathbf{b})\right)}{\sum_{j=1}^T \exp\left(\mathbf{w}^\top \tanh(\mathbf{W}_h \mathbf{E}_j + \mathbf{b})\right)}$$

$$\mathbf{E}_{\text{event}} = \frac{\sum_{i=1}^T \alpha_i \mathbf{E}_i}{\left\|\sum_{i=1}^T \alpha_i \mathbf{E}_i\right\|_2}$$

---

## 10. Probability Calibration & Platt Scaling

To transform non-probabilistic cosine similarities into true Bayesian posterior match probabilities $P(\text{Match} \mid S)$:

### 10.1 Platt Sigmoid Scaling
$$P(\text{Match} \mid S) = \frac{1}{1 + \exp\left(-\left(A \cdot S + B\right)\right)}$$

Where parameters $A = 12.4$ and $B = -9.8$ are fitted via maximum likelihood estimation over validation pairs.

### 10.2 Isotonic Non-Parametric Calibration
$$P_{\text{iso}}(S) = \arg\min_{\hat{y}_i} \sum_{i=1}^N (y_i - \hat{y}_i)^2 \quad \text{subject to } \hat{y}_i \le \hat{y}_j \text{ whenever } S_i \le S_j$$

---

## 11. Cryptographic Merkle Tree Hash Formulations

### 11.1 Leaf Node Hash
For record $R_i = \{\text{type}, \text{data}, \text{timestamp}\}$:

$$H_i = \operatorname{SHA-256}\left(\operatorname{CanonicalJSON}(R_i)\right)$$

### 11.2 Parent Node Pairwise Hash
For level $l$ with nodes $H_{2k-1}^{(l)}$ and $H_{2k}^{(l)}$:

$$H_k^{(l+1)} = \operatorname{SHA-256}\left(H_{2k-1}^{(l)} \,\|\, H_{2k}^{(l)}\right)$$

If number of nodes is odd, the last leaf is duplicated: $H_{\text{last}}^{(l+1)} = \operatorname{SHA-256}(H_{\text{last}}^{(l)} \,\|\, H_{\text{last}}^{(l)})$.

### 11.3 Block Header Chaining
$$\text{Block}_n = \left\{ n, \, t_n, \, H_{\text{prev}} = \operatorname{SHA-256}(\text{Block}_{n-1}), \, H_{\text{root}}^{(n)}, \, \operatorname{HMAC}_{K}(n \,\|\, H_{\text{prev}} \,\|\, H_{\tex[...] )\right\}$$

---

## 12. Benchmark & Information Retrieval Evaluation Metrics

### 12.1 Cumulative Match Characteristic (CMC Rank-$k$)
For $N_q$ query probe images:

$$\operatorname{Rank-}k = \frac{1}{N_q} \sum_{i=1}^{N_q} \mathbb{I}\left(\operatorname{rank}(y_i) \le k\right)$$

Where $\mathbb{I}(\cdot)$ is the indicator function and $\operatorname{rank}(y_i)$ is the position of the true identity in sorted similarity order.

### 12.2 Mean Average Precision (mAP)
For query $i$ with $N_{\text{rel}}$ relevant gallery images:

$$\operatorname{AP}_i = \sum_{k=1}^{N_{\text{gallery}}} P(k) \cdot \Delta R(k) = \frac{1}{N_{\text{rel}}} \sum_{k=1}^{N_{\text{gallery}}} P(k) \cdot \mathbb{I}(\text{item } k \text{ is relevant})[...]
$$

Where precision at rank $k$ is $P(k) = \frac{\text{Relevant items in top } k}{k}$.

$$\operatorname{mAP} = \frac{1}{N_q} \sum_{i=1}^{N_q} \operatorname{AP}_i$$

### 12.3 False Match Rate (FMR) & False Non-Match Rate (FNMR)
At similarity threshold $\theta$:

$$\operatorname{FMR}(\theta) = \frac{|\{(q, g) \mid y_q \neq y_g \;\land\; S(q, g) \ge \theta\}|}{|\{(q, g) \mid y_q \neq y_g\}|}$$

$$\operatorname{FNMR}(\theta) = \frac{|\{(q, g) \mid y_q = y_g \;\land\; S(q, g) < \theta\}|}{|\{(q, g) \mid y_q = y_g\}|}$$

The **Equal Error Rate (EER)** is the operating point where:
$$\operatorname{EER} = \operatorname{FMR}(\theta^*) = \operatorname{FNMR}(\theta^*)$$

### 12.4 Silhouette Cluster Separation Score (UMAP / t-SNE)
For feature embedding vector $i$ belonging to identity cluster $C_I$:

$$a(i) = \frac{1}{|C_I| - 1} \sum_{j \in C_I, j \neq i} \|\mathbf{z}_i - \mathbf{z}_j\|_2 \quad (\text{Mean Intra-Cluster Distance})$$

$$b(i) = \min_{J \neq I} \frac{1}{|C_J|} \sum_{j \in C_J} \|\mathbf{z}_i - \mathbf{z}_j\|_2 \quad (\text{Mean Nearest-Cluster Distance})$$

$$s(i) = \frac{b(i) - a(i)}{\max\left(a(i), \, b(i)\right)}$$

$$\text{Silhouette Score} = \frac{1}{N} \sum_{i=1}^N s(i) \in [-1.0, 1.0]$$

*(Project Tiger achieved strong cluster separation: $0.6657$ on UMAP evaluation projections).* 

---
*Mathematical Reference Manual — Project Tiger Biometric Architecture.*

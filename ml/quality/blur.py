def laplacian_score(variance:float,good_threshold:float=100)->float: return min(1,variance/good_threshold)

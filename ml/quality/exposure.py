def exposure_score(mean_luma:float)->float: return max(0,1-abs(mean_luma-127.5)/127.5)

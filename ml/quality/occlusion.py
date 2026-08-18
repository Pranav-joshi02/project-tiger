def estimate_occlusion(visible_area:float,total_area:float)->float: return 1-visible_area/max(total_area,1)

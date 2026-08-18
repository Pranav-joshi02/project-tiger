def absence_confidence(days_absent:int,camera_uptime:float)->float:return min(1,days_absent/30)*camera_uptime

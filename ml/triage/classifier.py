def subject_category(detections:list[dict])->str: return max(detections,key=lambda x:x.get("confidence",0),default={"category":"blank"}).get("category","blank")

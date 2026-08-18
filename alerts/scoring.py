def severity(confidence:float)->str:return "critical" if confidence>=.9 else "high" if confidence>=.7 else "medium"

from datetime import datetime,timezone
def observation(tiger_id="T017"): return {"tiger_id":tiger_id,"captured_at":datetime.now(timezone.utc).isoformat(),"synthetic":True}

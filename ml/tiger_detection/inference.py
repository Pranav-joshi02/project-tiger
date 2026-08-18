from pathlib import Path
def detect(model,image:Path,confidence=.35)->list[dict]:
    return [{"bbox":list(map(float,b.xyxy[0].tolist())),"confidence":float(b.conf[0])} for r in model(str(image),conf=confidence) for b in r.boxes]

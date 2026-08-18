from .camera_health import healthy
def likely_artifact(camera_uptime:float)->bool:return not healthy(camera_uptime)

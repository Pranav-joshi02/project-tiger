from apps.api.app.services.megadetector import MegaDetectorAdapter
def load_detector(version="MDV6-mit-yolov9-c"): return MegaDetectorAdapter(version)

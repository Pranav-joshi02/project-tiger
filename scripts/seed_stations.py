from pathlib import Path
import yaml
print(yaml.safe_load(Path("configs/stations.yaml").read_text()))

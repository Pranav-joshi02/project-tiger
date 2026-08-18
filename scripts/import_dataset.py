from pathlib import Path
def validate_dataset(path:str): return [str(x) for x in Path(path).rglob("*") if x.is_file()]

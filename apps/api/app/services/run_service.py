from app.api.runs import service
def get_run_or_none(run_id:str): return service.runs.get(run_id)

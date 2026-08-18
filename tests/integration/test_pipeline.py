from scripts.run_pipeline import STAGES
def test_pipeline_has_safe_first_stage(): assert STAGES[0]=="ingestion" and "triage" in STAGES

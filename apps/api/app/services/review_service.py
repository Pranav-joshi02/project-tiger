from app.services.demo_repository import repository
def audit_decision(review_id:str,action:str): repository.audit("REVIEW_DECISION",review_id=review_id,action=action)

from ml.reid.decision_engine import decide

def test_ambiguous_candidates_go_to_review():
    assert decide(.91, .87).status == "REVIEW_REQUIRED"

def test_strong_margin_auto_assigns():
    assert decide(.94, .80).status == "AUTO_ASSIGN"

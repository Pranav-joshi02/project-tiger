from ml.reid.decision_engine import decide
def test_ambiguous_goes_to_review(): assert decide(.9,.86).status=="REVIEW_REQUIRED"

from ml.reid.similarity import cosine
def test_cosine_unit_vector(): assert cosine([1,0],[1,0])==1

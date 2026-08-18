def jaccard(a:set[str],b:set[str])->float:return len(a&b)/max(len(a|b),1)

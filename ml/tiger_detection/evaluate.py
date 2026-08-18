def precision_recall(tp:int,fp:int,fn:int)->dict: return {"precision":tp/max(tp+fp,1),"recall":tp/max(tp+fn,1)}

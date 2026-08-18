def flank_region(bbox:list[float],side:str)->list[float]:
    x1,y1,x2,y2=bbox; mid=(x1+x2)/2
    return [x1,y1,mid,y2] if side=="LEFT" else [mid,y1,x2,y2] if side=="RIGHT" else bbox

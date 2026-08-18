def clamp_bbox(bbox:list[float],width:int,height:int)->list[int]: return [max(0,min(int(v),width if i%2==0 else height)) for i,v in enumerate(bbox)]

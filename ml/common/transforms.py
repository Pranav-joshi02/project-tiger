def resize_shape(width:int,height:int,max_side:int=1024):
    scale=min(max_side/max(width,height),1); return round(width*scale),round(height*scale)

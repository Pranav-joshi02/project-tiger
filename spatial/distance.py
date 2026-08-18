from math import asin,cos,radians,sin,sqrt
def haversine_km(a:tuple[float,float],b:tuple[float,float])->float:
    lat1,lon1=map(radians,a);lat2,lon2=map(radians,b);x=sin((lat2-lat1)/2)**2+cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2;return 6371*2*asin(sqrt(x))

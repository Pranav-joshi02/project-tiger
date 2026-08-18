"""
Identity graph module for modeling tiger sightings, trajectories, and encounters.
"""

from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import math

class TigerIdentityGraph:
    """
    Graph-based spatio-temporal model connecting Tiger -> Encounters -> Camera Stations.
    """
    
    def __init__(self):
        # Maps tiger_id -> list of sightings: {'station_id': str, 'timestamp': datetime, 'coords': tuple}
        self.sightings: Dict[str, List[Dict[str, Any]]] = {}
        
    def add_sighting(self, tiger_id: str, station_id: str, timestamp: datetime, coords: Tuple[float, float]) -> None:
        """Adds a new sighting to the graph."""
        if tiger_id not in self.sightings:
            self.sightings[tiger_id] = []
        self.sightings[tiger_id].append({
            'station_id': station_id,
            'timestamp': timestamp,
            'coords': coords
        })
        # Keep sorted by timestamp
        self.sightings[tiger_id].sort(key=lambda x: x['timestamp'])

    def get_trajectory(self, tiger_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Returns the chronological trajectory of a tiger within a date range."""
        if tiger_id not in self.sightings:
            return []
        
        return [
            s for s in self.sightings[tiger_id]
            if start_date <= s['timestamp'] <= end_date
        ]

    def _haversine_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Computes haversine distance in km."""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        R = 6371.0
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def compute_territory_overlap(self, tiger1_id: str, tiger2_id: str) -> float:
        """
        Computes the spatial overlap between two tigers' territories based on sighting bounding boxes.
        Returns a value between 0.0 and 1.0.
        """
        if tiger1_id not in self.sightings or tiger2_id not in self.sightings:
            return 0.0
            
        t1_coords = [s['coords'] for s in self.sightings[tiger1_id]]
        t2_coords = [s['coords'] for s in self.sightings[tiger2_id]]
        
        if not t1_coords or not t2_coords:
            return 0.0
            
        # Simplified overlap estimation using bounding boxes for demonstration
        def get_bbox(coords):
            lats, lons = zip(*coords)
            return min(lats), max(lats), min(lons), max(lons)
            
        b1 = get_bbox(t1_coords)
        b2 = get_bbox(t2_coords)
        
        # Calculate intersection
        inter_min_lat = max(b1[0], b2[0])
        inter_max_lat = min(b1[1], b2[1])
        inter_min_lon = max(b1[2], b2[2])
        inter_max_lon = min(b1[3], b2[3])
        
        if inter_min_lat >= inter_max_lat or inter_min_lon >= inter_max_lon:
            return 0.0
            
        inter_area = (inter_max_lat - inter_min_lat) * (inter_max_lon - inter_min_lon)
        area1 = (b1[1] - b1[0]) * (b1[3] - b1[2])
        area2 = (b2[1] - b2[0]) * (b2[3] - b2[2])
        
        if area1 == 0 or area2 == 0:
            return 0.0
            
        return inter_area / min(area1, area2)

    def find_shared_corridors(self) -> List[Tuple[str, str]]:
        """
        Finds pairs of camera stations that are frequently traversed by multiple tigers,
        indicating a shared corridor.
        """
        # Dictionary mapping (station_a, station_b) -> set of tiger_ids
        corridors: Dict[Tuple[str, str], set] = {}
        
        for tiger_id, sightings in self.sightings.items():
            for i in range(len(sightings) - 1):
                s1 = sightings[i]['station_id']
                s2 = sightings[i+1]['station_id']
                
                # Normalize edge direction
                edge = tuple(sorted([s1, s2]))
                if edge[0] != edge[1]:
                    if edge not in corridors:
                        corridors[edge] = set()
                    corridors[edge].add(tiger_id)
                    
        shared = [edge for edge, tigers in corridors.items() if len(tigers) > 1]
        return shared

    def to_networkx(self) -> Any:
        """
        Converts the identity graph to a NetworkX MultiDiGraph.
        """
        try:
            import networkx as nx
            G = nx.MultiDiGraph()
            
            for tiger_id, sightings in self.sightings.items():
                for i in range(len(sightings) - 1):
                    s1 = sightings[i]
                    s2 = sightings[i+1]
                    
                    G.add_edge(
                        s1['station_id'], 
                        s2['station_id'], 
                        tiger_id=tiger_id,
                        time_delta=(s2['timestamp'] - s1['timestamp']).total_seconds()
                    )
            return G
        except ImportError:
            raise ImportError("networkx is required to use to_networkx()")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the graph state to a dictionary."""
        return {
            "sightings": self.sightings
        }

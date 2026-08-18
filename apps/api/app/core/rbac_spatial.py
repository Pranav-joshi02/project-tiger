import hashlib
from enum import Enum
from typing import Dict, Any

class UserSpatialRole(Enum):
    PUBLIC = "public"
    RESEARCHER = "researcher"
    FOREST_OFFICER = "forest_officer"
    ADMIN = "admin"

class SpatialPrivacyFilter:
    """
    Applies spatial obfuscation and privacy filtering to geographic data based on user roles.
    """

    def __init__(self, reserve_name: str = "Pench Tiger Reserve", grid_size_km: float = 5.0):
        self.reserve_name = reserve_name
        self.grid_size_deg = grid_size_km / 111.32  # Rough approximation of km to degrees at equator

    def _obfuscate_to_grid(self, lat: float, lon: float, salt: str = "") -> tuple[float, float]:
        """Obfuscates coordinates to a grid centroid with deterministic jitter."""
        # Calculate grid centroid
        grid_lat = round(lat / self.grid_size_deg) * self.grid_size_deg
        grid_lon = round(lon / self.grid_size_deg) * self.grid_size_deg
        
        # Add deterministic jitter based on coordinates and salt
        hash_input = f"{grid_lat}:{grid_lon}:{salt}".encode('utf-8')
        jitter_hash = hashlib.md5(hash_input).hexdigest()
        
        # Extract small jitter values from hash (max ~10% of grid size)
        lat_jitter = (int(jitter_hash[:4], 16) / 65535.0 - 0.5) * (self.grid_size_deg * 0.1)
        lon_jitter = (int(jitter_hash[4:8], 16) / 65535.0 - 0.5) * (self.grid_size_deg * 0.1)
        
        return grid_lat + lat_jitter, grid_lon + lon_jitter

    def filter_observation(self, observation: Dict[str, Any], role: UserSpatialRole) -> Dict[str, Any]:
        """
        Filters observation data based on the provided role.
        """
        filtered = observation.copy()
        
        if 'latitude' not in filtered or 'longitude' not in filtered:
            return filtered
            
        lat = filtered['latitude']
        lon = filtered['longitude']
        
        if role == UserSpatialRole.PUBLIC:
            # Remove exact coordinates, replace with general reserve location
            filtered.pop('latitude', None)
            filtered.pop('longitude', None)
            filtered['location_general'] = self.reserve_name
            filtered['presence_only'] = True
            
        elif role == UserSpatialRole.RESEARCHER:
            # Obfuscate to grid
            obs_id = str(filtered.get('id', ''))
            new_lat, new_lon = self._obfuscate_to_grid(lat, lon, salt=obs_id)
            filtered['latitude'] = new_lat
            filtered['longitude'] = new_lon
            filtered['precision'] = "5km_grid"
            
        elif role == UserSpatialRole.FOREST_OFFICER:
            # Full precision, no changes needed
            filtered['precision'] = "exact"
            
        elif role == UserSpatialRole.ADMIN:
            # Exact + audit metadata
            filtered['precision'] = "exact"
            filtered['audit_viewed_by_admin'] = True
            
        return filtered

    def filter_station(self, station: Dict[str, Any], role: UserSpatialRole) -> Dict[str, Any]:
        """
        Filters camera station data based on the provided role.
        """
        filtered = station.copy()
        
        if 'latitude' not in filtered or 'longitude' not in filtered:
            return filtered
            
        if role == UserSpatialRole.PUBLIC:
            # Hide camera stations completely for public or just show rough region
            filtered.pop('latitude', None)
            filtered.pop('longitude', None)
            filtered['location_general'] = self.reserve_name
            
        elif role == UserSpatialRole.RESEARCHER:
            # Obfuscate to grid
            station_id = str(filtered.get('station_id', ''))
            lat = filtered['latitude']
            lon = filtered['longitude']
            new_lat, new_lon = self._obfuscate_to_grid(lat, lon, salt=station_id)
            filtered['latitude'] = new_lat
            filtered['longitude'] = new_lon
            filtered['precision'] = "5km_grid"
            
        elif role in (UserSpatialRole.FOREST_OFFICER, UserSpatialRole.ADMIN):
            # Full precision
            filtered['precision'] = "exact"
            
        return filtered

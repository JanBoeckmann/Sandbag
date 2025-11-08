from pyproj import Proj, transform

def utm_to_latlon(coordinates):
    utm_zone_number = 32  # Assuming UTM zone 32 for the example
    p = Proj(proj='utm', zone=utm_zone_number, ellps='WGS84')
    lon, lat = p(coordinates[0], coordinates[1], inverse=True)
    return lat, lon

def latlon_to_utm(coordinates):
    utm_zone_number = 32  # Assuming UTM zone 32 for the example
    p = Proj(proj='utm', zone=utm_zone_number, ellps='WGS84')
    x, y = p(coordinates[1], coordinates[0])
    return x, y
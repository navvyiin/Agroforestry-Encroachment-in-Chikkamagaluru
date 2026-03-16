import osmnx as ox
import geopandas as gpd
from pathlib import Path

print("Fetching Chikkamagaluru roads from OSM...")
roads = ox.features_from_place(
    "Chikkamagaluru district, Karnataka, India",
    tags={"highway": ["primary","secondary","tertiary","unclassified","trunk"]}
)
roads = roads[roads.geometry.geom_type.isin(['LineString','MultiLineString'])]
roads.to_file("data/raw/osm/roads.shp")
print(f"  Roads saved: {len(roads)} features")

print("Fetching settlements from OSM...")
settlements = ox.features_from_place(
    "Chikkamagaluru district, Karnataka, India",
    tags={"place": ["village","town","hamlet","city"]}
)
# Save as GeoJSON — handles mixed Point/Polygon geometries unlike shapefile
settlements.to_file("data/raw/osm/settlements.geojson", driver="GeoJSON")
print(f"  Settlements saved: {len(settlements)} features")

print("Fetching Bhadra Wildlife Sanctuary boundary...")
try:
    bhadra = ox.features_from_place(
        "Bhadra Wildlife Sanctuary, Karnataka, India",
        tags={"boundary": "protected_area"}
    )
    bhadra.to_file("data/raw/boundaries/bhadra_reserve.geojson", driver="GeoJSON")
    print(f"  Bhadra boundary saved: {len(bhadra)} features")
except:
    from shapely.geometry import box
    bhadra = gpd.GeoDataFrame(
        {"name": ["Bhadra Tiger Reserve Approximate"]},
        geometry=[box(75.55, 13.45, 75.85, 13.75)],
        crs="EPSG:4326"
    )
    bhadra.to_file("data/raw/boundaries/bhadra_reserve.geojson", driver="GeoJSON")
    print("  Used bounding box fallback for Bhadra")

print("\nALL BOUNDARY DATA FETCHED SUCCESSFULLY")
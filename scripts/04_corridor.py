import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
import numpy as np
import geopandas as gpd
from scipy.ndimage import distance_transform_edt, gaussian_filter
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
from pathlib import Path
from map_utils import add_map_furniture

print("=== SCRIPT 4: CORRIDOR MODEL ===\n")

# Load land cover at 100m
with rasterio.open("data/processed/landcover.tif") as src:
    scale = 10
    new_h = src.height // scale
    new_w = src.width  // scale
    lc  = src.read(1, out_shape=(new_h, new_w), resampling=Resampling.nearest)
    tfm = src.transform * src.transform.scale(src.width/new_w, src.height/new_h)
    crs = src.crs
    meta = src.meta.copy()
meta.update(height=new_h, width=new_w, transform=tfm, dtype='float32', count=1, nodata=-9999)
res = 100.0
print(f"Grid: {new_w}x{new_h} at 100m")

# Slope from SRTM
print("Computing slope...")
srtm_files = list(Path("data/raw/srtm").glob("*.tif"))
with rasterio.open(srtm_files[0]) as src:
    dem = src.read(1, out_shape=(new_h, new_w), resampling=Resampling.bilinear).astype(float)

def compute_slope(dem, cell_size=100):
    dz_dx = (dem[1:-1, 2:] - dem[1:-1, :-2]) / (2 * cell_size)
    dz_dy = (dem[2:, 1:-1] - dem[:-2, 1:-1]) / (2 * cell_size)
    slope = np.sqrt(dz_dx**2 + dz_dy**2)
    return np.pad(slope, 1, mode='edge')

slope = compute_slope(dem)
slope_norm = (slope - slope.min()) / (slope.max() - slope.min() + 1e-10)

# Roads resistance
print("Processing roads...")
roads = gpd.read_file("data/raw/osm/roads.shp").to_crs(crs)
road_shapes = [(geom, 1) for geom in roads.geometry if geom is not None]
road_raster = rasterize(road_shapes, out_shape=(new_h, new_w),
                        transform=tfm, fill=0, dtype='uint8')
dist_road = distance_transform_edt(1 - road_raster) * res
dist_road_norm = 1 - np.clip(dist_road / 2000, 0, 1)

# Settlements resistance
print("Processing settlements...")
try:
    settle = gpd.read_file("data/raw/osm/settlements.geojson").to_crs(crs)
    settle_raster = np.zeros((new_h, new_w), dtype=np.uint8)
    pts = settle[settle.geometry.geom_type == 'Point']
    if len(pts) > 0:
        pt_shapes = [(g.buffer(200), 1) for g in pts.geometry if g is not None]
        settle_raster += rasterize(pt_shapes, out_shape=(new_h, new_w),
                                   transform=tfm, fill=0, dtype='uint8')
    polys = settle[settle.geometry.geom_type.isin(['Polygon','MultiPolygon'])]
    if len(polys) > 0:
        poly_shapes = [(g, 1) for g in polys.geometry if g is not None]
        settle_raster = np.clip(settle_raster + rasterize(poly_shapes,
                        out_shape=(new_h, new_w), transform=tfm,
                        fill=0, dtype='uint8'), 0, 1)
    dist_settle = distance_transform_edt(1 - np.clip(settle_raster,0,1)) * res
    dist_settle_norm = 1 - np.clip(dist_settle / 3000, 0, 1)
    print(f"  {len(settle)} settlement features")
except Exception as e:
    print(f"  Fallback: {e}")
    dist_settle_norm = np.zeros((new_h, new_w))

# Land cover resistance
lc_resist = np.select(
    [lc==1, lc==2, lc==3, lc==4, lc==5],
    [0.05,  0.30,  0.60,  0.95,  0.70], default=0.70)

# Combined resistance
print("Building resistance surface...")
resistance = (0.50*lc_resist + 0.20*slope_norm +
              0.15*dist_road_norm + 0.15*dist_settle_norm)
resistance = gaussian_filter(resistance, sigma=2)
corridor   = np.clip(1.0 - resistance, 0, 1)

print(f"  Resistance: {resistance.min():.3f} to {resistance.max():.3f}")
print(f"  Corridor:   {corridor.min():.3f} to {corridor.max():.3f}")

# Bottlenecks
forest_edge = gaussian_filter((lc==1).astype(float), sigma=3)
edge_zone   = (forest_edge > 0.05) & (forest_edge < 0.95)
bottlenecks = edge_zone & (corridor < 0.35)
bn_ha = bottlenecks.sum() * (res*res) / 10000
print(f"\n  Bottleneck area: {bn_ha:,.0f} ha")

# Save both outputs
with rasterio.open("data/processed/corridor_suitability.tif", 'w', **meta) as dst:
    dst.write(corridor.astype(np.float32), 1)
with rasterio.open("data/processed/bottlenecks.tif", 'w', **meta) as dst:
    dst.write(bottlenecks.astype(np.float32), 1)
print("  Saved corridor and bottleneck rasters")

# Map
print("\nGenerating map...")
fig, axes = plt.subplots(1, 2, figsize=(20, 10))

ax1 = axes[0]
im1 = ax1.imshow(corridor, cmap='RdYlGn', vmin=0, vmax=1, interpolation='bilinear')
plt.colorbar(im1, ax=ax1, fraction=0.03, pad=0.02,
             label='Corridor Suitability\n(0=Barrier, 1=Optimal)')
ax1.set_title('Wildlife Corridor Suitability\nChikkamagaluru Coffee-Forest Mosaic',
              fontsize=13, fontweight='bold')
ax1.axis('off')
add_map_furniture(ax1, pixel_size_m=100)

ax2 = axes[1]
ax2.imshow(corridor, cmap='RdYlGn', vmin=0, vmax=1,
           interpolation='bilinear', alpha=0.7)
bn_overlay = np.ma.masked_where(~bottlenecks, bottlenecks.astype(float))
ax2.imshow(bn_overlay, cmap=mcolors.ListedColormap(['red']),
           vmin=0, vmax=1, alpha=0.9)
ax2.set_title('Critical Corridor Bottlenecks\n(Red = Priority Intervention Zones)',
              fontsize=13, fontweight='bold')
ax2.axis('off')
ax2.legend(handles=[
    Patch(facecolor='green',  label='High suitability'),
    Patch(facecolor='yellow', label='Moderate suitability'),
    Patch(facecolor='red',    label='Critical bottleneck'),
], loc='lower right', fontsize=10)
add_map_furniture(ax2, pixel_size_m=100)

plt.suptitle('Corridor Suitability & Bottleneck Analysis — Chikkamagaluru, Western Ghats',
             fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig('outputs/maps/03_corridor.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.show()
print("  Saved: outputs/maps/03_corridor.png")
print(f"\nKEY NUMBER FOR POSTER: Bottleneck area = {bn_ha:,.0f} ha")
print("=== SCRIPT 4 COMPLETE ===")
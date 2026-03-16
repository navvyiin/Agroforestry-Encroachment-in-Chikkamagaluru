import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
import rasterio
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
from pathlib import Path
from map_utils import add_map_furniture

print("=== SCRIPT 5: HEC HOTSPOT & CORRIDOR OVERLAY ===\n")

# --- LOAD HEC DATA ---
hec = pd.read_csv("data/raw/hec/incidents.csv")
print(f"HEC incidents loaded: {len(hec)}")
print(f"Year range: {hec['year'].min()}–{hec['year'].max()}")
print(f"Incident types:\n{hec['incident_type'].value_counts()}")
print(f"Taluks affected:\n{hec['taluk'].value_counts()}")

# Convert to GeoDataFrame in UTM Zone 43N
hec_gdf = gpd.GeoDataFrame(
    hec,
    geometry=gpd.points_from_xy(hec['longitude'], hec['latitude']),
    crs='EPSG:4326'
).to_crs('EPSG:32643')

x = hec_gdf.geometry.x.values
y = hec_gdf.geometry.y.values

# --- LOAD CORRIDOR FOR EXTENT REFERENCE ---
print("\nLoading corridor raster...")
with rasterio.open("data/processed/corridor_suitability.tif") as src:
    corridor = src.read(1).astype(float)
    tfm      = src.transform
    crs      = src.crs
    new_h, new_w = src.height, src.width
    # Get extent in UTM
    from rasterio.transform import array_bounds
    bounds = array_bounds(new_h, new_w, tfm)
    # bounds = (left, bottom, right, top)

x_min, x_max = bounds[0], bounds[2]
y_min, y_max = bounds[1], bounds[3]

# --- KDE ON MATCHING GRID ---
print("Running KDE...")
xi = np.linspace(x_min, x_max, new_w)
yi = np.linspace(y_min, y_max, new_h)
xx, yy = np.meshgrid(xi, yi)
positions = np.vstack([xx.ravel(), yy.ravel()])
values    = np.vstack([x, y])

kernel   = gaussian_kde(values, bw_method=0.15)
kde_grid = np.reshape(kernel(positions), (new_h, new_w))
# Flip y-axis to match raster orientation
kde_grid = np.flipud(kde_grid)

# Normalise 0-1
kde_norm = (kde_grid - kde_grid.min()) / (kde_grid.max() - kde_grid.min())
print(f"  KDE computed on {new_w}x{new_h} grid")

# --- LOAD BOTTLENECKS ---
with rasterio.open("data/processed/bottlenecks.tif") as src:
    bottlenecks = src.read(1).astype(bool)

# --- LOAD LAND COVER FOR CONTEXT ---
with rasterio.open("data/processed/landcover.tif") as src:
    lc = src.read(1, out_shape=(new_h, new_w), resampling=Resampling.nearest)

# --- SPATIAL COINCIDENCE: HEC near bottlenecks? ---
print("\nAnalysing spatial coincidence...")
# Check which incidents fall within bottleneck zones (or within 1.5km)
from scipy.ndimage import binary_dilation
from math import ceil

# Buffer bottlenecks by 1.5km = 15 cells at 100m
buffered_bn = binary_dilation(bottlenecks, iterations=15)

# For each incident, check if it falls in buffered bottleneck
def world_to_pixel(px, py, transform):
    col = int((px - transform.c) / transform.a)
    row = int((py - transform.f) / transform.e)
    return row, col

incidents_in_bn = 0
for xi_pt, yi_pt in zip(x, y):
    row, col = world_to_pixel(xi_pt, yi_pt, tfm)
    if 0 <= row < new_h and 0 <= col < new_w:
        if buffered_bn[row, col]:
            incidents_in_bn += 1

pct_in_bn = 100 * incidents_in_bn / len(hec)
print(f"\n{'='*50}")
print(f"  SPATIAL COINCIDENCE RESULT")
print(f"{'='*50}")
print(f"  Total HEC incidents: {len(hec)}")
print(f"  Incidents within 1.5km of bottleneck zone: {incidents_in_bn}")
print(f"  Percentage: {pct_in_bn:.1f}%")
print(f"  THIS IS YOUR KEY FINDING FOR THE POSTER")
print(f"{'='*50}")

# --- MAP: 4-PANEL FINAL FIGURE ---
print("\nGenerating final overlay map...")
fig, axes = plt.subplots(2, 2, figsize=(20, 18))

# Panel 1: Land cover
ax1 = axes[0,0]
cmap_lc = mcolors.ListedColormap([
    '#0d0d0d','#1B4332','#52B788','#D4A373','#E76F51','#4895EF'])
norm_lc = mcolors.BoundaryNorm([0,1,2,3,4,5,6], cmap_lc.N)
ax1.imshow(lc, cmap=cmap_lc, norm=norm_lc, interpolation='nearest')
ax1.set_title('① Land Cover Classification', fontsize=13, fontweight='bold')
ax1.axis('off')
legend1 = [Patch(color='#1B4332', label='Dense Forest'),
           Patch(color='#52B788', label='Shade Coffee'),
           Patch(color='#D4A373', label='Open Coffee'),
           Patch(color='#E76F51', label='Settlement'),
           Patch(color='#4895EF', label='Water')]
ax1.legend(handles=legend1, loc='lower right', fontsize=9)
add_map_furniture(ax1, pixel_size_m=100, north_x=0.93, north_y=0.18)

# Panel 2: KDE hotspots + incident points
ax2 = axes[0,1]
im2 = ax2.imshow(kde_norm, cmap='YlOrRd', vmin=0, vmax=1,
                 interpolation='bilinear', alpha=0.85)
# Plot incident points
ax2.scatter(
    [(xi_pt - x_min)/(x_max-x_min)*new_w for xi_pt in x],
    [new_h - (yi_pt - y_min)/(y_max-y_min)*new_h for yi_pt in y],
    s=40, c='black', zorder=5, alpha=0.8, label='HEC Incident'
)
plt.colorbar(im2, ax=ax2, fraction=0.03, pad=0.02, label='Incident Density')
ax2.set_title('② HEC Hotspot Density (KDE)', fontsize=13, fontweight='bold')
ax2.axis('off')
ax2.legend(loc='lower right', fontsize=9)
add_map_furniture(ax2, pixel_size_m=100, north_x=0.93, north_y=0.18)

# Panel 3: Corridor suitability
ax3 = axes[1,0]
im3 = ax3.imshow(corridor, cmap='RdYlGn', vmin=0, vmax=1,
                 interpolation='bilinear')
plt.colorbar(im3, ax=ax3, fraction=0.03, pad=0.02,
             label='Suitability (0=Barrier, 1=Optimal)')
ax3.set_title('③ Wildlife Corridor Suitability', fontsize=13, fontweight='bold')
ax3.axis('off')
add_map_furniture(ax3, pixel_size_m=100, north_x=0.93, north_y=0.18)

# Panel 4: KEY FINDING — overlap map
ax4 = axes[1,1]
ax4.imshow(corridor, cmap='RdYlGn', vmin=0, vmax=1,
           interpolation='bilinear', alpha=0.6)
# Bottleneck overlay
bn_show = np.ma.masked_where(~bottlenecks, np.ones_like(bottlenecks, float))
ax4.imshow(bn_show, cmap=mcolors.ListedColormap(['#CC0000']),
           alpha=0.7, interpolation='nearest')
# KDE overlay (semi-transparent)
ax4.imshow(kde_norm, cmap='YlOrRd', vmin=0.3, vmax=1,
           alpha=0.45, interpolation='bilinear')
# Incident points
ax4.scatter(
    [(xi_pt - x_min)/(x_max-x_min)*new_w for xi_pt in x],
    [new_h - (yi_pt - y_min)/(y_max-y_min)*new_h for yi_pt in y],
    s=60, c='white', edgecolors='black', linewidths=1.5,
    zorder=10, label=f'HEC Incident (n={len(hec)})'
)
ax4.set_title(f'④ KEY FINDING: Conflict Hotspots ∩ Corridor Bottlenecks\n'
              f'{incidents_in_bn}/{len(hec)} incidents ({pct_in_bn:.0f}%) within 1.5km of bottleneck zones',
              fontsize=12, fontweight='bold', color='#CC0000')
ax4.axis('off')
ax4.legend(handles=[
    Patch(color='#CC0000', label='Corridor bottleneck'),
    Patch(color='#E76F51', alpha=0.5, label='HEC density'),
], loc='lower right', fontsize=9)
add_map_furniture(ax4, pixel_size_m=100, north_x=0.93, north_y=0.18)

plt.suptitle('Spatial Analysis of Agroforestry Encroachment & Wildlife Corridor Breakdown\n'
             'Chikkamagaluru District, Western Ghats — Naval Kishore, Bangalore University 2026',
             fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('outputs/maps/04_hec_corridor_overlay.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.show()

print("  Saved: outputs/maps/04_hec_corridor_overlay.png")
print(f"\n{'='*50}")
print("  ALL 4 MAPS COMPLETE")
print(f"{'='*50}")
print(f"  Map 1: outputs/maps/01_landcover.png")
print(f"  Map 2: outputs/maps/02_fragmentation.png")
print(f"  Map 3: outputs/maps/03_corridor.png")
print(f"  Map 4: outputs/maps/04_hec_corridor_overlay.png")
print(f"\n  KEY POSTER NUMBERS:")
print(f"  Bottleneck area: 28,446 ha")
print(f"  HEC incidents near bottlenecks: {incidents_in_bn}/{len(hec)} ({pct_in_bn:.0f}%)")
print("=== ALL ANALYSIS COMPLETE — READY FOR POSTER DESIGN ===")
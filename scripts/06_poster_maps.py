import rasterio
from rasterio.enums import Resampling
from rasterio.transform import array_bounds
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from scipy.stats import gaussian_kde
from scipy.ndimage import binary_dilation
from pathlib import Path
from map_utils import add_map_furniture

print("=== GENERATING 4 INDIVIDUAL POSTER MAPS ===\n")
Path("outputs/maps").mkdir(parents=True, exist_ok=True)

# ── SHARED SETUP ──────────────────────────────────────────────
RES = 100
with rasterio.open("data/processed/landcover.tif") as src:
    scale = 10
    new_h = src.height // scale
    new_w = src.width  // scale
    lc = src.read(1, out_shape=(new_h, new_w), resampling=Resampling.nearest)
    tfm = src.transform * src.transform.scale(src.width/new_w, src.height/new_h)
    crs = src.crs

with rasterio.open("data/processed/corridor_suitability.tif") as src:
    corridor = src.read(1).astype(float)
    bounds   = array_bounds(src.height, src.width, src.transform)

with rasterio.open("data/processed/bottlenecks.tif") as src:
    bottlenecks = src.read(1).astype(bool)

hec = pd.read_csv("data/raw/hec/incidents.csv")
hec_gdf = gpd.GeoDataFrame(
    hec, geometry=gpd.points_from_xy(hec['longitude'], hec['latitude']),
    crs='EPSG:4326').to_crs('EPSG:32643')
x = hec_gdf.geometry.x.values
y = hec_gdf.geometry.y.values
x_min, y_min, x_max, y_max = bounds

# Land cover colourmap
lc_cmap = mcolors.ListedColormap(
    ['#0d0d0d','#1B4332','#52B788','#D4A373','#E76F51','#4895EF'])
lc_norm = mcolors.BoundaryNorm([0,1,2,3,4,5,6], lc_cmap.N)

def to_px(xc, yc):
    col = (xc - x_min) / (x_max - x_min) * new_w
    row = new_h - (yc - y_min) / (y_max - y_min) * new_h
    return col, row

px_x, px_y = to_px(x, y)

# ── Class pixel counts for legend labels ──────────────────────
total_px = np.sum(lc > 0)
def pct(cls): return 100 * np.sum(lc == cls) / total_px if total_px > 0 else 0

# ============================================================
# MAP 1: LAND COVER CLASSIFICATION  (ADVANCED FIXES)
# • Correct bar_km=10 label
# • Legend includes class % coverage
# • District boundary box (annotation)
# • Improved layout with explicit pixel_size correction
# ============================================================
print("Generating Map 1: Land Cover...")
fig, ax = plt.subplots(figsize=(12, 13))
ax.imshow(lc, cmap=lc_cmap, norm=lc_norm, interpolation='nearest')

legend = [
    mpatches.Patch(color='#1B4332', label=f'Dense Forest ({pct(1):.1f}%)'),
    mpatches.Patch(color='#52B788', label=f'Shade-grown Coffee ({pct(2):.1f}%)'),
    mpatches.Patch(color='#D4A373', label=f'Open/Sun Coffee ({pct(3):.1f}%)'),
    mpatches.Patch(color='#E76F51', label=f'Settlement / Bare ({pct(4):.1f}%)'),
    mpatches.Patch(color='#4895EF', label=f'Water ({pct(5):.1f}%)'),
]
ax.legend(handles=legend, loc='lower right', fontsize=10.5,
          framealpha=0.92, edgecolor='#333',
          title='Land Cover Class', title_fontsize=11)

# Key stats inset box (top-left)
stats_text = (
    f"Study Area: Chikkamagaluru District\n"
    f"Resolution: 10 m (Sentinel-2 SR)\n"
    f"Season: Nov 2023 – Feb 2024\n"
    f"CRS: UTM Zone 43N (EPSG:32643)"
)
ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
        fontsize=8.5, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                  alpha=0.88, edgecolor='#555'))

ax.set_title('Land Cover Classification\nChikkamagaluru District, Western Ghats',
             fontsize=15, fontweight='bold', pad=12)
ax.axis('off')
# pixel_size_m=100 because lc was loaded at scale=10 from 10m source
add_map_furniture(ax, pixel_size_m=100, image_width_px=new_w, bar_km=10)
fig.text(0.01, 0.01, 'Data: Sentinel-2 SR (GEE, Nov 2023–Feb 2024) | '
         'Classification: NDVI/NDWI/NDBI thresholds | EPSG:32643',
         fontsize=8, color='grey')
plt.tight_layout()
plt.savefig('outputs/maps/MAP1_landcover.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved: MAP1_landcover.png")

# ============================================================
# MAP 2: FOREST FRAGMENTATION  (ADVANCED FIXES)
# • Proper xlim/ylim from gdf.total_bounds
# • No conflicting imshow background
# • Scale bar clear of stats box
# ============================================================
print("Generating Map 2: Fragmentation...")
patches_gdf = gpd.read_file("data/processed/forest_patches.gpkg")

fig, ax = plt.subplots(figsize=(12, 13))
patches_gdf.plot(column='area_ha', cmap='YlGn', legend=True, ax=ax,
                 linewidth=0.1, edgecolor='#2d6a4f',
                 legend_kwds={'label':'Forest Patch Size (ha)',
                              'orientation':'vertical','shrink':0.5,'pad':0.02})
ax.set_title('Forest Patch Size Distribution\nChikkamagaluru Coffee-Forest Mosaic',
             fontsize=15, fontweight='bold', pad=12)

p_minx, p_miny, p_maxx, p_maxy = patches_gdf.total_bounds
ax.set_xlim(p_minx, p_maxx)
ax.set_ylim(p_miny, p_maxy)
ax.axis('off')
add_map_furniture(ax, pixel_size_m=50, image_width_px=new_w, bar_km=5, y_bar=0.23)

stats_text = ("Total patches (>2.5 ha): 8,215\n"
              "Patches under 50 ha: 97.4%\n"
              "Median patch size: 4.3 ha\n"
              "Largest core patch: 312,607 ha")
ax.text(0.02, 0.18, stats_text, transform=ax.transAxes,
        fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                  alpha=0.85, edgecolor='#2d6a4f'))
fig.text(0.01, 0.01,
         'Analysis: GeoPandas patch vectorisation at 50m | Fragmentation metrics: Shape Index, PAR',
         fontsize=8, color='grey')
plt.tight_layout()
plt.savefig('outputs/maps/MAP2_fragmentation.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved: MAP2_fragmentation.png")

# ============================================================
# MAP 3: CORRIDOR SUITABILITY + BOTTLENECKS  (ADVANCED FIXES)
# • Cleaner colorbar with explicit ticks at 0.35 (bottleneck) and 0.6 (high)
# • Bottleneck area annotation directly on map
# • Resistance weights inset
# ============================================================
print("Generating Map 3: Corridor...")
fig, ax = plt.subplots(figsize=(12, 13))
im = ax.imshow(corridor, cmap='RdYlGn', vmin=0, vmax=1, interpolation='bilinear')
bn_show = np.ma.masked_where(~bottlenecks, np.ones_like(corridor))
ax.imshow(bn_show, cmap=mcolors.ListedColormap(['#CC0000']),
          alpha=0.80, interpolation='nearest')

cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02, shrink=0.55)
cbar.set_label('Corridor Suitability  (0 = Barrier → 1 = Optimal)', fontsize=10)
cbar.set_ticks([0, 0.2, 0.35, 0.6, 0.8, 1.0])
cbar.set_ticklabels(['0.0','0.2','0.35\n(BN threshold)','0.6\n(High suit.)','0.8','1.0'],
                    fontsize=8)
# Mark threshold lines on colorbar
cbar.ax.axhline(0.35, color='#CC0000', linewidth=2, linestyle='--')
cbar.ax.axhline(0.60, color='#1a9850', linewidth=2, linestyle='--')

legend = [
    mpatches.Patch(color='#1a9850', label='High suitability (>0.60)'),
    mpatches.Patch(color='#fee08b', label='Moderate suitability (0.35–0.60)'),
    mpatches.Patch(color='#d73027', label='Low suitability (<0.35)'),
    mpatches.Patch(color='#CC0000', label='Critical bottleneck zones\n(28,446 ha | suitability <0.35 at forest edge)'),
]
ax.legend(handles=legend, loc='lower right', fontsize=9.5,
          framealpha=0.92, edgecolor='#333')

# Resistance weights inset box
weights_text = ("Resistance surface weights:\n"
                "  Land cover:   50%\n"
                "  Slope:        20%\n"
                "  Roads:        15%\n"
                "  Settlements:  15%")
ax.text(0.02, 0.98, weights_text, transform=ax.transAxes,
        fontsize=8.5, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#FAFFF8',
                  alpha=0.90, edgecolor='#2d6a4f'))

ax.set_title('Wildlife Corridor Suitability & Bottleneck Zones\nChikkamagaluru Coffee-Forest Mosaic',
             fontsize=15, fontweight='bold', pad=12)
ax.axis('off')
add_map_furniture(ax, pixel_size_m=100, image_width_px=corridor.shape[1])
fig.text(0.01, 0.01,
         'Resistance surface: weighted sum | Bottleneck: suitability < 0.35 at forest edge | EPSG:32643',
         fontsize=8, color='grey')
plt.tight_layout()
plt.savefig('outputs/maps/MAP3_corridor.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved: MAP3_corridor.png")

# ============================================================
# MAP 4: KEY FINDING — HEC HOTSPOTS + CORRIDOR OVERLAY  (ADVANCED FIXES)
# • HEC incident point added to legend (was missing)
# • Incident type breakdown annotation box
# • Cleaner KDE threshold
# • Larger incident point markers for poster visibility
# ============================================================
print("Generating Map 4: HEC Key Finding...")

xi_grid = np.linspace(x_min, x_max, new_w)
yi_grid = np.linspace(y_min, y_max, new_h)
xx, yy  = np.meshgrid(xi_grid, yi_grid)
positions = np.vstack([xx.ravel(), yy.ravel()])
kernel   = gaussian_kde(np.vstack([x, y]), bw_method=0.12)
kde_grid = np.reshape(kernel(positions), (new_h, new_w))
kde_grid = np.flipud(kde_grid)
kde_norm_arr = (kde_grid - kde_grid.min()) / (kde_grid.max() - kde_grid.min())

buffered_bn = binary_dilation(bottlenecks, iterations=15)
incidents_in_bn = sum(
    1 for xi_pt, yi_pt in zip(x, y)
    if 0 <= int((new_h - (yi_pt-y_min)/(y_max-y_min)*new_h)) < new_h
    and 0 <= int((xi_pt-x_min)/(x_max-x_min)*new_w) < new_w
    and buffered_bn[
        int(new_h - (yi_pt-y_min)/(y_max-y_min)*new_h),
        int((xi_pt-x_min)/(x_max-x_min)*new_w)
    ]
)
pct_val = 100 * incidents_in_bn / len(hec)

# Incident type counts for annotation
type_counts = hec['incident_type'].value_counts()

fig, ax = plt.subplots(figsize=(12, 13))

# Layer 1: land cover base
ax.imshow(lc, cmap=lc_cmap, norm=lc_norm,
          interpolation='nearest', alpha=0.30)
# Layer 2: corridor suitability
ax.imshow(corridor, cmap='RdYlGn', vmin=0, vmax=1,
          interpolation='bilinear', alpha=0.40)
# Layer 3: KDE hotspots
kde_masked = np.ma.masked_where(kde_norm_arr < 0.12, kde_norm_arr)
ax.imshow(kde_masked, cmap='YlOrRd', vmin=0.12, vmax=1,
          alpha=0.65, interpolation='bilinear')
# Layer 4: bottlenecks
bn_show = np.ma.masked_where(~bottlenecks, np.ones_like(corridor))
ax.imshow(bn_show, cmap=mcolors.ListedColormap(['#8B0000']),
          alpha=0.65, interpolation='nearest')
# Layer 5: incident points — larger for poster visibility
ax.scatter(px_x, px_y, s=28, c='white', edgecolors='#111',
           linewidths=1.0, zorder=10, alpha=0.90)

ax.set_title(
    f'KEY FINDING: Conflict Hotspots ∩ Corridor Bottlenecks\n'
    f'{incidents_in_bn}/{len(hec)} incidents ({pct_val:.0f}%) cluster within '
    f'1.5 km of bottleneck zones',
    fontsize=14, fontweight='bold', color='#8B0000', pad=12)
ax.axis('off')

# FIX: complete legend INCLUDING white circle for HEC incident points
legend = [
    mpatches.Patch(color='#1B4332', label='Dense forest (high suitability)'),
    mpatches.Patch(color='#fee08b', label='Moderate corridor zone'),
    mpatches.Patch(color='#E76F51', alpha=0.65, label='HEC density hotspot (KDE)'),
    mpatches.Patch(color='#8B0000', label='Critical bottleneck zone'),
    Line2D([0],[0], marker='o', color='none', markerfacecolor='white',
           markeredgecolor='black', markeredgewidth=1.0, markersize=8,
           label=f'HEC incident point (n={len(hec)})'),
]
ax.legend(handles=legend, loc='lower right', fontsize=9.5,
          framealpha=0.92, edgecolor='#333')

# Incident type breakdown annotation box (top-left)
type_lines = "\n".join(
    f"  {k.replace('_',' ').title()}: {v}" for k, v in type_counts.items()
)
incident_text = f"Incident types (2018–2023):\n{type_lines}"
ax.text(0.02, 0.98, incident_text, transform=ax.transAxes,
        fontsize=8, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF8F0',
                  alpha=0.90, edgecolor='#8B0000'))

add_map_furniture(ax, pixel_size_m=100, image_width_px=corridor.shape[1])
fig.text(0.01, 0.01,
         'HEC: Spatially modelled from KFD taluk-level totals 2018–2023 | '
         'KDE bw=0.12 | Bottleneck buffer=1.5km | EPSG:32643',
         fontsize=8, color='grey')
plt.tight_layout()
plt.savefig('outputs/maps/MAP4_hec_keyfinding.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved: MAP4_hec_keyfinding.png")

print("\n=== ALL 4 POSTER MAPS SAVED ===")
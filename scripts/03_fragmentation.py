import rasterio
from rasterio.features import shapes
from rasterio.enums import Resampling
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
import matplotlib.pyplot as plt
from pathlib import Path
from map_utils import add_map_furniture

print("=== SCRIPT 3: FRAGMENTATION ANALYSIS ===\n")

# --- LOAD AND DOWNSAMPLE TO 50m (memory-safe) ---
print("Loading and resampling land cover to 50m...")
with rasterio.open("data/processed/landcover.tif") as src:
    # Downsample 5x: 10m → 50m
    scale = 5
    new_h = src.height // scale
    new_w = src.width  // scale
    lc = src.read(1,
        out_shape=(new_h, new_w),
        resampling=Resampling.nearest
    )
    # Adjust transform for new resolution
    tfm = src.transform * src.transform.scale(
        src.width  / new_w,
        src.height / new_h
    )
    crs = src.crs

res = 50.0  # metres
pixel_area_ha = (res * res) / 10000
print(f"  Resampled to: {new_w}x{new_h}px at 50m resolution")

# --- VECTORISE FOREST PATCHES ---
print("Vectorising forest patches...")
forest_mask = (lc == 1).astype(np.uint8)
results = list(shapes(forest_mask, transform=tfm))
geoms   = [shape(r[0]) for r in results if r[1] == 1]
print(f"  Raw patches: {len(geoms)}")

gdf = gpd.GeoDataFrame({'geometry': geoms}, crs=crs)
gdf = gdf.to_crs(epsg=32643)
gdf['area_ha']     = gdf.area / 10000
gdf['perimeter_m'] = gdf.length
gdf = gdf[gdf['area_ha'] > 2.5].reset_index(drop=True)  # >2.5ha filter at 50m
print(f"  Patches >2.5 ha: {len(gdf)}")

# --- METRICS ---
gdf['shape_idx'] = gdf['perimeter_m'] / (2 * np.sqrt(np.pi * gdf.area))
gdf['par']       = gdf['perimeter_m'] / gdf['area_ha']

def size_class(ha):
    if ha < 10:    return 'Micro (<10 ha)'
    elif ha < 50:  return 'Small (10-50 ha)'
    elif ha < 200: return 'Medium (50-200 ha)'
    elif ha < 500: return 'Large (200-500 ha)'
    else:          return 'Core (>500 ha)'
gdf['size_class'] = gdf['area_ha'].apply(size_class)

total_forest_ha = gdf['area_ha'].sum()
total_area_ha   = lc.size * pixel_area_ha
forest_pct      = 100 * total_forest_ha / total_area_ha
edge_density    = gdf['perimeter_m'].sum() / (total_forest_ha * 10000) * 100

print("\n" + "="*50)
print("  FRAGMENTATION SUMMARY")
print("="*50)
print(f"  Total patches (>2.5 ha):  {len(gdf):,}")
print(f"  Total forest area:        {total_forest_ha:,.1f} ha")
print(f"  Forest cover:             {forest_pct:.1f}%")
print(f"  Largest patch:            {gdf['area_ha'].max():,.1f} ha")
print(f"  Median patch size:        {gdf['area_ha'].median():.1f} ha")
print(f"  Mean shape index:         {gdf['shape_idx'].mean():.3f}")
print(f"  Edge density (m/100ha):   {edge_density:.2f}")
print()
print("  SIZE CLASS BREAKDOWN:")
for cls in ['Micro (<10 ha)','Small (10-50 ha)','Medium (50-200 ha)',
            'Large (200-500 ha)','Core (>500 ha)']:
    n   = (gdf['size_class'] == cls).sum()
    pct = 100 * n / len(gdf) if len(gdf) > 0 else 0
    ha  = gdf.loc[gdf['size_class']==cls, 'area_ha'].sum()
    print(f"    {cls}: {n} patches ({pct:.1f}%) — {ha:,.0f} ha total")
print("="*50)

# Save
Path("outputs/stats").mkdir(parents=True, exist_ok=True)
gdf[['area_ha','perimeter_m','shape_idx','par','size_class']]\
    .to_csv("outputs/stats/fragmentation_stats.csv", index=False)
gdf.to_file("data/processed/forest_patches.gpkg", driver="GPKG")
print("\n  Saved stats and patches")

# --- MAP ---
print("\nGenerating map...")
fig, axes = plt.subplots(1, 2, figsize=(20, 10))

ax1 = axes[0]
gdf.plot(column='area_ha', cmap='YlGn', legend=True, ax=ax1,
         linewidth=0.1, edgecolor='white',
         legend_kwds={'label':'Patch Size (ha)','orientation':'vertical','shrink':0.6})
ax1.set_title('Forest Patch Size\nChikkamagaluru Coffee-Forest Mosaic',
              fontsize=13, fontweight='bold')
ax1.axis('off')
add_map_furniture(ax1, pixel_size_m=50, bar_km=5)

ax2 = axes[1]
gdf.plot(column='shape_idx', cmap='RdYlGn_r', legend=True, ax=ax2,
         linewidth=0.1, edgecolor='white',
         legend_kwds={'label':'Shape Index','orientation':'vertical','shrink':0.6})
ax2.set_title('Patch Shape Index\n(Higher = More Fragmented Edge)',
              fontsize=13, fontweight='bold')
ax2.axis('off')
add_map_furniture(ax2, pixel_size_m=50, bar_km=5)

plt.suptitle('Forest Fragmentation — Chikkamagaluru, Western Ghats',
             fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig('outputs/maps/02_fragmentation.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.show()
print("  Saved: outputs/maps/02_fragmentation.png")
print("\n=== SCRIPT 3 COMPLETE — NOTE DOWN THE STATS ABOVE ===")
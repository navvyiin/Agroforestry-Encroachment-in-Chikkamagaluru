import rasterio
from rasterio.merge import merge
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path
from map_utils import add_map_furniture

print("=== SCRIPT 2: LAND COVER CLASSIFICATION (Memory-Efficient) ===\n")

def classify_tile(filepath):
    """Classify a single tile without loading full mosaic into RAM"""
    with rasterio.open(filepath) as src:
        meta = src.meta.copy()
        print(f"  Reading {filepath.name} — {src.count} bands, {src.width}x{src.height}px")
        
        # Read bands one at a time to save memory
        if src.count >= 9:
            print("  Using pre-computed GEE indices...")
            NDVI = src.read(7).astype(np.float32)
            NDWI = src.read(8).astype(np.float32)
            NDBI = src.read(9).astype(np.float32)
        else:
            print("  Computing indices from raw bands...")
            green = src.read(2).astype(np.float32)
            red   = src.read(3).astype(np.float32)
            nir   = src.read(4).astype(np.float32)
            swir1 = src.read(5).astype(np.float32)
            NDVI  = (nir - red)   / (nir + red   + 1e-10)
            NDWI  = (green - nir) / (green + nir + 1e-10)
            NDBI  = (swir1 - nir) / (swir1 + nir + 1e-10)
            del green, red, nir, swir1  # Free memory immediately

    # Clean nodata
    NDVI = np.where(np.isfinite(NDVI), NDVI, 0)
    NDWI = np.where(np.isfinite(NDWI), NDWI, 0)
    NDBI = np.where(np.isfinite(NDBI), NDBI, 0)

    print(f"  NDVI range: {NDVI.min():.3f} to {NDVI.max():.3f}")

    # Classify
    lc = np.zeros(NDVI.shape, dtype=np.uint8)
    lc[(NDVI > 0.55)]                                       = 1  # Dense Forest
    lc[(NDVI > 0.30) & (NDVI <= 0.55) & (NDBI < 0.05)]    = 2  # Shade Coffee
    lc[(NDVI > 0.15) & (NDVI <= 0.30) & (NDBI < 0.05)]    = 3  # Open Coffee
    lc[(NDBI > 0.05) | (NDVI < 0.10)]                      = 4  # Settlement/Bare
    lc[NDWI > 0.20]                                         = 5  # Water
    del NDVI, NDWI, NDBI  # Free memory

    # Save classified tile
    out_meta = meta.copy()
    out_meta.update(dtype='uint8', count=1, nodata=0)
    return lc, out_meta

# --- PROCESS EACH TILE ---
s2_files = sorted(Path("data/raw/sentinel2").glob("*.tif"))
tile_paths = []

for i, f in enumerate(s2_files):
    print(f"\nProcessing tile {i+1}/{len(s2_files)}...")
    lc, meta = classify_tile(f)
    
    out_path = Path(f"data/processed/landcover_tile{i}.tif")
    with rasterio.open(out_path, 'w', **meta) as dst:
        dst.write(lc, 1)
    tile_paths.append(out_path)
    print(f"  Saved: {out_path.name}")
    del lc  # Free memory

# --- MERGE CLASSIFIED TILES (uint8 = tiny, no memory issues) ---
print("\nMerging classified tiles...")
datasets = [rasterio.open(p) for p in tile_paths]
mosaic, out_transform = merge(datasets, nodata=0)
out_meta = datasets[0].meta.copy()
out_meta.update(height=mosaic.shape[1], width=mosaic.shape[2],
                transform=out_transform)
for ds in datasets:
    ds.close()

landcover = mosaic[0]

# Save final merged classification
with rasterio.open("data/processed/landcover.tif", 'w', **out_meta) as dst:
    dst.write(landcover, 1)
print("  Saved: data/processed/landcover.tif")

# --- CLASS DISTRIBUTION ---
classes = {1:'Dense Forest', 2:'Shade Coffee', 3:'Open Coffee',
           4:'Settlement/Bare', 5:'Water'}
total = np.sum(landcover > 0)
print("\n  CLASS DISTRIBUTION:")
for code, name in classes.items():
    count = np.sum(landcover == code)
    pct   = 100 * count / total if total > 0 else 0
    print(f"  Class {code} ({name}): {count:,} pixels ({pct:.1f}%)")

# --- MAP ---
print("\nGenerating map...")
Path("outputs/maps").mkdir(parents=True, exist_ok=True)

cmap = mcolors.ListedColormap([
    '#0d0d0d','#1B4332','#52B788','#D4A373','#E76F51','#4895EF'])
norm = mcolors.BoundaryNorm([0,1,2,3,4,5,6], cmap.N)

fig, ax = plt.subplots(figsize=(14, 12))
img = ax.imshow(landcover, cmap=cmap, norm=norm, interpolation='nearest')
cbar = plt.colorbar(img, ax=ax, fraction=0.03, pad=0.02,
                    ticks=[0.5,1.5,2.5,3.5,4.5,5.5])
cbar.set_ticklabels(['NoData','Dense Forest','Shade Coffee',
                     'Open Coffee','Settlement/Bare','Water'], fontsize=11)
ax.set_title('Land Cover Classification\nChikkamagaluru District, Western Ghats',
             fontsize=14, fontweight='bold')
ax.axis('off')
add_map_furniture(ax, pixel_size_m=10)
fig.text(0.01, 0.01,
         'Data: Sentinel-2 SR (GEE) | NDVI/NDWI/NDBI classification | EPSG:32643',
         fontsize=8, color='grey')
plt.tight_layout()
plt.savefig('outputs/maps/01_landcover.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.show()

print("\n  Map saved: outputs/maps/01_landcover.png")
print("=== SCRIPT 2 COMPLETE ===")

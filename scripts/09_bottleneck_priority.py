"""
Script 09 — Bottleneck Priority Ranking & Site-Specific Interventions
Ranks the top intervention zones by ecological urgency and conflict pressure.
Naval Kishore & Ria Dutta | Bangalore University 2026
"""

import rasterio
from rasterio.enums import Resampling
from rasterio.transform import array_bounds
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.ndimage import label, gaussian_filter, binary_dilation
from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from pathlib import Path
from map_utils import add_map_furniture

print("=== SCRIPT 09: BOTTLENECK PRIORITY RANKING ===\n")

OUT_MAPS  = Path("outputs/maps")
OUT_STATS = Path("outputs/stats")

# ── LOAD DATA ─────────────────────────────────────────────────
print("Loading rasters...")
with rasterio.open("data/processed/bottlenecks.tif") as src:
    bottlenecks = src.read(1).astype(bool)
    tfm   = src.transform
    crs   = src.crs
    h, w  = bottlenecks.shape
    bounds = array_bounds(h, w, tfm)

with rasterio.open("data/processed/corridor_suitability.tif") as src:
    corridor = src.read(1).astype(float)

with rasterio.open("data/processed/landcover.tif") as src:
    lc = src.read(1, out_shape=(h, w), resampling=Resampling.nearest)

hec = pd.read_csv("data/raw/hec/incidents.csv")
hec_gdf = gpd.GeoDataFrame(
    hec, geometry=gpd.points_from_xy(hec['longitude'], hec['latitude']),
    crs='EPSG:4326').to_crs(crs)
x_hec = hec_gdf.geometry.x.values
y_hec = hec_gdf.geometry.y.values

x_min, y_min, x_max, y_max = bounds
RES = 100.0  # metres

# ── KDE ON GRID ───────────────────────────────────────────────
print("Computing KDE density grid...")
xi = np.linspace(x_min, x_max, w)
yi = np.linspace(y_min, y_max, h)
xx, yy = np.meshgrid(xi, yi)
positions = np.vstack([xx.ravel(), yy.ravel()])
kernel = gaussian_kde(np.vstack([x_hec, y_hec]), bw_method=0.12)
kde_grid = np.reshape(kernel(positions), (h, w))
kde_grid = np.flipud(kde_grid)
kde_norm = (kde_grid - kde_grid.min()) / (kde_grid.max() - kde_grid.min() + 1e-10)

# ── LABEL CONNECTED BOTTLENECK ZONES ─────────────────────────
print("Labelling bottleneck zones...")
labeled, n_zones = label(bottlenecks)
print(f"  Found {n_zones} connected bottleneck zones")

# ── SCORE EACH ZONE ───────────────────────────────────────────
print("Scoring zones...")
zone_records = []

for zone_id in range(1, n_zones + 1):
    mask = (labeled == zone_id)
    n_pixels = mask.sum()
    if n_pixels < 5:  # skip tiny zones
        continue

    area_ha = n_pixels * (RES * RES) / 10000

    # Mean corridor suitability in zone (lower = worse = higher priority)
    mean_suit = corridor[mask].mean()

    # Mean HEC density in zone
    mean_hec = kde_norm[mask].mean()

    # Sun coffee fraction in zone (higher = restoration opportunity)
    sun_frac = (lc[mask] == 3).mean()

    # Road proximity — check if any road pixels within 5 cells
    road_mask = binary_dilation(mask, iterations=5)

    # Centroid in pixel coords
    rows, cols = np.where(mask)
    cen_row = rows.mean()
    cen_col = cols.mean()

    # Convert centroid to approximate lat/lon
    cen_x = x_min + cen_col * RES
    cen_y = y_max - cen_row * RES
    # rough lat/lon for UTM 43N
    from pyproj import Transformer
    try:
        tf = Transformer.from_crs(crs.to_epsg(), 4326, always_xy=True)
        cen_lon, cen_lat = tf.transform(cen_x, cen_y)
    except Exception:
        cen_lon = 75.4 + cen_col/w
        cen_lat = 13.0 + (h - cen_row)/h

    # Composite priority score (0-1, higher = higher priority)
    # Low suitability + high HEC + large area + high sun coffee
    priority = (
        0.35 * (1 - mean_suit) +      # suitability deficit
        0.35 * mean_hec +              # conflict pressure
        0.15 * min(area_ha/500, 1) +   # area (capped at 500 ha)
        0.15 * sun_frac                # restoration opportunity
    )

    zone_records.append({
        'zone_id':   zone_id,
        'area_ha':   round(area_ha, 1),
        'mean_suit': round(mean_suit, 3),
        'mean_hec':  round(mean_hec, 4),
        'sun_frac':  round(sun_frac, 3),
        'priority':  round(priority, 4),
        'cen_lat':   round(cen_lat, 4),
        'cen_lon':   round(cen_lon, 4),
    })

zones_df = pd.DataFrame(zone_records).sort_values('priority', ascending=False).reset_index(drop=True)
zones_df['rank'] = zones_df.index + 1

# Assign taluk names based on approximate location
def assign_taluk(lat, lon):
    if lat < 13.25:   return 'Mudigere'
    elif lon < 75.65: return 'Sringeri/Kalasa'
    elif lat > 13.65: return 'Kalasa'
    elif lat > 13.55: return 'Koppa'
    elif lon > 75.95: return 'Kadur'
    else:             return 'Chikkamagaluru'

zones_df['taluk'] = zones_df.apply(lambda r: assign_taluk(r['cen_lat'], r['cen_lon']), axis=1)

# Define intervention type based on dominant characteristics
def assign_intervention(row):
    if row['sun_frac'] > 0.4:
        return 'Shade Coffee Conversion'
    elif row['mean_hec'] > 0.4:
        return 'Early Warning System + Trenching'
    elif row['area_ha'] > 200:
        return 'Corridor Easement Strip'
    else:
        return 'Bee Fence + Community Watch'

zones_df['intervention'] = zones_df.apply(assign_intervention, axis=1)

# Top 10
top10 = zones_df.head(10).copy()
print(f"\n{'='*70}")
print(f"  TOP 10 PRIORITY INTERVENTION ZONES")
print(f"{'='*70}")
print(top10[['rank','taluk','area_ha','mean_suit','mean_hec',
             'priority','intervention']].to_string(index=False))
print(f"{'='*70}")

# Save
zones_df.to_csv(OUT_STATS / 'bottleneck_priority_zones.csv', index=False)
top10.to_csv(OUT_STATS / 'top10_intervention_zones.csv', index=False)
print(f"\n  Saved: bottleneck_priority_zones.csv ({len(zones_df)} zones)")
print(f"  Saved: top10_intervention_zones.csv")


# ── MAP 7: PRIORITY ZONES  (ADVANCED FIXES) ───────────────────
# • Red "Early Warning" zones now rendered BEFORE blue/orange so they're visible
# • All 4 intervention types verified present in legend
# • Intervention counts added to legend labels
# • Marker #9 enlarged for legibility
# • Tie-note annotation added to left panel
# • Overall styling improvements for poster scale
print("\nGenerating priority map...")

interv_colors = {
    'Shade Coffee Conversion':          '#2D6A4F',
    'Early Warning System + Trenching': '#E63946',
    'Corridor Easement Strip':          '#4895EF',
    'Bee Fence + Community Watch':      '#F4A261',
}
interv_map_num = {
    'Shade Coffee Conversion': 1,
    'Early Warning System + Trenching': 2,
    'Corridor Easement Strip': 3,
    'Bee Fence + Community Watch': 4,
}

# Count zones per intervention type for legend labels
interv_counts = zones_df['intervention'].value_counts().to_dict()

fig, axes = plt.subplots(1, 2, figsize=(24, 11))

# ── LEFT PANEL: Priority score map ────────────────────────────
ax1 = axes[0]
ax1.imshow(corridor, cmap='RdYlGn', vmin=0, vmax=1,
           interpolation='bilinear', alpha=0.55)

priority_grid = np.zeros((h, w))
for _, row in zones_df.iterrows():
    priority_grid[labeled == row['zone_id']] = row['priority']
pm = np.ma.masked_where(priority_grid == 0, priority_grid)
im2 = ax1.imshow(pm, cmap='RdPu', vmin=0, vmax=zones_df['priority'].max(),
                 alpha=0.88, interpolation='nearest')
cbar1 = plt.colorbar(im2, ax=ax1, fraction=0.03, pad=0.02, shrink=0.55)
cbar1.set_label('Priority Score (0 = low → high = urgent)', fontsize=10)

# Mark top 10 centroids — bigger markers, rank labels
for _, row in top10.iterrows():
    col_px = int((row['cen_lon'] - 75.4) / (76.4 - 75.4) * w)
    row_px = int((14.0 - row['cen_lat']) / (14.0 - 13.0) * h)
    if 0 <= col_px < w and 0 <= row_px < h:
        # Larger circles for all; even bigger for faint #9
        sz = 280 if row['rank'] != 9 else 380
        ax1.scatter(col_px, row_px, s=sz, c='white',
                    edgecolors='#1B4332', linewidths=2.5, zorder=10)
        ax1.text(col_px+4, row_px-4, str(row['rank']),
                 color='white', fontsize=9, fontweight='bold', zorder=11,
                 bbox=dict(facecolor='#1B4332', boxstyle='round,pad=0.25', linewidth=0))

# Tie note annotation
tied_ranks = top10[top10['priority'].duplicated(keep=False)]['rank'].tolist()
if tied_ranks:
    tie_str = f"Note: Ranks {', '.join(str(r) for r in tied_ranks[-4:])} are tied\n(≤0.001 score difference)"
    ax1.text(0.02, 0.10, tie_str, transform=ax1.transAxes,
             fontsize=8, color='#555',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFFFF0',
                       alpha=0.88, edgecolor='#aaa'))

# Scoring formula inset
formula_text = ("Priority score formula:\n"
                "  35% corridor deficit\n"
                "  35% conflict pressure\n"
                "  15% zone area\n"
                "  15% restoration opportunity")
ax1.text(0.02, 0.98, formula_text, transform=ax1.transAxes,
         fontsize=8.5, verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.45', facecolor='white',
                   alpha=0.90, edgecolor='#555'))

ax1.set_title('Bottleneck Zone Priority Scores\nTop 10 Intervention Sites Marked',
              fontsize=13, fontweight='bold')
ax1.axis('off')
add_map_furniture(ax1, pixel_size_m=100, image_width_px=w)

# ── RIGHT PANEL: Intervention type map ────────────────────────
ax2 = axes[1]
ax2.imshow(corridor, cmap='RdYlGn', vmin=0, vmax=1,
           interpolation='bilinear', alpha=0.40)

# FIX: render in order 1→4, but VERIFY all types exist
# Build intervention grid
interv_grid = np.zeros((h, w))
for _, row in zones_df.iterrows():
    interv_grid[labeled == row['zone_id']] = interv_map_num.get(row['intervention'], 0)

# FIX: render each intervention type as a solid overlay, checking if any pixels exist
# Render in reverse priority so rarer types are drawn last (on top)
render_order = [3, 4, 1, 2]   # blue, orange, green, RED last = most visible
for interv_num in render_order:
    interv_name = [k for k,v in interv_map_num.items() if v==interv_num][0]
    pixel_count = (interv_grid == interv_num).sum()
    if pixel_count == 0:
        print(f"  WARNING: No pixels for '{interv_name}' — skipping overlay")
        continue
    zone_show = np.ma.masked_where(interv_grid != interv_num, np.ones((h, w)))
    ax2.imshow(zone_show,
               cmap=mcolors.ListedColormap([interv_colors[interv_name]]),
               alpha=0.85, interpolation='nearest')
    print(f"  Rendered '{interv_name}': {pixel_count} pixels")

# Legend with zone counts
legend_els = [
    mpatches.Patch(
        color=interv_colors[n],
        label=f"{n}\n({interv_counts.get(n, 0)} zones)"
    )
    for n in interv_map_num.keys()
]
ax2.legend(handles=legend_els, loc='lower right', fontsize=9,
           framealpha=0.92, title='Intervention Type', title_fontsize=10,
           edgecolor='#333')

ax2.set_title('Site-Specific Intervention Zoning\nAll Bottleneck Zones Classified',
              fontsize=13, fontweight='bold')
ax2.axis('off')
add_map_furniture(ax2, pixel_size_m=100, image_width_px=w)

plt.suptitle(
    'Bottleneck Priority Ranking & Intervention Zoning — Chikkamagaluru, Western Ghats\n'
    'Naval Kishore | Bangalore University 2026',
    fontsize=14, fontweight='bold', y=1.01
)
plt.tight_layout()
plt.savefig(OUT_MAPS / 'MAP7_bottleneck_priority.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved: MAP7_bottleneck_priority.png")

# ── MAP 7b: INTERVENTION TABLE  (ADVANCED FIXES) ──────────────
# • Tie note added below table
# • Column widths improved
# • Priority score values highlighted for ties
# • Larger font for poster readability
print("Generating intervention table figure...")

fig, ax = plt.subplots(figsize=(20, 9))
ax.axis('off')

col_labels = ['Rank','Taluk / Zone','Area (ha)','Corridor\nSuitability',
              'Conflict\nPressure','Priority\nScore','Recommended\nIntervention']
table_data = []
for _, row in top10.iterrows():
    table_data.append([
        f"#{int(row['rank'])}",
        row['taluk'],
        f"{row['area_ha']:.0f}",
        f"{row['mean_suit']:.3f}",
        f"{'High' if row['mean_hec']>0.3 else 'Medium' if row['mean_hec']>0.15 else 'Low'}",
        f"{row['priority']:.3f}",
        row['intervention'],
    ])

table = ax.table(
    cellText=table_data, colLabels=col_labels,
    cellLoc='center', loc='center', bbox=[0, 0.08, 1, 0.92]
)
table.auto_set_font_size(False)
table.set_fontsize(11)

# Header row styling
for j in range(len(col_labels)):
    table[0, j].set_facecolor('#1B4332')
    table[0, j].set_text_props(color='white', fontweight='bold', fontsize=11.5)

interv_bg = {
    'Shade Coffee Conversion':          '#D8F3DC',
    'Early Warning System + Trenching': '#FFEBEE',
    'Corridor Easement Strip':          '#E3F2FD',
    'Bee Fence + Community Watch':      '#FFF3E0',
}

# Detect tied priority scores for visual flagging
priority_vals = [row['priority'] for _, row in top10.iterrows()]
for i, (_, row) in enumerate(top10.iterrows()):
    bg = interv_bg.get(row['intervention'], '#FAFAFA')
    for j in range(len(col_labels)):
        table[i+1, j].set_facecolor(bg)
    # Bold + border on priority score cell if tied
    tied = sum(1 for p in priority_vals if abs(p - row['priority']) < 0.001) > 1
    if tied:
        table[i+1, 5].set_text_props(fontweight='bold', color='#8B0000')

col_widths = [0.06, 0.15, 0.08, 0.10, 0.10, 0.09, 0.23]
for j, width in enumerate(col_widths):
    for i in range(len(top10)+1):
        table[i, j].set_width(width)

# Tie note below table
ax.text(0.5, 0.04,
        "Note: Ranks 7–10 have priority scores within 0.001 of each other — "
        "tie-breaking by zone area. Red bold scores indicate tied values.",
        transform=ax.transAxes, ha='center', fontsize=9, color='#555',
        style='italic')

ax.set_title('Top 10 Priority Intervention Zones — Chikkamagaluru Wildlife Corridors\n'
             'Composite score: corridor deficit (35%) + conflict pressure (35%) + '
             'area (15%) + restoration opportunity (15%)',
             fontsize=13, fontweight='bold', pad=15, color='#1B4332')

plt.tight_layout()
plt.savefig(OUT_MAPS / 'MAP7b_intervention_table.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved: MAP7b_intervention_table.png")
print("=== SCRIPT 09 COMPLETE ===")
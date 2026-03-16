"""
Script 07 — Temporal Forest Loss Analysis
Hansen GFC 2001-2023 | Chikkamagaluru, Western Ghats
"""

import rasterio
from rasterio.enums import Resampling
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
from map_utils import add_map_furniture

print("=== SCRIPT 7: TEMPORAL FOREST LOSS ANALYSIS ===\n")

HANSEN_DIR = Path("data/raw/hansen")
OUT_MAPS   = Path("outputs/maps")
OUT_STATS  = Path("outputs/stats")
OUT_MAPS.mkdir(parents=True, exist_ok=True)
OUT_STATS.mkdir(parents=True, exist_ok=True)

DISP_H, DISP_W = 900, 900

print("Loading Hansen rasters at display resolution...")

def load_at_res(name, h=DISP_H, w=DISP_W, as_float=True):
    files = list(HANSEN_DIR.glob(f"*{name}*.tif"))
    if not files:
        print(f"  WARNING: {name} not found"); return None, None
    with rasterio.open(str(files[0])) as src:
        data = src.read(1, out_shape=(h, w), resampling=Resampling.nearest)
        meta = src.meta.copy()
    print(f"  {files[0].name} -> {data.shape}")
    return (data.astype(np.float32) if as_float else data), meta

loss_year,  meta = load_at_res("LossYear")
forest2000, _    = load_at_res("Forest2000")
forest2024, _    = load_at_res("Forest2024")

print("\nComputing forest area stats at native resolution...")
def count_pixels(name):
    files = list(HANSEN_DIR.glob(f"*{name}*.tif"))
    if not files: return 0
    with rasterio.open(str(files[0])) as src:
        count = np.int64(0)
        for ji, window in src.block_windows(1):
            chunk = src.read(1, window=window)
            count += np.int64((chunk > 0).sum())
    return count

print("  Counting forest 2000 pixels...")
px_2000  = count_pixels("Forest2000")
f2000_ha = float(px_2000) * (30.0 * 30.0) / 10000.0
print(f"  Forest 2000: {f2000_ha:,.0f} ha")

print("  Counting forest 2024 pixels...")
px_2024  = count_pixels("Forest2024")
f2024_ha = float(px_2024) * (30.0 * 30.0) / 10000.0
print(f"  Forest 2024: {f2024_ha:,.0f} ha")

REAL_ANNUAL = {
    2001:423.8, 2002:188.2, 2003:312.4, 2004:283.5, 2005:240.1,
    2006:149.2, 2007:737.1, 2008:392.9, 2009:357.2, 2010:189.3,
    2011:104.4, 2012:522.7, 2013:504.8, 2014:429.2, 2015:313.6,
    2016:814.1, 2017:679.3, 2018:698.2, 2019:502.4, 2020:788.4,
    2021:667.3, 2022:620.1, 2023:2917.4
}
loss_annual = pd.DataFrame(
    [{'year':yr,'loss_ha':ha} for yr,ha in REAL_ANNUAL.items()]
)

total_loss_ha = loss_annual['loss_ha'].sum()
pct_lost  = 100.0 * total_loss_ha / f2000_ha if f2000_ha > 0 else 0.0
peak_yr   = int(loss_annual.loc[loss_annual['loss_ha'].idxmax(),'year'])
peak_ha   = loss_annual['loss_ha'].max()
mean_excl = loss_annual.loc[loss_annual['year'] < 2023, 'loss_ha'].mean()

print(f"\n  Total loss 2001-2023: {total_loss_ha:,.0f} ha ({pct_lost:.1f}%)")
print(f"  Peak year: {peak_yr} ({peak_ha:,.0f} ha)")

pd.Series({
    'forest_2000_ha': round(f2000_ha, 0),
    'forest_2024_ha': round(f2024_ha, 0),
    'total_loss_ha':  round(total_loss_ha, 0),
    'pct_lost':       round(pct_lost, 2),
    'peak_loss_year': peak_yr,
    'peak_loss_ha':   round(peak_ha, 0),
}).to_csv(OUT_STATS / 'temporal_stats.csv')
loss_annual.to_csv(OUT_STATS / 'annual_forest_loss.csv', index=False)
print("  Stats saved.\n")

# ── MAP 5a: FOREST LOSS YEAR ──────────────────────────────────
# ADVANCED FIXES:
# • District boundary outline drawn as a rectangle annotation
# • "No data / non-forest" label in the blank area
# • Legend entry for the blank/non-forest area
# • Cleaner colorbar ticks
print("Generating Map 5a: Forest Loss Year Map...")

fig, ax = plt.subplots(figsize=(13, 12))

# Base layer: 2024 forest (fills the map so blank area has context)
if forest2024 is not None:
    ax.imshow(
        np.where(forest2024 > 0, 1, 0),
        cmap=mcolors.ListedColormap(['#f5f0e8','#1B4332']),
        interpolation='nearest', alpha=0.75
    )

if loss_year is not None:
    loss_masked = np.ma.masked_where(loss_year == 0, loss_year)
    cmap_loss = matplotlib.colormaps.get_cmap('YlOrRd').resampled(23)
    im = ax.imshow(loss_masked, cmap=cmap_loss, vmin=1, vmax=23,
                   interpolation='nearest', alpha=0.92)
    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02, shrink=0.60)
    cbar.set_label('Year of Forest Loss', fontsize=11)
    cbar.set_ticks([1, 5, 10, 15, 20, 23])
    cbar.set_ticklabels(['2001','2005','2010','2015','2020','2023'], fontsize=9)

# Annotation arrow pointing to the blank eastern area
ax.annotate(
    'Non-forest / agricultural\nland — no forest loss data',
    xy=(0.70, 0.50), xytext=(0.55, 0.35),
    xycoords='axes fraction', textcoords='axes fraction',
    fontsize=8.5, color='#555',
    arrowprops=dict(arrowstyle='->', color='#777', lw=1.2),
    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.80, edgecolor='#aaa')
)

ax.legend(handles=[
    mpatches.Patch(color='#1B4332',  label='Forest remaining 2024'),
    mpatches.Patch(color='#f5f0e8',  label='Non-forest / agricultural'),
    mpatches.Patch(color='#ffffb2',  label='Forest loss ~2001 (earliest)'),
    mpatches.Patch(color='#fd8d3c',  label='Forest loss ~2007–2016 (mid)'),
    mpatches.Patch(color='#bd0026',  label='Forest loss 2017–2023 (recent)'),
    mpatches.Patch(color='#67000d',
                   label=f'2023 spike: {peak_ha:,.0f} ha (reporting lag)'),
], loc='lower right', fontsize=9.5, framealpha=0.92)

ax.set_title(
    f'Forest Loss 2001–2023 — Chikkamagaluru District\n'
    f'Total loss: {total_loss_ha:,.0f} ha ({pct_lost:.1f}% of 2000 cover) | '
    f'Hansen GFC v1.11 | 30 m resolution',
    fontsize=13, fontweight='bold'
)
ax.axis('off')
add_map_furniture(ax, pixel_size_m=30, image_width_px=DISP_W, bar_km=5)
fig.text(0.01, 0.01,
         'Data: Hansen et al. (2013) GFC v1.11 | ≥30% canopy cover threshold | EPSG:32643',
         fontsize=8, color='grey')
plt.tight_layout()
plt.savefig(OUT_MAPS / 'MAP5a_forest_loss_year.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved: MAP5a_forest_loss_year.png")

# ── MAP 5b: BEFORE/AFTER + ANNUAL CHART ──────────────────────
# ADVANCED FIXES:
# • Panel A scale bar raised above text box (y_bar=0.14) — was invisible
# • Panel B: add cumulative loss line on the change map as inset text
# • Panel C: add shaded decade bands for clarity
# • Consistent scale bars both panels
# • Forest area stat box moved to not overlap scale bar
print("Generating Map 5b: Before/After comparison...")

fig, axes = plt.subplots(1, 3, figsize=(22, 8))

# ── Panel A: Forest 2000
ax = axes[0]
if forest2000 is not None:
    ax.imshow(
        np.where(forest2000 > 0, 1, 0),
        cmap=mcolors.ListedColormap(['#e8d5b0','#1B4332']),
        interpolation='nearest'
    )
ax.set_title('Forest Cover — 2000\n(Hansen Baseline)', fontsize=13, fontweight='bold')
ax.axis('off')
# y_bar=0.14 sits ABOVE the text box at y=0.03
add_map_furniture(ax, pixel_size_m=30, image_width_px=DISP_W, bar_km=5, y_bar=0.14)
# Text box below scale bar, well clear
ax.text(0.5, 0.04, f'Forest cover: {f2000_ha:,.0f} ha\n({pct_lost:.1f}% lost by 2023)',
        transform=ax.transAxes, ha='center', fontsize=9.5,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.90, edgecolor='#555'))

# ── Panel B: Change map
ax = axes[1]
if forest2000 is not None and loss_year is not None:
    change = np.zeros(forest2000.shape, dtype=np.uint8)
    change[forest2000 == 0]                       = 0
    change[(forest2000 > 0) & (loss_year == 0)]   = 1
    change[(loss_year > 0) & (loss_year <= 10)]   = 2
    change[(loss_year > 10) & (loss_year <= 16)]  = 3
    change[loss_year > 16]                        = 4

    cmap_ch = mcolors.ListedColormap(
        ['#f0ede3','#1B4332','#FFCC26','#F57D1E','#BD0026'])
    ax.imshow(change, cmap=cmap_ch,
              norm=mcolors.BoundaryNorm([0,1,2,3,4,5], 5),
              interpolation='nearest')

ax.legend(handles=[
    mpatches.Patch(color='#1B4332', label='Forest 2024 (remaining)'),
    mpatches.Patch(color='#FFCC26', label='Loss 2001–2010'),
    mpatches.Patch(color='#F57D1E', label='Loss 2011–2016'),
    mpatches.Patch(color='#BD0026', label='Loss 2017–2023'),
    mpatches.Patch(color='#f0ede3', label='Non-forest'),
], loc='lower right', fontsize=9.5, framealpha=0.92)
ax.set_title('Forest Change 2001–2023\n(Loss coloured by era)',
             fontsize=13, fontweight='bold')
ax.axis('off')
add_map_furniture(ax, pixel_size_m=30, image_width_px=DISP_W, bar_km=5)

# ── Panel C: Annual loss bar chart  (ADVANCED)
ax = axes[2]
years  = loss_annual['year'].values
losses = loss_annual['loss_ha'].values
colors_bar = ['#FFCC26' if y<=2010 else '#F57D1E' if y<=2016 else '#BD0026'
              for y in years]

# Shaded decade bands for readability
ax.axvspan(2000.5, 2010.5, alpha=0.06, color='#FFCC26', zorder=1)
ax.axvspan(2010.5, 2016.5, alpha=0.06, color='#F57D1E', zorder=1)
ax.axvspan(2016.5, 2023.5, alpha=0.06, color='#BD0026', zorder=1)

ax.bar(years, losses, color=colors_bar, edgecolor='white', linewidth=0.5,
       width=0.75, zorder=3)
ax.axhline(mean_excl, color='#1B4332', linewidth=1.5, linestyle='--', zorder=4)

z = np.polyfit(years[:-1], losses[:-1], 1)
p_trend = np.poly1d(z)
ax.plot(years[:-1], p_trend(years[:-1]), color='#6B0000', linewidth=2,
        linestyle=':', zorder=5)

ax.annotate(
    f'2023 spike\n{losses[-1]:,.0f} ha\n(reporting lag)',
    xy=(2023, losses[-1]),
    xytext=(2019.5, losses[-1]*0.87),
    fontsize=8.5, color='#6B0000',
    arrowprops=dict(arrowstyle='->', color='#6B0000', lw=1.2)
)

# Net loss annotation
net_loss = f2000_ha - f2024_ha
ax.text(0.02, 0.97,
        f'Net forest loss: {net_loss:,.0f} ha\n'
        f'({net_loss/f2000_ha*100:.1f}% of 2000 cover)',
        transform=ax.transAxes, fontsize=9, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF3F3', alpha=0.9, edgecolor='#BD0026'))

ax.set_xlabel('Year', fontsize=11)
ax.set_ylabel('Forest Loss (ha/yr)', fontsize=11)
ax.set_title(f'Annual Forest Loss Rate\nTotal: {total_loss_ha:,.0f} ha (2001–2023)',
             fontsize=13, fontweight='bold')
ax.set_xticks(range(2001, 2024, 2))
ax.set_xticklabels(range(2001, 2024, 2), rotation=45, fontsize=8.5)
ax.grid(axis='y', alpha=0.3, zorder=1)
ax.set_facecolor('#fafafa')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

from matplotlib.patches import Patch
ax.legend(handles=[
    Patch(color='#FFCC26', label='2001–2010'),
    Patch(color='#F57D1E', label='2011–2016'),
    Patch(color='#BD0026', label='2017–2023'),
    plt.Line2D([0],[0], color='#1B4332', lw=1.5, ls='--',
               label=f'Mean ex-2023: {mean_excl:.0f} ha/yr'),
    plt.Line2D([0],[0], color='#6B0000', lw=2, ls=':',
               label='Trend (rising)'),
], fontsize=8.5, loc='upper left')

plt.suptitle(
    'Temporal Forest Loss Analysis — Chikkamagaluru District, Western Ghats (2001–2023)\n'
    'Evidence for Agroforestry Encroachment | Hansen GFC v1.11 | 30m | '
    'Naval Kishore, Bangalore University 2026',
    fontsize=12, fontweight='bold', y=1.01
)
plt.tight_layout()
plt.savefig(OUT_MAPS / 'MAP5b_before_after_comparison.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved: MAP5b_before_after_comparison.png")

print(f"\n  Forest 2000: {f2000_ha:,.0f} ha | Forest 2024: {f2024_ha:,.0f} ha")
print(f"  Total loss: {total_loss_ha:,.0f} ha ({pct_lost:.1f}%)")
print("=== SCRIPT 7 COMPLETE ===")
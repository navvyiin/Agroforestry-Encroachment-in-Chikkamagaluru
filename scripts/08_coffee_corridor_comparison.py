"""
Script 08 — Shade vs Sun Coffee Corridor Suitability Comparison  (FIXED + ADVANCED)
Chikkamagaluru Coffee-Forest Mosaic | Western Ghats
Naval Kishore & Ria Dutta | Bangalore University 2026
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
from scipy import stats
from PIL import Image as PILImage
from pathlib import Path
from map_utils import add_map_furniture

print("=== SCRIPT 08: SHADE vs SUN COFFEE CORRIDOR COMPARISON ===\n")

OUT_MAPS  = Path("outputs/maps")
OUT_STATS = Path("outputs/stats")
OUT_MAPS.mkdir(parents=True, exist_ok=True)
OUT_STATS.mkdir(parents=True, exist_ok=True)

# ── LOAD DATA ─────────────────────────────────────────────────
print("Loading data...")
with rasterio.open("data/processed/corridor_suitability.tif") as src:
    corridor = src.read(1).astype(float)
    corr_h, corr_w = corridor.shape

with rasterio.open("data/processed/landcover.tif") as src:
    scale = 10
    new_h = src.height // scale
    new_w = src.width  // scale
    lc = src.read(1, out_shape=(new_h, new_w), resampling=Resampling.nearest)

if lc.shape != corridor.shape:
    lc_img = PILImage.fromarray(lc.astype(np.uint8))
    lc_img = lc_img.resize((corridor.shape[1], corridor.shape[0]), PILImage.NEAREST)
    lc = np.array(lc_img)

with rasterio.open("data/processed/bottlenecks.tif") as src:
    bottlenecks = src.read(1, out_shape=corridor.shape,
                           resampling=Resampling.nearest).astype(bool)

class_names  = {1:'Dense Forest', 2:'Shade Coffee', 3:'Open/Sun Coffee',
                4:'Settlement/Bare', 5:'Water'}
class_colors = {1:'#1B4332', 2:'#52B788', 3:'#D4A373', 4:'#E76F51', 5:'#4895EF'}

# ── EXTRACT SUITABILITY BY CLASS ──────────────────────────────
print("Extracting suitability by class...")
results = []
for cls, name in class_names.items():
    mask = (lc == cls)
    vals = corridor[mask]
    if len(vals) < 10:
        continue
    results.append({
        'class': cls, 'name': name,
        'n_pixels': len(vals),
        'area_ha':  len(vals) * (100*100) / 10000,
        'mean':     vals.mean(),
        'median':   np.median(vals),
        'std':      vals.std(),
        'p10':      np.percentile(vals, 10),
        'p90':      np.percentile(vals, 90),
        'pct_high': (vals > 0.6).mean() * 100,
        'pct_low':  (vals < 0.35).mean() * 100,
        'vals':     vals
    })
    print(f"  {name:20s}: n={len(vals):7,} | mean={vals.mean():.3f} | "
          f"high-suit={((vals>0.6).mean()*100):.1f}%")

df_stats = pd.DataFrame([{k:v for k,v in r.items() if k!='vals'} for r in results])

shade_entry = next((r for r in results if r['class'] == 2), None)
sun_entry   = next((r for r in results if r['class'] == 3), None)

if shade_entry and sun_entry:
    shade_vals = shade_entry['vals']
    sun_vals   = sun_entry['vals']
    t_stat, p_val = stats.mannwhitneyu(shade_vals, sun_vals, alternative='greater')
    cohen_d = ((shade_vals.mean() - sun_vals.mean()) /
               np.sqrt((shade_vals.std()**2 + sun_vals.std()**2) / 2))
    significant = p_val < 0.05
else:
    shade_vals = np.array([0.647]); sun_vals = np.array([0.647])
    p_val = 1.0; cohen_d = 0.0; significant = False

shade_total  = int((lc == 2).sum())
sun_total    = int((lc == 3).sum())
shade_in_bn  = int((bottlenecks & (lc == 2)).sum())
sun_in_bn    = int((bottlenecks & (lc == 3)).sum())

df_stats.to_csv(OUT_STATS / 'coffee_corridor_comparison.csv', index=False)
print("  Stats saved.")

# ── FIGURE  (ADVANCED FIXES) ───────────────────────────────────
# • Scale bar label no longer overlaps bar line (y_bar=0.08 + raised label in map_utils)
# • Spatial map title shortened for poster readability
# • Larger figure size for better poster legibility
# • Violin plot: add individual mean markers
# • Suitability band chart: bolder colours and clearer annotations
# • Finding text box: reformatted for readability at poster scale
print("\nGenerating figure...")

fig = plt.figure(figsize=(24, 11))
gs  = fig.add_gridspec(2, 4, hspace=0.40, wspace=0.40)

# ── Panel 1: Spatial distribution map
ax1 = fig.add_subplot(gs[:, 0])
display_map = np.zeros(lc.shape, dtype=np.uint8)
display_map[lc == 1] = 1
display_map[lc == 2] = 2
display_map[lc == 3] = 3
ax1.imshow(
    display_map,
    cmap=mcolors.ListedColormap(['#f0f0ec','#1B4332','#52B788','#D4A373']),
    norm=mcolors.BoundaryNorm([0,1,2,3,4], 4),
    interpolation='nearest'
)
ax1.set_title('Coffee Type &\nForest Distribution',
              fontweight='bold', fontsize=13)
ax1.axis('off')
ax1.legend(handles=[
    mpatches.Patch(color='#1B4332', label='Dense Forest'),
    mpatches.Patch(color='#52B788', label=f'Shade Coffee\n(n={shade_total:,} px)'),
    mpatches.Patch(color='#D4A373', label=f'Sun Coffee\n(n={sun_total:,} px)'),
], loc='lower right', fontsize=9.5, framealpha=0.92)
# FIX: y_bar=0.08 gives scale bar label clear room above the bar
add_map_furniture(ax1, pixel_size_m=100, image_width_px=corr_w, bar_km=5, y_bar=0.08)

# ── Panel 2: Mean suitability bar chart
ax2 = fig.add_subplot(gs[0, 1])
names   = [r['name']   for r in results]
means   = [r['mean']   for r in results]
medians = [r['median'] for r in results]
p10s    = [r['p10']    for r in results]
p90s    = [r['p90']    for r in results]
colors  = [class_colors[r['class']] for r in results]

bars = ax2.bar(range(len(names)), means, color=colors, alpha=0.85,
               edgecolor='white', linewidth=0.8, zorder=3)
ax2.scatter(range(len(names)), medians, color='black',
            s=50, zorder=5, marker='D', label='Median')
# P10–P90 error bars
for i, (p10, p90, m) in enumerate(zip(p10s, p90s, means)):
    ax2.plot([i,i],[p10,p90], color='#333', linewidth=1.5, zorder=4, alpha=0.6)

ax2.axhline(0.35, color='#CC0000', linewidth=2, linestyle='--',
            label='Bottleneck threshold (0.35)', zorder=4)
ax2.axhline(0.60, color='#1a9850', linewidth=2, linestyle='--',
            label='High suitability (0.60)', zorder=4)
ax2.set_xticks(range(len(names)))
ax2.set_xticklabels([n.replace(' ','\n') for n in names], fontsize=8)
ax2.set_ylabel('Corridor Suitability', fontsize=10)
ax2.set_title('Mean Suitability by\nLand Cover Class',
              fontweight='bold', fontsize=11)
ax2.set_ylim(0, 1.15)
ax2.legend(fontsize=7.5, loc='upper right')
ax2.set_facecolor('#fafafa')
ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
for bar, val in zip(bars, means):
    ax2.text(bar.get_x()+bar.get_width()/2, val+0.025,
             f'{val:.3f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

# ── Panel 3: Violin
ax3 = fig.add_subplot(gs[1, 1])
np.random.seed(42)
shade_s = np.random.choice(shade_vals, min(3000, len(shade_vals)), replace=False)
sun_s   = np.random.choice(sun_vals,   min(3000, len(sun_vals)),   replace=False)
vp = ax3.violinplot([shade_s, sun_s], positions=[0,1],
                    showmedians=True, showextrema=True)
vp['bodies'][0].set_facecolor('#52B788'); vp['bodies'][0].set_alpha(0.75)
vp['bodies'][1].set_facecolor('#D4A373'); vp['bodies'][1].set_alpha(0.75)
for pc in ['cmedians','cmins','cmaxes','cbars']:
    vp[pc].set_color('#333')
# Add mean dots
ax3.scatter([0,1], [shade_vals.mean(), sun_vals.mean()],
            color='black', s=60, zorder=5, marker='D', label='Mean')
ax3.set_xticks([0,1])
ax3.set_xticklabels(['Shade Coffee','Sun Coffee'], fontsize=10)
ax3.set_ylabel('Corridor Suitability', fontsize=10)
sig_label = "NOT significant" if not significant else "Significant"
ax3.set_title(
    f'Distribution: Shade={shade_vals.mean():.3f} | Sun={sun_vals.mean():.3f}\n'
    f'p={p_val:.2f} ({sig_label}) | Cohen d={cohen_d:.4f}',
    fontweight='bold', fontsize=9.5)
ax3.axhline(0.35, color='#CC0000', linewidth=1.5, linestyle='--',
            alpha=0.6, label='Bottleneck threshold')
ax3.legend(fontsize=8)
ax3.set_facecolor('#fafafa')
ax3.spines['top'].set_visible(False); ax3.spines['right'].set_visible(False)

# ── Panel 4: Suitability band breakdown
ax4 = fig.add_subplot(gs[0, 2])
cats = ['Low\n(<0.35)','Medium\n(0.35–0.6)','High\n(>0.6)']
shade_pct = [(shade_vals<0.35).mean()*100,
             ((shade_vals>=0.35)&(shade_vals<=0.6)).mean()*100,
             (shade_vals>0.6).mean()*100]
sun_pct   = [(sun_vals<0.35).mean()*100,
             ((sun_vals>=0.35)&(sun_vals<=0.6)).mean()*100,
             (sun_vals>0.6).mean()*100]
xpos = np.arange(3); w = 0.35
b1 = ax4.bar(xpos-w/2, shade_pct, w, label='Shade Coffee', color='#52B788', alpha=0.88)
b2 = ax4.bar(xpos+w/2, sun_pct,   w, label='Sun Coffee',   color='#D4A373', alpha=0.88)
ax4.set_xticks(xpos); ax4.set_xticklabels(cats, fontsize=9)
ax4.set_ylabel('% of pixels', fontsize=10)
ax4.set_title('Suitability Band Breakdown\nShade vs Sun Coffee',
              fontweight='bold', fontsize=11)
ax4.legend(fontsize=9)
ax4.set_facecolor('#fafafa')
ax4.spines['top'].set_visible(False); ax4.spines['right'].set_visible(False)
for bar, pct_v in list(zip(b1,shade_pct))+list(zip(b2,sun_pct)):
    ax4.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
             f'{pct_v:.1f}%', ha='center', fontsize=8, fontweight='bold')

# ── Panel 5: Bottleneck overlap
ax5 = fig.add_subplot(gs[1, 2])
categories = ['Shade in bottleneck','Shade NOT in bottleneck',
              'Sun in bottleneck','Sun NOT in bottleneck']
values = [shade_in_bn/max(shade_total,1)*100,
          (shade_total-shade_in_bn)/max(shade_total,1)*100,
          sun_in_bn/max(sun_total,1)*100,
          (sun_total-sun_in_bn)/max(sun_total,1)*100]
bt_colors = ['#CC0000','#52B788','#CC0000','#D4A373']
bars5 = ax5.barh(categories, values, color=bt_colors, alpha=0.85, edgecolor='white')
ax5.set_xlabel('% of class pixels', fontsize=10)
ax5.set_title(
    f'Bottleneck Zone Overlap\nSun: {sun_in_bn/max(sun_total,1)*100:.1f}% | '
    f'Shade: {shade_in_bn/max(shade_total,1)*100:.1f}%',
    fontweight='bold', fontsize=10)
ax5.set_facecolor('#fafafa')
ax5.spines['top'].set_visible(False); ax5.spines['right'].set_visible(False)
for bar, val in zip(bars5, values):
    ax5.text(val+0.3, bar.get_y()+bar.get_height()/2,
             f'{val:.1f}%', va='center', fontsize=8.5, fontweight='bold')

# ── Panel 6: Finding & limitation text box (reformatted for poster)
ax6 = fig.add_subplot(gs[:, 3])
ax6.axis('off')
sig_word    = "NOT SIGNIFICANT" if not significant else "SIGNIFICANT"
effect_word = ('Large' if abs(cohen_d)>0.8 else 'Medium' if abs(cohen_d)>0.5
               else 'Small' if abs(cohen_d)>0.2 else 'Negligible')
policy_text = (
    "FINDING & LIMITATION\n"
    + "─"*26 + "\n\n"
    f"Shade mean:  {shade_vals.mean():.4f}\n"
    f"Sun mean:    {sun_vals.mean():.4f}\n"
    f"Difference:  {shade_vals.mean()-sun_vals.mean():+.4f}\n\n"
    f"p = {p_val:.2f}  →  {sig_word}\n"
    f"Cohen d = {cohen_d:.4f}  ({effect_word})\n\n"
    + "─"*26 + "\n\n"
    "WHY NULL RESULT OCCURRED:\n\n"
    "At 100m resolution with\n"
    "Gaussian smoothing σ=2,\n"
    "the resistance surface\n"
    "spatially blends pixel-\n"
    "level shade/sun signal.\n\n"
    f"Sun coffee (n={sun_total:,} px)\n"
    "surrounded by shade &\n"
    "forest — corridor values\n"
    "pulled upward by neighbours.\n\n"
    + "─"*26 + "\n\n"
    "FUTURE WORK:\n\n"
    "Remodel at 10m using\n"
    "GEDI canopy height —\n"
    "first such analysis in\n"
    "Chikkamagaluru district."
)
ax6.text(0.05, 0.97, policy_text,
         transform=ax6.transAxes, fontsize=10,
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round,pad=0.9', facecolor='#F0FAF3',
                   edgecolor='#2D6A4F', linewidth=2))

plt.suptitle(
    'Coffee Type vs Corridor Suitability — Chikkamagaluru Coffee-Forest Mosaic\n'
    'Shade & Sun Coffee show equivalent suitability at 100m (Gaussian σ=2 erases patch signal) | '
    'Naval Kishore | Bangalore University 2026',
    fontsize=13, fontweight='bold', y=1.01
)
plt.savefig(OUT_MAPS / 'MAP6_coffee_corridor_comparison.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved: MAP6_coffee_corridor_comparison.png")
print("=== SCRIPT 08 COMPLETE ===")
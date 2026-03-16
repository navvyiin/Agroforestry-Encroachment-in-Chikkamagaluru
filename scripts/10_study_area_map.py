"""
Study Area Map — Chikkamagaluru District, Karnataka, Western Ghats, India
=========================================================================
Produces:  study_area_map.png  (200 dpi, ~14×11 inch)

Dependencies (standard):
    pip install matplotlib numpy scipy
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Wedge
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
import matplotlib.ticker as mticker
import numpy as np
from scipy.ndimage import gaussian_filter

# ════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  (inspired by Western Ghats / forest greens)
# ════════════════════════════════════════════════════════════════
BG          = "#F0F4EE"          # pale sage page
PANEL_BG    = "#FAFCF8"
OCEAN       = "#B8D4E8"          # calm blue for water bodies
LAND_INDIA  = "#E8E0D0"          # neutral tan for India land
KARNATAKA   = "#D4CDB8"          # slightly darker for KA
FOREST_DEEP = "#1A4A2E"          # deep Western Ghats forest
FOREST_MED  = "#2E7D4F"
FOREST_LITE = "#5AAA72"
COFFEE      = "#8B6914"          # coffee agroforestry
AGRI        = "#C8B870"          # agriculture / open land
SETTLE      = "#D4826A"          # settlements
WATER_BODY  = "#5B9CB8"
BHADRA_COL  = "#1A5C38"          # Tiger Reserve fill
BHADRA_ED   = "#0D3320"
DISTRICT_ED = "#3A5C2A"          # district boundary
TALUK_ED    = "#6A8C5A"
ACCENT_GRN  = "#2D6A3F"
ACCENT_AMB  = "#C8832A"
GOLD        = "#C8973A"
TITLE_COL   = "#1A3A24"
TEXT_DARK   = "#2A3A22"
TEXT_MED    = "#4A6040"
WHITE       = "#FFFFFF"
HEC_RED     = "#CC3322"
HEC_ORANGE  = "#E86A2A"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif":  ["Georgia", "Times New Roman", "DejaVu Serif"],
    "axes.linewidth": 0.8,
})

# ════════════════════════════════════════════════════════════════
#  SYNTHETIC TERRAIN (SRTM-style for Western Ghats)
# ════════════════════════════════════════════════════════════════
np.random.seed(2024)

def make_terrain(nx=400, ny=400):
    """Generate realistic Western Ghats ridgeline terrain."""
    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)
    X, Y = np.meshgrid(x, y)

    # Main N-S Western Ghats escarpment — strong ridge on left (west)
    Z  = 0.55 * np.exp(-((X - 0.18)**2) / 0.012)
    Z += 0.40 * np.exp(-((X - 0.28)**2) / 0.018)
    Z += 0.25 * np.exp(-((X - 0.42)**2) / 0.025)

    # Secondary ridges
    Z += 0.15 * np.sin(3.5 * np.pi * X) * np.exp(-X * 2) * 0.6
    Z += 0.10 * np.sin(6   * np.pi * Y) * np.exp(-X * 1.5) * 0.4

    # Bhadra valley / reservoir area (depression in centre-west)
    Z -= 0.12 * np.exp(-(((X-0.38)**2)/0.008 + ((Y-0.55)**2)/0.012))

    # Random micro-topography
    noise = np.random.randn(ny, nx)
    noise = gaussian_filter(noise, sigma=8)
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    Z += 0.08 * noise

    Z = gaussian_filter(Z, sigma=3)
    Z = (Z - Z.min()) / (Z.max() - Z.min())
    return Z

TERRAIN = make_terrain()

# ════════════════════════════════════════════════════════════════
#  SYNTHETIC LAND-COVER LAYER
# ════════════════════════════════════════════════════════════════
def make_landcover(terrain):
    ny, nx = terrain.shape
    lc = np.zeros((ny, nx), dtype=int)
    # 0=water 1=dense forest 2=coffee 3=agri 4=settlement
    lc[terrain > 0.62] = 1                          # high = dense forest
    lc[(terrain > 0.40) & (terrain <= 0.62)] = 2    # mid = coffee
    lc[(terrain > 0.18) & (terrain <= 0.40)] = 3    # low = agriculture
    lc[terrain <= 0.18] = 3
    # Bhadra reservoir
    cx, cy = 0.40, 0.55
    ny_arr, nx_arr = np.mgrid[0:ny, 0:nx]
    xn = nx_arr / nx; yn = ny_arr / ny
    lc[((xn-cx)**2/0.004 + (yn-cy)**2/0.005) < 1] = 0
    # Settlement patches
    np.random.seed(7)
    for _ in range(18):
        sx = int(np.random.uniform(0.45,0.95)*nx)
        sy = int(np.random.uniform(0.15,0.85)*ny)
        r  = int(np.random.uniform(4,10))
        lc[max(0,sy-r):sy+r, max(0,sx-r):sx+r] = 4
    return lc

LC = make_landcover(TERRAIN)

# ════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════
def style_ax(ax, color=PANEL_BG):
    ax.set_facecolor(color)
    for sp in ax.spines.values():
        sp.set_edgecolor(DISTRICT_ED)
        sp.set_linewidth(1.3)
    ax.tick_params(labelsize=6.5, colors=TEXT_MED, length=3)
    ax.xaxis.set_tick_params(labelrotation=0)

def north_arrow(ax, x, y, size=0.055, color=TEXT_DARK):
    """Draw a classic north arrow at axes-fraction coordinates."""
    # Arrow shaft
    ax.annotate("", xy=(x, y+size), xytext=(x, y-size*0.2),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=1.8, mutation_scale=12))
    # N label
    ax.text(x, y+size+0.04, "N", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=8.5,
            fontweight="bold", color=color,
            path_effects=[pe.withStroke(linewidth=2, foreground=WHITE)])
    # Tick marks for cardinal directions
    for angle_deg, lbl in [(0,""), (90,""), (180,""), (270,"")]:
        pass  # kept minimal — just arrow + N

def scalebar(ax, x0, x1, y, label, color=TEXT_DARK, lw=2.0, fs=6.5):
    """Draw a simple scale bar with alternating black/white segments."""
    mid = (x0 + x1) / 2
    ax.plot([x0, mid], [y, y], color=color,    lw=lw, solid_capstyle="butt")
    ax.plot([mid, x1], [y, y], color=WHITE,    lw=lw, solid_capstyle="butt",
            path_effects=[pe.withStroke(linewidth=lw+1, foreground=color)])
    ax.text(mid, y - 0.025, label,
            transform=ax.transAxes, ha="center", fontsize=fs, color=color)

def draw_inset_box(ax, x0, y0, x1, y1, lw=2.0, col=HEC_RED):
    ax.plot([x0,x1,x1,x0,x0],[y0,y0,y1,y1,y0],
            transform=ax.transAxes,
            color=col, lw=lw, zorder=10, clip_on=False)

# ════════════════════════════════════════════════════════════════
#  FIGURE LAYOUT
# ════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(15, 11), facecolor=BG)
fig.patch.set_facecolor(BG)

# ── Title ────────────────────────────────────────────────────────
fig.text(0.50, 0.972,
         "STUDY AREA — CHIKKAMAGALURU DISTRICT",
         ha="center", va="top", fontsize=22, fontweight="bold",
         color=TITLE_COL)
fig.text(0.50, 0.938,
         "Western Ghats, Karnataka, India  ·  Forest-Coffee Mosaic Landscape  ·  Bhadra Tiger Reserve",
         ha="center", va="top", fontsize=10.5, color=TEXT_MED, style="italic")

# Gold rules
for y_, h_, col_ in [(0.920, 0.004, GOLD), (0.916, 0.0015, ACCENT_GRN)]:
    ar = fig.add_axes([0.06, y_, 0.88, h_])
    ar.set_facecolor(col_); ar.axis("off")

gs = GridSpec(2, 3, figure=fig,
              left=0.055, right=0.975, top=0.908, bottom=0.08,
              wspace=0.12, hspace=0.14)

# ════════════════════════════════════════════════════════════════
#  PANEL A — India context
# ════════════════════════════════════════════════════════════════
axA = fig.add_subplot(gs[0, 0])
axA.set_facecolor(OCEAN)
axA.set_aspect("equal")

# Simplified India outline (major coastal/boundary points)
india_lon = [68.0, 70.5, 72.6, 74.0, 77.0, 80.0, 80.3, 79.8, 80.2,
             81.0, 82.5, 84.0, 85.5, 87.0, 88.0, 89.0, 92.5, 97.4,
             97.0, 95.0, 93.0, 91.5, 90.0, 89.5, 88.5, 87.0, 85.5,
             84.0, 82.0, 80.2, 78.0, 76.5, 74.0, 72.5, 70.5, 68.0, 68.0]
india_lat = [23.0, 22.8, 22.0, 20.0, 18.5, 16.5, 14.0, 13.5, 12.0,
             11.5, 11.0, 10.5, 10.0, 9.5,  9.0,  9.5, 10.5, 11.5,
             13.5, 15.0, 16.5, 17.0, 20.0, 21.0, 22.5, 23.5, 22.5,
             22.0, 22.5, 23.0, 22.0, 21.0, 20.0, 20.5, 22.0, 23.0, 23.0]
# North part
india_n_lon = [68.0,72.0,74.5,76.5,78.5,80.0,82.0,84.0,86.0,88.5,
               91.0,94.0,97.0,97.4,97.0,95.0,97.0,96.5,95.5,92.5,
               89.0,88.0,87.0,85.0,83.0,80.0,77.0,74.0,73.5,72.0,
               70.0,68.5,68.0]
india_n_lat = [23.0,24.0,25.5,27.5,29.0,30.0,31.0,32.0,33.0,34.0,
               35.5,36.0,36.5,35.5,30.0,27.5,26.5,24.5,22.5,22.0,
               22.0,22.5,24.0,23.0,22.0,21.5,20.5,20.0,20.5,21.0,
               21.0,22.0,23.0]

all_lon = india_lon[:18] + india_n_lon[1:]
all_lat = india_lat[:18] + india_n_lat[1:]
axA.fill(all_lon, all_lat, color=LAND_INDIA, zorder=2)
axA.plot(all_lon, all_lat, color="#A09080", lw=0.7, zorder=3)

# Karnataka highlight (rough polygon)
ka_lon = [74.0,76.5,78.0,78.5,78.0,77.5,77.0,76.0,74.5,73.5,73.0,74.0]
ka_lat = [15.5,15.8,16.5,15.0,13.0,12.0,11.5,11.5,12.5,13.5,14.5,15.5]
axA.fill(ka_lon, ka_lat, color="#B8D4A8", zorder=4, alpha=0.85)
axA.plot(ka_lon, ka_lat, color=ACCENT_GRN, lw=1.0, zorder=5)
axA.text(75.8, 13.8, "Karnataka", fontsize=6.5, color=ACCENT_GRN,
         fontweight="bold", ha="center", zorder=6,
         path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

# Study district star
axA.plot(75.8, 13.5, "*", ms=10, color=HEC_RED, zorder=8,
         markeredgecolor=WHITE, markeredgewidth=0.6)
axA.annotate("Chikkamagaluru\nDistrict", xy=(75.8, 13.5),
             xytext=(77.5, 12.2), fontsize=6, color=HEC_RED,
             fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=HEC_RED, lw=0.9))

# Ocean labels
axA.text(68.5, 15.0, "Arabian\nSea", fontsize=6, color="#4A7A96",
         ha="center", style="italic", alpha=0.85)
axA.text(85.0, 15.5, "Bay of\nBengal", fontsize=6, color="#4A7A96",
         ha="center", style="italic", alpha=0.85)
axA.text(77.0, 10.0, "Indian\nOcean", fontsize=6, color="#4A7A96",
         ha="center", style="italic", alpha=0.85)
axA.text(80.0, 28.0, "India", fontsize=8.5, color=TEXT_DARK,
         ha="center", style="italic", alpha=0.6, fontweight="bold")

axA.set_xlim(66, 98); axA.set_ylim(6, 38)
axA.set_title("National Context", fontsize=8.5, color=TITLE_COL,
              fontweight="bold", pad=5, loc="left")
north_arrow(axA, 0.88, 0.75)
style_ax(axA, OCEAN)

# ════════════════════════════════════════════════════════════════
#  PANEL B — Karnataka context
# ════════════════════════════════════════════════════════════════
axB = fig.add_subplot(gs[0, 1])
axB.set_facecolor(OCEAN)
axB.set_aspect("equal")

axB.fill(ka_lon, ka_lat, color=LAND_INDIA, zorder=2, alpha=0.9)
axB.plot(ka_lon, ka_lat, color=ACCENT_GRN, lw=1.2, zorder=3)
axB.text(76.0, 14.5, "Karnataka", fontsize=8, color=ACCENT_GRN,
         fontweight="bold", ha="center", alpha=0.65, style="italic")

# Chikkamagaluru district highlight (rough)
chkm_lon = [75.4, 76.4, 76.4, 75.9, 75.4, 75.0, 75.4]
chkm_lat = [13.0, 13.0, 13.6, 14.0, 14.0, 13.5, 13.0]
axB.fill(chkm_lon, chkm_lat, color="#4A9A60", zorder=4, alpha=0.88)
axB.plot(chkm_lon, chkm_lat, color=FOREST_DEEP, lw=1.8, zorder=5)
axB.text(75.9, 13.5, "Chikkamagaluru", fontsize=7, color=WHITE,
         fontweight="bold", ha="center", zorder=6,
         path_effects=[pe.withStroke(linewidth=2, foreground=FOREST_DEEP)])

# Western Ghats label
axB.text(74.5, 13.5, "Western\nGhats", fontsize=6.5, color=FOREST_DEEP,
         ha="center", style="italic", rotation=5, alpha=0.75)

# Other major districts (rough centres)
for dname, dlon, dlat in [
    ("Shimoga",    75.6, 14.2),
    ("Hassan",     76.1, 13.0),
    ("Dakshina K.",75.0, 12.8),
    ("Udupi",      74.8, 13.3),
]:
    axB.plot(dlon, dlat, "o", ms=3, color=TEXT_MED, zorder=5)
    axB.text(dlon+0.07, dlat, dname, fontsize=5, color=TEXT_MED, va="center")

# Bounding box of study area
axB.add_patch(Rectangle((75.4, 13.0), 1.0, 1.0,
              linewidth=2.0, edgecolor=HEC_RED, facecolor="none", zorder=7))

axB.set_xlim(73.5, 78.5); axB.set_ylim(11.3, 15.2)
axB.set_title("State Context", fontsize=8.5, color=TITLE_COL,
              fontweight="bold", pad=5, loc="left")
north_arrow(axB, 0.88, 0.75)
style_ax(axB, OCEAN)

# ════════════════════════════════════════════════════════════════
#  PANEL C — District overview (main map, large)
# ════════════════════════════════════════════════════════════════
axC = fig.add_subplot(gs[:, 1:])   # spans both rows, rightmost 2 cols
axC.set_aspect("equal")

# ---- Terrain hillshade ----------------------------------------
from matplotlib.colors import LightSource
ls  = LightSource(azdeg=315, altdeg=45)
rgb = ls.shade(TERRAIN, cmap=plt.cm.YlGn, vert_exag=1.5,
               blend_mode="overlay")
axC.imshow(rgb, extent=[75.4, 76.4, 13.0, 14.0], origin="lower",
           zorder=1, aspect="auto")

# ---- Land-cover overlay (semi-transparent) --------------------
lc_colors = {
    0: (0.36, 0.61, 0.73, 0.55),   # water — blue
    1: (0.10, 0.30, 0.18, 0.50),   # forest — dark green
    2: (0.55, 0.42, 0.08, 0.45),   # coffee — brown
    3: (0.78, 0.72, 0.43, 0.35),   # agri   — yellow
    4: (0.83, 0.51, 0.42, 0.60),   # settle — red-orange
}
lc_img = np.zeros((*LC.shape, 4))
for code, rgba in lc_colors.items():
    mask = LC == code
    for ch, v in enumerate(rgba):
        lc_img[mask, ch] = v
axC.imshow(lc_img, extent=[75.4, 76.4, 13.0, 14.0],
           origin="lower", zorder=2, aspect="auto")

# ---- Bhadra Tiger Reserve (approximate polygon) ---------------
bhadra_lon = [75.55, 75.65, 75.75, 75.85, 75.85, 75.75, 75.60, 75.52, 75.55]
bhadra_lat = [13.45, 13.40, 13.42, 13.48, 13.70, 13.78, 13.80, 13.65, 13.45]
axC.fill(bhadra_lon, bhadra_lat, color=BHADRA_COL, alpha=0.35, zorder=3)
axC.plot(bhadra_lon, bhadra_lat, color=BHADRA_ED, lw=1.8,
         linestyle="--", zorder=4, label="Bhadra Tiger Reserve")
axC.text(75.70, 13.62, "Bhadra\nTiger Reserve",
         ha="center", va="center", fontsize=7.5, fontweight="bold",
         color=WHITE, zorder=5,
         path_effects=[pe.withStroke(linewidth=2.5, foreground=BHADRA_ED)])

# ---- Taluks outline (approximate) ----------------------------
taluks = {
    "Mudigere":     ([75.54,75.72,75.72,75.54,75.54],[13.00,13.00,13.28,13.28,13.00], 187),
    "Sringeri":     ([75.52,75.68,75.68,75.52,75.52],[13.45,13.45,13.70,13.70,13.45], 143),
    "Kalasa":       ([75.52,75.68,75.68,75.52,75.52],[13.70,13.70,13.90,13.90,13.70], 112),
    "Chikkamagaluru":([75.70,75.90,75.90,75.70,75.70],[13.20,13.20,13.46,13.46,13.20], 89),
    "Koppa":        ([75.62,75.80,75.80,75.62,75.62],[13.44,13.44,13.62,13.62,13.44], 76),
    "Tarikere":     ([75.72,75.96,75.96,75.72,75.72],[13.62,13.62,13.88,13.88,13.62], 54),
    "Kadur":        ([75.88,76.20,76.20,75.88,75.88],[13.46,13.46,13.72,13.72,13.46], 31),
    "NR Pura":      ([75.40,75.58,75.58,75.40,75.40],[13.60,13.60,13.90,13.90,13.60], 28),
}
for tname,(tx,ty,hec) in taluks.items():
    axC.plot(tx, ty, color=DISTRICT_ED, lw=0.8,
             linestyle="-", zorder=5, alpha=0.6)
    cx, cy = np.mean(tx[:-1]), np.mean(ty[:-1])
    axC.text(cx, cy, tname, ha="center", va="center",
             fontsize=5.5, color=TEXT_DARK, fontweight="bold",
             alpha=0.85, zorder=6,
             path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

# ---- HEC Hotspots (proportional circles) ----------------------
hec_sites = [
    ("Mudigere",    75.88, 13.13, 187),
    ("Sringeri",    75.58, 13.57, 143),
    ("Kalasa",      75.62, 13.67, 112),
    ("Chikkamagaluru",75.78,13.32, 89),
    ("Koppa",       75.72, 13.53, 76),
    ("Tarikere",    75.82, 13.71, 54),
    ("Kadur",       76.01, 13.56, 31),
    ("NR Pura",     75.52, 13.62, 28),
]
max_hec = max(h for *_, h in hec_sites)
for name, lon, lat, count in hec_sites:
    r = 0.012 + 0.052 * (count / max_hec)
    circle = plt.Circle((lon, lat), r,
                         color=HEC_ORANGE, alpha=0.50, zorder=7)
    axC.add_patch(circle)
    circle2 = plt.Circle((lon, lat), r,
                          color=HEC_RED, fill=False,
                          linewidth=0.9, zorder=8)
    axC.add_patch(circle2)
    axC.text(lon, lat + r + 0.012, f"{count}", ha="center",
             fontsize=5.5, color=HEC_RED, fontweight="bold", zorder=9,
             path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

# ---- Rivers (synthetic) ---------------------------------------
# Bhadra river runs N→S through the reserve
riv_lon = [75.72, 75.70, 75.68, 75.66, 75.64, 75.62, 75.60]
riv_lat = [13.80, 13.72, 13.65, 13.55, 13.46, 13.35, 13.20]
axC.plot(riv_lon, riv_lat, color="#3A7AB8", lw=2.2, zorder=6,
         alpha=0.80, solid_capstyle="round", label="Bhadra River")
axC.text(75.61, 13.50, "Bhadra R.", fontsize=6, color="#3A7AB8",
         rotation=80, style="italic", alpha=0.9)

# Bhadra Reservoir
res_lon = [75.65, 75.72, 75.78, 75.78, 75.72, 75.65, 75.60, 75.62, 75.65]
res_lat = [13.47, 13.44, 13.47, 13.54, 13.58, 13.58, 13.55, 13.50, 13.47]
axC.fill(res_lon, res_lat, color="#4A8FB8", alpha=0.70, zorder=5)
axC.plot(res_lon, res_lat, color="#2A5A7A", lw=1.0, zorder=6)
axC.text(75.71, 13.51, "Bhadra\nReservoir", ha="center", fontsize=6,
         color=WHITE, fontweight="bold", zorder=7,
         path_effects=[pe.withStroke(linewidth=2, foreground="#2A5A7A")])

# ---- District boundary box ------------------------------------
axC.add_patch(Rectangle((75.4, 13.0), 1.0, 1.0,
              linewidth=2.5, edgecolor=DISTRICT_ED,
              facecolor="none", zorder=9, linestyle="-"))

# ---- Graticule labels -----------------------------------------
axC.set_xlim(75.35, 76.45); axC.set_ylim(12.94, 14.06)
axC.xaxis.set_major_locator(mticker.MultipleLocator(0.2))
axC.yaxis.set_major_locator(mticker.MultipleLocator(0.2))
axC.set_xlabel("Longitude (°E)", fontsize=7.5, color=TEXT_MED)
axC.set_ylabel("Latitude (°N)", fontsize=7.5, color=TEXT_MED)
axC.grid(True, linewidth=0.3, color=TEXT_MED, alpha=0.25, linestyle="--")
axC.set_title("Chikkamagaluru District — Detailed Study Area",
              fontsize=10, color=TITLE_COL, fontweight="bold", pad=6, loc="left")

# ---- Inset map indicator on axB --------------------------------
draw_inset_box(axB, 0.08, 0.06, 0.65, 0.78)

# ---- North Arrow (main panel) ---------------------------------
north_arrow(axC, 0.955, 0.90, size=0.045, color=TEXT_DARK)

# ---- Scale bar (main panel)  ----------------------------------
# 0.2 degrees ≈ ~22 km at 13°N
axC.plot([75.42, 75.62], [13.02, 13.02], color=TEXT_DARK, lw=3.5,
         solid_capstyle="butt", zorder=10)
axC.plot([75.42, 75.52], [13.02, 13.02], color=WHITE, lw=2.8,
         solid_capstyle="butt", zorder=11)
axC.text(75.52, 12.99, "0        10       20 km",
         ha="center", fontsize=6.5, color=TEXT_DARK, fontweight="bold", zorder=12)

style_ax(axC, PANEL_BG)

# ════════════════════════════════════════════════════════════════
#  LEGEND (main panel — bottom-right inset)
# ════════════════════════════════════════════════════════════════
leg_ax = fig.add_axes([0.620, 0.090, 0.175, 0.230])
leg_ax.set_facecolor("#FAFCF8")
leg_ax.set_xlim(0,1); leg_ax.set_ylim(0,1)
leg_ax.axis("off")
for sp in [leg_ax.spines[s] for s in leg_ax.spines]:
    sp.set_visible(True); sp.set_edgecolor(DISTRICT_ED); sp.set_linewidth(1)

leg_ax.text(0.5, 0.95, "LEGEND", ha="center", fontsize=7.5,
            fontweight="bold", color=TITLE_COL, va="top")
leg_ax.plot([0.1,0.9],[0.88,0.88], color=GOLD, lw=1)

items = [
    ("#1A4A2E",  "Dense Forest / BTR"),
    ("#8B6914",  "Coffee Agroforestry"),
    ("#C8B870",  "Agriculture / Grassland"),
    ("#5B9CB8",  "Water Bodies"),
    ("#D4826A",  "Settlements"),
    (HEC_ORANGE, "HEC Incident Hotspot"),
    (BHADRA_ED,  "Bhadra Tiger Reserve"),
    (DISTRICT_ED,"Taluk / District Boundary"),
]
for i,(col,lbl) in enumerate(items):
    y = 0.80 - i * 0.10
    ls_ = "--" if "Tiger" in lbl else "-"
    if "Hotspot" in lbl:
        circ = plt.Circle((0.08, y+0.01), 0.04,
                          color=col, alpha=0.6,
                          transform=leg_ax.transAxes)
        leg_ax.add_patch(circ)
    else:
        leg_ax.plot([0.04,0.14],[y+0.015,y+0.015],
                    color=col, lw=4.5 if ls_=="-" else 2.0,
                    linestyle=ls_, transform=leg_ax.transAxes,
                    solid_capstyle="butt")
    leg_ax.text(0.18, y+0.01, lbl, fontsize=6.2, color=TEXT_DARK,
                va="center", transform=leg_ax.transAxes)

# HEC proportional circle legend
leg_ax.text(0.5, 0.01, "Circle size ∝ HEC incidents",
            ha="center", fontsize=5.8, color=TEXT_MED,
            style="italic", transform=leg_ax.transAxes)

# ════════════════════════════════════════════════════════════════
#  BOTTOM META-BAR
# ════════════════════════════════════════════════════════════════
bot = fig.add_axes([0.055, 0.020, 0.920, 0.048])
bot.set_facecolor("#1A3A24"); bot.set_xlim(0,1); bot.set_ylim(0,1); bot.axis("off")
for sp in bot.spines.values():
    sp.set_visible(True); sp.set_edgecolor(GOLD); sp.set_linewidth(1.2)

meta_items = [
    ("Projection:", "WGS 84 / UTM Zone 43N  (EPSG:32643)"),
    ("Data sources:", "Sentinel-2 SR  ·  SRTM 30m DEM  ·  Hansen GFC  ·  OSM"),
    ("Study period:", "October 2001 – February 2024"),
    ("District area:", "≈ 7,201 km²"),
]
for i,(key,val) in enumerate(meta_items):
    x = 0.015 + i*0.255
    bot.text(x,   0.62, key, fontsize=6.5, color=GOLD, fontweight="bold")
    bot.text(x,   0.22, val, fontsize=6.2, color=WHITE, alpha=0.85)

# ── Separator rules ──────────────────────────────────────────────
for y_, h_, col_ in [(0.912, 0.0015, GOLD)]:
    ar = fig.add_axes([0.06, y_, 0.88, h_])
    ar.set_facecolor(col_); ar.axis("off")

plt.savefig("study_area_map.png", dpi=200,
            bbox_inches="tight", facecolor=BG)
print("✓  Saved:  study_area_map.png")
plt.show()
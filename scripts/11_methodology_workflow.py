"""
Methodology Workflow — Downward-Flowing Diagram
================================================
Forest Fragmentation & HEC Corridor Analysis
Chikkamagaluru, Western Ghats, India

Produces:  methodology_workflow.png  (200 dpi, 25 cm tall × 15 cm wide)

Dependencies:
    pip install matplotlib numpy
"""

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ════════════════════════════════════════════════════════════════
#  COLOUR PALETTE
# ════════════════════════════════════════════════════════════════
BG       = "#EEF4EC"
CARD_BG  = "#FFFFFF"

STEP_COLORS = {
    1: "#1A6B4A",
    2: "#2E8B5A",
    3: "#3A9A50",
    4: "#5A8A30",
    5: "#7A8A20",
    6: "#C87830",
    7: "#C84830",
}

BADGE_BG    = "#1A3A28"
ARROW_HEAD  = "#2A5A3A"
OUTPUT_BG   = "#F0F8F0"
OUTPUT_ED   = "#80B880"
OUTPUT_TEXT = "#2A5A3A"
GOLD        = "#C8973A"
WHITE       = "#FFFFFF"
TITLE_COL   = "#1A3A1A"
CARD_TEXT   = "#3A4A3A"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif":  ["Georgia", "Times New Roman", "DejaVu Serif"],
})

# ════════════════════════════════════════════════════════════════
#  STEP DATA
# ════════════════════════════════════════════════════════════════
steps = [
    {
        "num": 1,
        "title": "Satellite Data Acquisition",
        "subtitle": "Sentinel-2 SR via GEE",
        "tag": "Nov–Feb  ·  10 m res",
        "output": "Pre-processed 10 m multi-band image stack",
    },
    {
        "num": 2,
        "title": "Land Cover Classification",
        "subtitle": "Random Forest · 5-class LULC",
        "tag": "10 m res  ·  5 classes",
        "output": "LULC maps 2001 / 2013 / 2023  (EPSG:32643)",
    },
    {
        "num": 3,
        "title": "Forest Fragmentation Analysis",
        "subtitle": "Patch metrics & shape index",
        "tag": "8,215 patches",
        "output": "Fragmentation index maps + patch statistics",
    },
    {
        "num": 4,
        "title": "Multi-Factor Resistance Surface",
        "subtitle": "LC + Slope + Roads + Settlements",
        "tag": "100 m res  ·  weighted sum",
        "output": "Resistance surface (100 m, unitless 1–10)",
    },
    {
        "num": 5,
        "title": "Corridor Suitability & Bottlenecks",
        "subtitle": "Least-cost path · Circuitscape",
        "tag": "28,446 ha BN",
        "output": "Corridor network + bottleneck polygons",
    },
    {
        "num": 6,
        "title": "Temporal Forest Loss",
        "subtitle": "Hansen GFC 2001 – 2023",
        "tag": "12,836 ha lost",
        "output": "Annual forest loss rasters + trend statistics",
    },
    {
        "num": 7,
        "title": "HEC Hotspot Analysis",
        "subtitle": "KFD incident records · KDE + Gi*",
        "tag": "720 incidents",
        "output": "HEC density surface + risk zone polygons",
    },
]

# ════════════════════════════════════════════════════════════════
#  FIGURE SIZE  — 15 cm wide × 25 cm tall
#  KEY FIX: the internal axes coordinate system is set to match
#  the figure size in inches (fig_w × fig_h), so 1 unit = 1 inch.
#  The old code used xlim(0,11) regardless of actual figure width,
#  which caused everything to overflow or be clipped.
# ════════════════════════════════════════════════════════════════
FIG_W_CM = 15
FIG_H_CM = 25
fig_w = FIG_W_CM / 2.54   # 5.906 inches
fig_h = FIG_H_CM / 2.54   # 9.843 inches

fig = plt.figure(figsize=(fig_w, fig_h), facecolor=BG)

ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor(BG)
ax.set_xlim(0, fig_w)    # coord units now equal inches
ax.set_ylim(0, fig_h)
ax.axis("off")

# ════════════════════════════════════════════════════════════════
#  LAYOUT CONSTANTS  (all values in inches)
# ════════════════════════════════════════════════════════════════
MARGIN_L = 0.28
MARGIN_R = 0.28
CARD_W   = fig_w - MARGIN_L - MARGIN_R   # ~5.35 inches

TITLE_H  = 1.05    # vertical space for title block
FOOTER_H = 0.52    # vertical space for final banner
N_STEPS  = len(steps)
ARROW_H  = 0.16    # height consumed by each inter-card arrow

# Cards fill all remaining vertical space equally
available = fig_h - TITLE_H - FOOTER_H - 0.12
CARD_H    = (available - (N_STEPS - 1) * ARROW_H) / N_STEPS

STRIPE_H  = CARD_H * 0.37   # header stripe = 37% of card height

# Font sizes derived from card height so they always fit
FS_TITLE    = max(6.0, CARD_H * 4.0)
FS_SUBTITLE = max(5.2, CARD_H * 3.2)
FS_TAG      = max(4.2, CARD_H * 2.6)
FS_OUTPUT   = max(4.8, CARD_H * 2.9)
FS_BADGE    = max(6.5, CARD_H * 4.3)

# ════════════════════════════════════════════════════════════════
#  TITLE BLOCK
# ════════════════════════════════════════════════════════════════
ty = fig_h - 0.10

ax.text(fig_w / 2, ty,
        "METHODOLOGY",
        ha="center", va="top",
        fontsize=max(9.0, fig_w * 1.5), fontweight="bold",
        color=TITLE_COL,
        path_effects=[pe.withStroke(linewidth=3, foreground=BG)])

ax.text(fig_w / 2, ty - 0.28,
        "Wildlife Corridor Fragmentation in Chikkamagaluru",
        ha="center", va="top",
        fontsize=max(6.0, fig_w * 0.95),
        color="#3A6A3A", style="italic")

ax.text(fig_w / 2, ty - 0.50,
        "Chikkamagaluru District  ·  Western Ghats, Karnataka, India",
        ha="center", va="top",
        fontsize=max(5.2, fig_w * 0.82),
        color="#5A8A5A")

# Gold rule lines below title
rule_y = ty - 0.68
ax.plot([MARGIN_L, fig_w - MARGIN_R], [rule_y,        rule_y],
        color=GOLD,     lw=1.5)
ax.plot([MARGIN_L, fig_w - MARGIN_R], [rule_y - 0.04, rule_y - 0.04],
        color=BADGE_BG, lw=0.5, alpha=0.4)

# ════════════════════════════════════════════════════════════════
#  STEP CARDS  (drawn top → bottom)
# ════════════════════════════════════════════════════════════════
first_card_y0 = fig_h - TITLE_H - CARD_H   # bottom-edge of first card

for i, step in enumerate(steps):
    y0  = first_card_y0 - i * (CARD_H + ARROW_H)
    col = STEP_COLORS[step["num"]]
    cx  = MARGIN_L

    # Shadow
    ax.add_patch(FancyBboxPatch(
        (cx + 0.035, y0 - 0.035), CARD_W, CARD_H,
        boxstyle="round,pad=0.06",
        facecolor="#B8C8B8", edgecolor="none",
        alpha=0.45, zorder=1))

    # Card body
    ax.add_patch(FancyBboxPatch(
        (cx, y0), CARD_W, CARD_H,
        boxstyle="round,pad=0.06",
        facecolor=CARD_BG, edgecolor="#C0D4C0",
        linewidth=0.8, zorder=2))

    # Coloured header stripe
    ax.add_patch(FancyBboxPatch(
        (cx, y0 + CARD_H - STRIPE_H), CARD_W, STRIPE_H,
        boxstyle="round,pad=0.05",
        facecolor=col, edgecolor=col,
        linewidth=0, zorder=3))

    # Number badge (circle)
    badge_x = cx + STRIPE_H * 0.52
    badge_y = y0 + CARD_H - STRIPE_H / 2
    badge_r = STRIPE_H * 0.34
    ax.add_patch(plt.Circle(
        (badge_x, badge_y), badge_r,
        color=BADGE_BG, zorder=4))
    ax.text(badge_x, badge_y, str(step["num"]),
            ha="center", va="center",
            fontsize=FS_BADGE, fontweight="bold",
            color=WHITE, zorder=5)

    # Step title (in header stripe)
    title_x = badge_x + badge_r + 0.09
    ax.text(title_x, badge_y,
            step["title"],
            ha="left", va="center",
            fontsize=FS_TITLE, fontweight="bold",
            color=WHITE, zorder=5)

    # Tag pill — right side of header
    tag   = step["tag"]
    tag_w = len(tag) * FS_TAG * 0.0098 + 0.12
    tag_x0 = cx + CARD_W - tag_w - 0.07
    tag_y0 = badge_y - STRIPE_H * 0.21
    ax.add_patch(FancyBboxPatch(
        (tag_x0, tag_y0), tag_w, STRIPE_H * 0.42,
        boxstyle="round,pad=0.025",
        facecolor=BADGE_BG, edgecolor="none",
        alpha=0.75, zorder=4))
    ax.text(tag_x0 + tag_w / 2, badge_y,
            tag,
            ha="center", va="center",
            fontsize=FS_TAG, fontweight="bold",
            color=WHITE, zorder=5)

    # Subtitle (below stripe, inside card body)
    sub_y = y0 + CARD_H - STRIPE_H - 0.07
    ax.text(title_x, sub_y,
            step["subtitle"],
            ha="left", va="top",
            fontsize=FS_SUBTITLE,
            color=col, style="italic", zorder=4)

    # Output ribbon (bottom of card)
    rib_h = CARD_H * 0.30
    rib_y = y0 + 0.04
    ax.add_patch(FancyBboxPatch(
        (cx + 0.08, rib_y), CARD_W - 0.16, rib_h,
        boxstyle="round,pad=0.03",
        facecolor=OUTPUT_BG, edgecolor=OUTPUT_ED,
        linewidth=0.7, zorder=3))
    ax.text(cx + CARD_W / 2, rib_y + rib_h / 2,
            "▶  " + step["output"],
            ha="center", va="center",
            fontsize=FS_OUTPUT, fontweight="bold",
            color=OUTPUT_TEXT, style="italic", zorder=4)

    # Downward arrow to next card
    if i < N_STEPS - 1:
        mid_x   = cx + CARD_W / 2
        arr_top = y0 - 0.01
        arr_bot = y0 - ARROW_H + 0.01
        ax.annotate("",
            xy=(mid_x, arr_bot), xytext=(mid_x, arr_top),
            arrowprops=dict(
                arrowstyle="-|>",
                color=ARROW_HEAD,
                lw=1.4,
                mutation_scale=11,
            ), zorder=6)

# ════════════════════════════════════════════════════════════════
#  FINAL DELIVERABLES BANNER
# ════════════════════════════════════════════════════════════════
last_y0  = first_card_y0 - (N_STEPS - 1) * (CARD_H + ARROW_H)
banner_h = 0.30
banner_y = last_y0 - ARROW_H - 0.04

# Arrow from last card to banner
ax.annotate("",
    xy=(MARGIN_L + CARD_W / 2, banner_y + banner_h),
    xytext=(MARGIN_L + CARD_W / 2, last_y0 - 0.01),
    arrowprops=dict(arrowstyle="-|>", color=GOLD,
                    lw=1.4, mutation_scale=11), zorder=6)

ax.add_patch(FancyBboxPatch(
    (MARGIN_L - 0.04, banner_y), CARD_W + 0.08, banner_h,
    boxstyle="round,pad=0.05",
    facecolor=BADGE_BG, edgecolor=GOLD,
    linewidth=1.1, zorder=5))

ax.text(MARGIN_L + CARD_W / 2, banner_y + banner_h / 2,
        "FINAL DELIVERABLES:  Fragmentation Atlas  |  Corridor & Bottleneck Maps"
        "  |  Temporal Loss DB  |  HEC Risk Zones",
        ha="center", va="center",
        fontsize=max(4.5, fig_w * 0.80),
        color=GOLD, fontweight="bold", zorder=6)

# ════════════════════════════════════════════════════════════════
#  LEFT PROGRESS SPINE
# ════════════════════════════════════════════════════════════════
spine_x = MARGIN_L - 0.14
for i, step in enumerate(steps):
    y_top = first_card_y0 + CARD_H - i * (CARD_H + ARROW_H)
    y_bot = first_card_y0         - i * (CARD_H + ARROW_H)
    col   = STEP_COLORS[step["num"]]
    ax.plot([spine_x, spine_x], [y_bot, y_top],
            color=col, lw=3.5, solid_capstyle="butt",
            zorder=2, alpha=0.55)
    ax.plot([spine_x - 0.04, spine_x + 0.04],
            [(y_top + y_bot) / 2] * 2,
            color=col, lw=1.0, zorder=3)

# ════════════════════════════════════════════════════════════════
#  SAVE
# ════════════════════════════════════════════════════════════════
plt.savefig("methodology_workflow.png", dpi=200,
            bbox_inches="tight", facecolor=BG)
print("✓  Saved:  methodology_workflow.png")
plt.show()
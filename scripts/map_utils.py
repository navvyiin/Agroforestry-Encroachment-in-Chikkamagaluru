"""
map_utils.py — Shared utilities for North Arrow and Scale Bar
All poster maps for Naval Kishore | Bangalore University 2026

v3 FIXES:
- Scale bar y position is configurable (y_bar) to avoid overlapping text boxes
- add_north_arrow stays at top-right axes fraction (works for imshow + vector maps)
- Script 03 must set xlim/ylim from gdf bounds to anchor the arrow correctly
- MAP5a uses bar_km=5 (27km total width at 30m/900px)
- MAP5b panel A raises y_bar to clear the forest-area text box
"""

import matplotlib.pyplot as plt
import numpy as np


def add_north_arrow(ax, color='black'):
    """
    North arrow at TOP-RIGHT corner of the axes (axes-fraction coords).
    Works for both imshow rasters and gdf.plot() vector maps provided
    xlim/ylim are set to the data extent before calling.
    """
    x      = 0.93
    y_base = 0.82
    y_tip  = 0.91

    ax.annotate(
        '',
        xy=(x, y_tip),
        xytext=(x, y_base),
        xycoords='axes fraction',
        textcoords='axes fraction',
        arrowprops=dict(
            arrowstyle='-|>',
            color=color,
            lw=2.0,
            mutation_scale=16
        ),
        zorder=25
    )
    ax.text(
        x, y_tip + 0.03,
        'N',
        transform=ax.transAxes,
        ha='center', va='bottom',
        fontsize=11, fontweight='bold', color=color,
        zorder=25
    )


def add_scale_bar(ax, pixel_size_m, image_width_px,
                  x=0.04, y_bar=0.05, bar_km=10,
                  color='black', lw=3):
    """
    Accurately calibrated scale bar.

    Parameters
    ----------
    ax              : matplotlib Axes
    pixel_size_m    : ground resolution in metres per pixel
    image_width_px  : width of raster array in pixels  (arr.shape[1])
    x               : axes-fraction x position of left end of bar
    y_bar           : axes-fraction y position of the bar line
                      (raise above 0.05 if a text box occupies the bottom)
    bar_km          : scale bar length in kilometres
    color           : colour
    lw              : line width
    """
    bar_m      = bar_km * 1000.0
    bar_pixels = bar_m / pixel_size_m
    bar_frac   = bar_pixels / float(image_width_px)

    # Safety clamp — never occupy less than 3% or more than 40% of axes width
    bar_frac = max(0.03, min(0.40, bar_frac))

    tick_h = 0.013

    # Horizontal bar line
    ax.plot(
        [x, x + bar_frac], [y_bar, y_bar],
        transform=ax.transAxes,
        color=color, linewidth=lw,
        solid_capstyle='butt', zorder=20
    )
    # Vertical end ticks
    for xp in [x, x + bar_frac]:
        ax.plot(
            [xp, xp], [y_bar - tick_h, y_bar + tick_h],
            transform=ax.transAxes,
            color=color, linewidth=max(lw * 0.6, 1.0), zorder=20
        )
    # Label — sits above the bar with a small gap
    ax.text(
        x + bar_frac / 2.0,
        y_bar + tick_h + 0.020,      # raised slightly to avoid touching the bar
        f'{bar_km} km',
        transform=ax.transAxes,
        ha='center', va='bottom',
        fontsize=9, fontweight='bold', color=color,
        zorder=20
    )


def add_map_furniture(ax, pixel_size_m, image_width_px,
                      bar_km=10, y_bar=0.05, color='black'):
    """
    Add north arrow (top-right) + scale bar (bottom-left).
    Call AFTER imshow / gdf.plot() AND after setting xlim/ylim.

    Parameters
    ----------
    ax              : matplotlib Axes
    pixel_size_m    : metres per pixel of the source raster
    image_width_px  : raster array width in pixels (arr.shape[1])
    bar_km          : scale bar length in km
    y_bar           : axes-fraction y for scale bar line
                      (default 0.05; raise to ~0.12 if bottom text overlaps)
    color           : colour for both elements
    """
    add_north_arrow(ax, color=color)
    add_scale_bar(ax, pixel_size_m, image_width_px,
                  y_bar=y_bar, bar_km=bar_km, color=color)
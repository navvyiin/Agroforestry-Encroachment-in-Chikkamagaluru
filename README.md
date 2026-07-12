# Agroforestry Encroachment & Human-Elephant Conflict — Chikkamagaluru

A spatial ML pipeline mapping agroforestry expansion into wildlife corridors in Chikkamagaluru's coffee-forest mosaic, and its relationship to human-elephant conflict (HEC).

Poster presented at Bangalore University Science Festival 2026 (BUSF, PM-USHA). Developed in the context of the Karnataka Forest Department's International Conference on Human-Elephant Conflict Management.

## Background

I've worked as a farm hand on a coffee plantation in this landscape since 2018. The study area — the coffee-forest boundary in Chikkamagaluru, part of the Bhadra-Kudremukh-Pushpagiri elephant corridor system — is the same land I've physically worked. That's not incidental context; it's why I picked this question over a more conventional benchmark dataset.

## What it does

1. **Land cover classification** — Sentinel-2 multispectral imagery (10m) classified into forest, agroforestry, agriculture, and built-up classes using a Random Forest classifier, with NDVI, NDWI, and EVI as engineered features.
2. **Forest change detection** — Hansen Global Forest Watch tree cover loss layers (2010–2023) processed to confirm 12,836 ha of forest loss in the district since 2001, with visibly accelerated loss along the coffee-forest boundary after 2016.
3. **Corridor resistance modelling** — A resistance surface built from land cover class, SRTM slope, and proximity to roads/settlements. Least-cost path analysis on this surface identifies 28,446 ha of critical corridor bottleneck zones across 8,215 mapped forest patches.
4. **Conflict hotspot detection** — Kernel density estimation applied to georeferenced HEC incident records from the Karnataka Forest Department, producing a smoothed conflict intensity surface.
5. **Integrated overlay** — Corridor resistance and conflict intensity are overlaid to find where encroachment pressure, corridor degradation, and conflict frequency actually coincide spatially, rather than assuming they do.

That overlay is the main finding: **14.3% of recorded HEC incidents cluster within 1.5 km of an identified bottleneck zone**, and HEC incidence rose 46% between 2018 and 2023.

## On the resistance model

Movement resistance can't be learned from labelled data the way land cover can — there's no ground-truth "resistance value" to regress against. The values used here (how costly a given land ccover type, slope, or distance-to-road is to elephant movement) come from published landscape ecology literature on elephant corridor studies, not from GPS telemetry on this specific population. That's a real limitation, not a footnote: it means the corridor map shows *plausible* movement resistance given known elephant behaviour patterns generally, not *confirmed* movement paths for these specific herds. Actual telemetry data would be the natural next step to validate it.

## Tech stack

Python, Google Earth Engine, GeoPandas, Rasterio, Scikit-learn, Shapely, QGIS.

## Known limitations

- HEC incident records depend on what gets reported to the Forest Department, which undercounts conflict in remote areas with less administrative presence.
- Cloud contamination in optical Sentinel-2 imagery limits usable cloud-free scenes during monsoon months, when a meaningful share of agroforestry expansion likely happens.
- The corridor model is static — it doesn't simulate actual elephant movement or account for seasonal migration patterns.

## Setup

```bash
git clone https://github.com/navvyiin/agroforestry-encroachment-hec-chikkamagaluru.git
cd agroforestry-encroachment-hec-chikkamagaluru
pip install -r requirements.txt
earthengine authenticate
python src/preprocess.py && python src/classify.py && python src/corridor.py
```

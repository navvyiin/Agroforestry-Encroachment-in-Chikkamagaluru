# Agroforestry Encroachment and Human-Elephant Conflict in Chikkamagaluru

A spatial analysis of agroforestry expansion into wildlife corridors in Chikkamagaluru District, Karnataka, and its relationship with human-elephant conflict (HEC). The study area sits within the Western Ghats coffee-forest mosaic, a landscape where agricultural land use and forest cover exist in close and increasingly contested proximity.

This project combines satellite-based land cover classification, forest change analysis, resistance-based corridor modelling, and hotspot detection to map where landscape fragmentation is most likely driving conflict between farming communities and Asian elephants.

---

## Research Context

Chikkamagaluru's forests form part of the Bhadra-Kudremukh-Pushpagiri corridor system, one of the critical connectivity zones for elephant populations in the Western Ghats. As coffee and other agroforestry crops expand into buffer zones and corridor edges, elephant movement paths become compressed and conflict incidents increase.

This work was developed in the context of the **International Conference on Human-Elephant Conflict Management** (Karnataka Forest Department) and draws on publicly available remote sensing datasets to produce spatially explicit conflict-risk maps that can inform conservation planning and land use policy.

---

## What the Analysis Does

- Classifies multi-year land cover from Sentinel-2 imagery to detect agroforestry expansion at the forest edge
- Quantifies forest cover loss using Hansen Global Forest Watch data to identify where tree cover has declined and in what years
- Models wildlife corridor resistance based on land cover, slope, and human infrastructure, to map functional connectivity for elephant movement
- Applies Kernel Density Estimation to reported HEC incidents to produce conflict intensity surfaces
- Overlays corridor resistance and conflict hotspots to identify spatial coincidence between encroachment, corridor degradation, and conflict pressure

---

## Data Sources

| Dataset | Source | Resolution |
|---------|--------|------------|
| Sentinel-2 multispectral imagery | ESA Copernicus / Google Earth Engine | 10m |
| Hansen Global Forest Change | University of Maryland / GFW | 30m |
| SRTM Digital Elevation Model | NASA / USGS | 30m |
| HEC incident records | Karnataka Forest Department | Point data |
| Administrative boundaries | Survey of India / OGRDS | Vector |
| Road network | OpenStreetMap | Vector |

---

## Methods

**Land Cover Classification**
Sentinel-2 bands (B2, B3, B4, B8, B11, B12) and derived indices (NDVI, NDWI, EVI) are used to classify land cover into forest, agroforestry, agriculture, built-up, and water classes using a Random Forest classifier trained on reference samples from the study area.

**Forest Change Detection**
Hansen GFW tree cover loss layers (year of loss, loss extent) are clipped to the study area to produce a temporal map of deforestation, with particular attention to loss occurring at the forest-agroforestry boundary between 2010 and 2023.

**Corridor Resistance Modelling**
A resistance surface is constructed by assigning cost values to each land cover class, slope category, and proximity to roads and settlements. Least-cost path analysis identifies the functional movement corridors that remain accessible to elephants given the current landscape configuration.

**Conflict Hotspot Detection**
Kernel Density Estimation is applied to georeferenced HEC incident records to generate a smoothed conflict intensity surface. KDE bandwidth is selected using cross-validation to balance spatial resolution and statistical stability.

**Integrated Analysis**
Corridor resistance values and KDE conflict intensity are overlaid to identify spatial clusters where high encroachment pressure coincides with degraded corridor connectivity and elevated conflict frequency.

---

## Project Structure

```
Agroforestry-Encroachment-in-Chikkamagaluru/
├── data/
│   ├── raw/                      # Input datasets (shapefiles, CSVs, imagery)
│   └── processed/                # Classified rasters, corridor grids, KDE outputs
├── gee/
│   └── sentinel2_classification.js   # GEE script for land cover classification
├── src/
│   ├── preprocess.py             # Data loading and CRS harmonisation
│   ├── classify.py               # Random Forest land cover classification
│   ├── forest_change.py          # Hansen data processing and loss mapping
│   ├── corridor.py               # Resistance surface and least-cost path analysis
│   ├── hotspots.py               # KDE conflict intensity surface
│   ├── overlay.py                # Integrated encroachment-conflict analysis
│   └── visualise.py             # Map outputs and figure generation
├── outputs/
│   ├── maps/                     # Final map figures
│   └── tables/                   # Summary statistics
├── notebooks/
│   └── exploration.ipynb         # Exploratory analysis and diagnostics
├── requirements.txt
└── README.md
```

---

## Getting Started

**Requirements:** Python 3.8 or above, GDAL, Google Earth Engine account (for Sentinel-2 data access)

```bash
git clone https://github.com/navvyiin/Agroforestry-Encroachment-in-Chikkamagaluru.git
cd Agroforestry-Encroachment-in-Chikkamagaluru
pip install -r requirements.txt
```

Authenticate your GEE account before running the classification script:

```bash
earthengine authenticate
```

---

## Running the Analysis

Run the full pipeline in sequence:

```bash
python src/preprocess.py
python src/classify.py
python src/forest_change.py
python src/corridor.py
python src/hotspots.py
python src/overlay.py
python src/visualise.py
```

Or run the GEE classification script (`gee/sentinel2_classification.js`) directly in the Google Earth Engine Code Editor and export results to the `data/processed/` directory before running the Python pipeline.

---

## Tech Stack

`Python` `Google Earth Engine` `GeoPandas` `Rasterio` `Scikit-learn` `SciPy` `QGIS` `Shapely` `Matplotlib`

---

## Key Findings

- Agroforestry expansion is concentrated along the western and southern edges of the Bhadra Wildlife Sanctuary buffer zone
- Hansen data indicates accelerated tree cover loss at forest-coffee boundaries between 2018 and 2022
- Corridor resistance is highest in sectors where road infrastructure and estate expansion have converged
- KDE conflict hotspots show strong spatial overlap with zones of lowest remaining corridor connectivity
- Several village clusters fall within areas of both high encroachment pressure and degraded corridor function, indicating elevated long-term conflict risk

---

## Limitations

- HEC incident data completeness depends on Karnataka Forest Department reporting coverage, which may underrepresent incidents in remote areas
- Sentinel-2 classification accuracy is affected by cloud cover in the monsoon season
- Corridor modelling uses a simplified resistance schema and does not account for elephant social behaviour or seasonal movement patterns

---

## Relevance

This work sits at the intersection of conservation planning, remote sensing, and spatial ML. The methods are transferable to other forest-agriculture boundary contexts across South and Southeast Asia where land use pressure on wildlife corridors is increasing.

---

## Citation

If you use this work or adapt the methods, please cite this repository and acknowledge the Karnataka Forest Department for the HEC incident data.

---

## License

MIT License. © 2026 navvyiin

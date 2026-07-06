# EcoCorridorAI
### A Computational Framework for Mapping Agroforestry Encroachment, Landscape Connectivity, and Human–Elephant Conflict Using Earth Observation and Spatial Intelligence

> A reproducible geospatial analytics framework that integrates satellite remote sensing, landscape ecology, spatial statistics, and computational modelling to investigate how land-use change alters wildlife connectivity and intensifies human–elephant conflict within the Western Ghats biodiversity hotspot.

EcoCorridorAI is an open-source computational framework designed to analyse the relationship between landscape fragmentation and human–wildlife conflict using multi-source Earth observation data.

The platform combines land-cover classification, forest change detection, ecological resistance modelling, least-cost corridor analysis, hotspot detection, and spatial overlay analysis into a single reproducible workflow capable of supporting conservation planning, ecological research, and evidence-based land management.

Although demonstrated within the coffee–forest mosaic of Chikkamagaluru District, Karnataka, the analytical framework is transferable to wildlife corridors throughout South and Southeast Asia.

---

# Motivation

Human–elephant conflict has emerged as one of the most significant conservation and socio-economic challenges across the Western Ghats.

Agricultural expansion, infrastructure development, and landscape fragmentation increasingly compress elephant movement corridors, forcing wildlife into closer contact with farming communities.

Traditional ecological studies often investigate land-cover change, wildlife connectivity, or conflict incidents independently.

EcoCorridorAI was developed to integrate these components into a unified computational framework capable of answering a central research question:

> **How does agroforestry expansion reshape landscape connectivity, and where does this fragmentation translate into elevated human–elephant conflict risk?**

Rather than treating conflict as isolated incidents, the framework models conflict as an emergent property of landscape structure.

---

# Research Objectives

The framework is designed to

- quantify agroforestry expansion along forest boundaries
- detect long-term forest cover change
- model functional wildlife connectivity
- estimate ecological movement resistance
- identify statistically significant conflict hotspots
- integrate multiple spatial datasets into conservation-ready decision products

---

# Key Features

## Earth Observation

- Multi-temporal Sentinel-2 imagery
- Spectral index generation (NDVI, NDWI, EVI)
- Supervised land-cover classification
- Automated preprocessing using Google Earth Engine

---

## Forest Change Analysis

- Hansen Global Forest Change
- Temporal tree-cover loss mapping
- Forest edge dynamics
- Multi-year landscape monitoring

---

## Landscape Connectivity

- Ecological resistance surface modelling
- Cost-distance analysis
- Least-cost corridor generation
- Connectivity assessment under fragmented landscapes

---

## Spatial Statistics

- Kernel Density Estimation
- Spatial overlay analysis
- Corridor degradation mapping
- Conflict intensity modelling

---

## Conservation Intelligence

The framework integrates ecological connectivity and conflict intensity to identify

- priority restoration corridors
- vulnerable agricultural frontiers
- landscape bottlenecks
- high-risk conservation zones

---

# Study Area

The study focuses on the coffee–forest mosaic of **Chikkamagaluru District, Karnataka**, located within the central Western Ghats.

This landscape forms part of the broader

- Bhadra
- Kudremukh
- Pushpagiri

elephant corridor system, one of India's most ecologically significant connectivity networks.

Rapid expansion of coffee plantations and associated infrastructure has transformed portions of the landscape into fragmented ecological mosaics where human and elephant movement increasingly intersect.

---

# Data Sources

| Dataset | Source | Spatial Resolution |
|----------|--------|-------------------|
| Sentinel-2 MSI | ESA Copernicus | 10 m |
| Hansen Global Forest Change | University of Maryland | 30 m |
| SRTM DEM | NASA / USGS | 30 m |
| Human–Elephant Conflict Records | Karnataka Forest Department | Point observations |
| Administrative Boundaries | Survey of India | Vector |
| Road Network | OpenStreetMap | Vector |

---

# Computational Workflow

```text
             Satellite Imagery
                    │
                    ▼
      Land Cover Classification
                    │
                    ▼
         Forest Change Detection
                    │
                    ▼
      Landscape Resistance Surface
                    │
                    ▼
       Least-Cost Corridor Analysis
                    │
                    ▼
 Human–Elephant Conflict Incidents
                    │
                    ▼
      Kernel Density Estimation
                    │
                    ▼
     Integrated Spatial Overlay
                    │
                    ▼
 Conservation Priority Mapping
                    │
                    ▼
 Scientific Maps & Decision Support
```

---

# Methodology

EcoCorridorAI follows a reproducible computational workflow consisting of six analytical stages.

## 1. Land Cover Classification

Sentinel-2 multispectral imagery is processed within Google Earth Engine.

Spectral bands together with vegetation and moisture indices are used to classify

- Forest
- Agroforestry
- Agriculture
- Built-up
- Water

using a Random Forest classifier.

---

## 2. Forest Change Detection

Historical tree-cover loss is quantified using Hansen Global Forest Change data to identify

- forest degradation
- expanding agricultural frontiers
- temporal loss dynamics

between 2010 and 2023.

---

## 3. Ecological Resistance Modelling

Landscape resistance is estimated using

- land-cover classes
- slope
- roads
- settlements

to construct a movement-cost surface representing ecological permeability for elephant movement.

---

## 4. Corridor Modelling

Least-cost path analysis identifies functional wildlife corridors that remain ecologically accessible despite landscape fragmentation.

---

## 5. Conflict Hotspot Analysis

Kernel Density Estimation transforms georeferenced conflict records into continuous spatial intensity surfaces.

Bandwidth optimisation balances spatial precision with statistical stability.

---

## 6. Integrated Landscape Analysis

Spatial overlays combine

- resistance
- corridor accessibility
- forest loss
- conflict intensity

to identify regions where ecological degradation most strongly coincides with elevated human–elephant conflict.

---

# Repository Structure

```text
EcoCorridorAI/

├── data/
│   ├── raw/
│   └── processed/
│
├── gee/
│   └── sentinel2_classification.js
│
├── src/
│   ├── preprocess.py
│   ├── classify.py
│   ├── forest_change.py
│   ├── corridor.py
│   ├── hotspots.py
│   ├── overlay.py
│   └── visualise.py
│
├── outputs/
│   ├── maps/
│   └── tables/
│
├── docs/
│   ├── methodology.md
│   ├── resistance_model.md
│   ├── validation.md
│   ├── limitations.md
│   └── references.md
│
├── notebooks/
│   └── exploration.ipynb
│
├── requirements.txt
└── README.md
```

---

# Installation

## Requirements

- Python 3.10+
- GDAL
- Google Earth Engine
- QGIS (optional)

```bash
git clone https://github.com/navvyiin/EcoCorridorAI.git

cd EcoCorridorAI

python -m venv env

source env/bin/activate

pip install -r requirements.txt
```

Authenticate Google Earth Engine

```bash
earthengine authenticate
```

---

# Running the Framework

Execute the complete analytical workflow

```bash
python src/preprocess.py

python src/classify.py

python src/forest_change.py

python src/corridor.py

python src/hotspots.py

python src/overlay.py

python src/visualise.py
```

Alternatively, run the Google Earth Engine classification script directly within the Earth Engine Code Editor before executing the remaining Python pipeline.

---

# Outputs

The framework produces

- Classified land-cover maps
- Forest loss maps
- Ecological resistance surfaces
- Wildlife corridor maps
- Conflict hotspot maps
- Integrated conservation priority maps
- Publication-ready figures
- Summary statistics

---

# Engineering Challenges

The greatest challenge was integrating heterogeneous spatial datasets into a consistent ecological modelling framework.

Each dataset differed in

- spatial resolution
- coordinate reference systems
- temporal coverage
- classification schemes
- uncertainty

Developing a reproducible preprocessing pipeline capable of harmonising satellite imagery, forest change products, terrain models, ecological variables, and conflict observations required substantially more engineering effort than implementing the machine learning algorithms themselves.

A second challenge involved ecological resistance modelling.

Unlike conventional machine learning problems, movement resistance cannot be learned directly from labelled data.

Instead, resistance values were derived from ecological literature and landscape characteristics, requiring careful integration of computational methods with ecological domain knowledge.

---

# Applications

EcoCorridorAI can support

- Conservation Planning
- Wildlife Corridor Assessment
- Landscape Ecology
- Forest Management
- Environmental Impact Assessment
- Biodiversity Monitoring
- Spatial Decision Support
- Climate Adaptation Planning
- Geospatial Artificial Intelligence Research

---

# Current Limitations

Current limitations include

- resistance values derived from expert-informed assumptions rather than GPS telemetry
- dependence on reported conflict incidents
- cloud contamination in optical satellite imagery
- static corridor modelling
- absence of behavioural movement simulation

These limitations represent opportunities for future research rather than software deficiencies.

---

# Future Work

Future development will explore

- Graph Neural Networks for wildlife movement prediction
- Agent-based elephant movement simulation
- Temporal corridor evolution modelling
- Foundation Models for Earth Observation
- SAR integration using Sentinel-1
- Cloud-native raster analytics
- Distributed geospatial processing with Dask
- Climate-driven habitat suitability modelling
- Real-time conservation dashboards
- Reinforcement learning for landscape restoration optimisation

---

# Scientific Significance

EcoCorridorAI demonstrates how remote sensing, spatial statistics, machine learning, and ecological modelling can be integrated into a unified computational framework for biodiversity conservation.

Rather than treating conservation mapping as a sequence of disconnected GIS operations, the framework formalises landscape analysis into a reproducible scientific workflow capable of supporting both ecological research and practical conservation decision-making.

---

# Citation

If you use EcoCorridorAI in academic work, please cite

```text
Naval Kishore

EcoCorridorAI: A Computational Framework for Mapping Agroforestry Encroachment, Landscape Connectivity, and Human–Elephant Conflict Using Earth Observation and Spatial Intelligence.

GitHub Repository, 2026.
```

Please also acknowledge the Karnataka Forest Department for the Human–Elephant Conflict incident records where applicable.

---

# License

Released under the MIT License.

---

# Acknowledgements

EcoCorridorAI builds upon the open scientific ecosystem provided by

- Google Earth Engine
- ESA Copernicus Programme
- Hansen Global Forest Change
- GeoPandas
- Rasterio
- scikit-learn
- SciPy
- GDAL
- Shapely
- Matplotlib

whose contributions have made modern computational ecology and geospatial artificial intelligence possible.

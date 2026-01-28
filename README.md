# TRIGRS-PyWrap

A Python wrapper for the TRIGRS (Transient Rainfall Infiltration and Grid-Based Regional Slope-Stability) model, designed to simplify landslide hazard analysis workflows using Python.

## Overview

TRIGRS-PyWrap provides a Pythonic interface to the TRIGRS model, which is used for analyzing rainfall-induced landslide hazards. This wrapper handles the complexity of input file generation, model execution, and output processing, allowing researchers and engineers to focus on analysis rather than file formatting.

## Features

- **Automated Input Generation**: Creates properly formatted TRIGRS input files from Python data structures
- **DEM Processing**: Integrated tools for processing digital elevation models (DEMs)
- **Geological Data Integration**: Rasterization of geological properties from vector data
- **Flow Direction Analysis**: Automatic computation of hydrological flow directions
- **Slope Stability Analysis**: Factor of safety calculations with uncertainty quantification
- **Batch Processing**: Support for parameter sensitivity analysis and Monte Carlo simulations
- **Spatial Data Handling**: Native support for georeferenced raster and vector data formats

## Installation

### Prerequisites

- Python 3.12 or higher
- TRIGRS executables included (`TRIGRS.exe`, `TopoIndex.exe`, `gridmatch.exe`)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/federicogmz/trigrs-pywrap.git
cd trigrs-pywrap
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .trigrsenv
source .trigrsenv/bin/activate 
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

TRIGRS-PyWrap is conceived to work on Windows Subsystem for Linux.

### Basic Example

```python
import geopandas as gpd
from geohazards import TRIGRS

# Load input data
dem_path = "path/to/dem.tif"
geo = gpd.read_file("path/to/geological_units.shp")

# Initialize TRIGRS model
model = TRIGRS(dem_path=dem_path, geo=geo)

# Run analysis
fs = model(
    out_path="source_code/",
    geo_columns=["Cohesion", "Friction", "Gamma", "Permeability"],
    hora=4,  # Duration in hours
    cri=21,  # Critical rainfall intensity (mm/h)
    amenaza=True  # Enable hazard assessment mode
)
```

### Input Data Requirements

#### Digital Elevation Model (DEM)
- Format: GeoTIFF (`.tif`)
- Projection: Any projected coordinate system
- Values: Elevation in meters

#### Geological Units
- Format: Shapefile (`.shp`) or GeoJSON
- Required fields:
  - `Cohesion`: Soil cohesion (kPa)
  - `Friction`: Internal friction angle (degrees)
  - `Gamma`: Unit weight (kN/m³)
  - `Permeability`: Saturated hydraulic conductivity (m/s)
  - `Zona`: Zone identifier (integer)

### Output

The model generates:
- Factor of safety grids
- Minimum factor of safety locations
- Hazard index (when `amenaza=True`)
- TRIGRS log files and intermediate products

## Project Structure

```
trigrs-pywrap/
├── geohazards.py      # Main TRIGRS wrapper class
├── Trigrs.py          # Example usage script
├── requirements.txt   # Python dependencies
└── source_code/       # TRIGRS source executables
```

## Key Classes

### `geohazards`
Base class providing spatial data processing utilities:
- DEM preprocessing and hillshade generation
- Slope calculation
- Flow direction analysis
- Raster export to ASCII format
- Catani soil thickness model

### `TRIGRS`
Main wrapper class extending `geohazards`:
- TRIGRS input file generation
- Model execution and output parsing
- Uncertainty quantification
- Batch processing for sensitivity analysis

## Advanced Features

### Hazard Assessment Mode

Enable uncertainty quantification by setting `amenaza=True`:

```python
hazard_index = model(
    out_path="output/",
    geo_columns=["C", "P", "G", "K"],
    hora=4,
    cri=21,
    amenaza=True
)
```

This runs multiple simulations with parameter perturbations and computes a confidence-based hazard index.

## Dependencies

Key dependencies include:
- `geopandas`: Vector data handling
- `rasterio` / `rioxarray`: Raster I/O
- `xarray`: Multi-dimensional arrays
- `pysheds`: Hydrological analysis
- `geocube`: Vector to raster conversion
- `numpy`, `scipy`: Numerical computations
- `matplotlib`: Visualization

See [requirements.txt](requirements.txt) for complete list.

## Limitations

- Requires TRIGRS executables (Windows-based, requires WSL)
- Currently supports ESRI flow direction convention

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is open source. Please check with the repository maintainer for specific license terms.

## Acknowledgments

- USGS for the original TRIGRS model
- Python geospatial community for excellent tools

## Contact

For questions or issues, please open an issue on [GitHub](https://github.com/federicogmz/trigrs-pywrap/issues).

## References

1. Baum, R.L., Savage, W.Z., and Godt, J.W., 2008, TRIGRS—A Fortran Program for Transient Rainfall Infiltration and Grid-Based Regional Slope-Stability Analysis, Version 2.0: U.S. Geological Survey Open-File Report 2008-1159.

2. Catani, F., Segoni, S., and Falorni, G., 2010, An empirical geomorphology-based approach to the spatial prediction of soil thickness at catchment scale: Water Resources Research, v. 46.

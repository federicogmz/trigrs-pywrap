# %%
import geopandas as gpd

from geohazards import TRIGRS

dem_path = "Ejemplo_TRIGRS/DTM.tif"
geo_path = "Ejemplo_TRIGRS/UGS.shp"

geo = gpd.read_file(geo_path)

geo_columns = ["C", "P", "G", "K"]

t = TRIGRS(dem_path=dem_path, geo=geo)
fs = t(
    out_path="trigrs-pywrap/source_code/",
    geo_columns=["C", "P", "G", "K"],
    hora=4,
    cri=21,
    amenaza=True,
)

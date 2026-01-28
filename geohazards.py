import os
import re
import rasterio
import rioxarray
import subprocess
import numpy as np
import xarray as xr
import geopandas as gpd
from scipy import ndimage
from pysheds.grid import Grid
import matplotlib.pyplot as plt
from geocube.api.core import make_geocube


class geohazards:

    def __init__(self, dem_path: str, geo: gpd.GeoDataFrame):
        """
        Inicializa clase padre y crea variables base.

        Args:
            dem_path (str): Ruta al archivo de datos del modelo de elevación digital.
            geo (gpd.GeoDataFrame): Ruta al archivo de datos de las unidades geológicas.
        """
        self.figsize = (12, 8)
        self.dem_path = dem_path
        self.dem = xr.open_dataarray(dem_path)
        self.geo = geo

        self.extent = [
            self.geo.total_bounds[0],
            self.geo.total_bounds[2],
            self.geo.total_bounds[1],
            self.geo.total_bounds[3],
        ]

        self.hillshade = self._hillshade()

    def preprocess_dem(self, dem_path):

        print("--- Preprocessing DTM. ---")

        with rasterio.open(dem_path) as src:
            data = src.read(1, masked=True)
            nodata_mask = data.mask

            dilated_mask = ndimage.binary_dilation(nodata_mask)

            data_filled = data.copy()
            data_filled[nodata_mask] = np.mean(data[dilated_mask])

            profile = src.profile
            with rasterio.open(dem_path, "w", **profile) as dst:
                dst.write(data_filled, 1)

        print("--- DTM successfully proccessed. ---")

        dem = xr.open_dataarray(dem_path)

        return dem

    def rasterizar_columna(self, gdf, columna: str):
        """
        Rasteriza una columna específica de un geodataframe.

        Args:
            gdf (geopandas.GeoDataFrame): geodataframe que contiene columna a rasterizar.
            columna (str): Nombre de la columna que se desea rasterizar.

        Returns:
            xarray.DataArray: Mapa rasterizado de la columna especificada.
        """

        return make_geocube(
            vector_data=gdf, measurements=[columna], like=self.dem, fill=np.nan
        )[columna]

    def geo_variables(self, geo_columns):
        """
        Rasteriza las variables geográficas especificadas.

        Args:
            geo_columns (lsit): Lista que contiene los nombres de las columnas geográficas.
        """

        cohesion, friccion, gamma, permeabilidad = geo_columns

        self.c = self.rasterizar_columna(self.geo, cohesion)
        p = self.rasterizar_columna(self.geo, friccion)
        self.p = np.deg2rad(p)
        self.g = self.rasterizar_columna(self.geo, gamma)
        self.k = self.rasterizar_columna(self.geo, permeabilidad)

    def resample(self, input, resolution, export=False, output=""):

        inputRaster = rioxarray.open_rasterio(input)

        # Resample the dataset to the new resolution
        rasterResample = inputRaster.rio.reproject(
            dst_crs=inputRaster.rio.crs, resolution=resolution
        )[0]

        if export:
            rasterResample.rio.to_raster(output)

        return rasterResample

    def exportASCII(self, data, output, fmt="%f"):

        if len(data.shape) == 3:
            data = data.squeeze()

        # Convert DataArray to NumPy array
        data_array = data.values

        # Get the shape of the array
        rows, cols = data.sizes["y"], data.sizes["x"]

        # Write the ASCII file
        with open(output, "w") as f:
            # Write the header information
            f.write("ncols {}\n".format(cols))
            f.write("nrows {}\n".format(rows))
            f.write("xllcorner {}\n".format(data.x.values[0]))
            f.write("yllcorner {}\n".format(data.y.values[0]))
            f.write("cellsize {}\n".format(float(data.coords["x"].diff("x").values[0])))
            f.write("NODATA_value -9999\n")

            data_array = np.where(np.isnan(data_array), -9999, data_array)

            # Write the data with custom formatting
            np.savetxt(f, data_array, fmt=fmt, delimiter=" ")

        print(f"Raster exported succesfully to {output}.")

    def Catani(self, hmin=0.1, hmax=5.0):
        """
        Function to get soil thickness from model S Catani et. al (2010)
        """

        slope_rad = self.Slope(unit="rad")

        if isinstance(hmin, str):
            hmin = make_geocube(
                vector_data=self.geo, measurements=[hmin], like=self.dem, fill=np.nan
            )[hmin]

        if isinstance(hmax, str):
            hmax = make_geocube(
                vector_data=self.geo, measurements=[hmax], like=self.dem, fill=np.nan
            )[hmax]

        # Calculates variables with Tangent
        tan_slope = np.tan(slope_rad)
        tan_slope_max = np.tan(np.nanmax(slope_rad))
        tan_slope_min = np.tan(np.nanmin(slope_rad))

        # Calculates soil thickness
        catani = hmax * (
            1
            - ((tan_slope - tan_slope_min) / (tan_slope_max - tan_slope_min))
            * (1 - (hmin / hmax))
        )

        catani = xr.DataArray(
            catani, coords=[self.dem.coords["y"], self.dem.coords["x"]]
        )

        catani = catani.where(~np.isnan(self.dem), np.nan).squeeze()

        return catani

    def Slope(self, unit: str = "deg") -> xr.DataArray:
        """
        Calcula la pendiente a partir del DEM.

        Args:
            unit: Unidad de salida ('deg' para grados, 'rad' para radianes)

        Returns:
            DataArray con la pendiente calculada
        """
        dx, dy = self.dem.rio.resolution()
        dzdx = (self.dem.shift(x=1) - self.dem.shift(x=-1)) / (2 * dx)
        dzdy = (self.dem.shift(y=1) - self.dem.shift(y=-1)) / (2 * dy)

        slope = np.arctan(np.sqrt(dzdx**2 + dzdy**2))[0]
        return np.degrees(slope) if unit == "deg" else slope

    def flowdir(self):

        # Create a PySheds grid
        grid = Grid.from_raster(self.dem_path)
        dem = grid.read_raster(self.dem_path)

        # Return the preprocessed DEM array
        pit_filled_dem = grid.fill_pits(dem)
        flooded_dem = grid.fill_depressions(pit_filled_dem)
        inflated_dem = grid.resolve_flats(flooded_dem)

        flow_direction = grid.flowdir(inflated_dem, nodata_out=-9999)

        # Convert to xarray DataArray
        flow_direction = xr.DataArray(
            flow_direction, coords=[self.dem.coords["y"], self.dem.coords["x"]]
        )

        flow_direction = flow_direction.where(flow_direction > 0, np.nan)

        flow_direction.rio.write_crs(self.dem.rio.crs, inplace=True)

        return flow_direction

    def _hillshade(self, sun_elevation=45, sun_azimuth=315):
        """
        Calcula el sombreado del terreno a partir del modelo de elevación digital.

        Args:
            sun_elevation (float): Elevación solar en grados.
            sun_azimuth (float): Azimut solar en grados.

        Returns:
            ndarray: Sombreado del terreno.
        """

        dem = self.dem[0].values

        sun_elevation = np.radians(sun_elevation)
        sun_azimuth = np.radians(sun_azimuth)

        slope = np.arctan(
            np.sqrt(np.square(np.gradient(dem)[0]) + np.square(np.gradient(dem)[1]))
        )
        aspect = np.arctan2(-np.gradient(dem)[0], np.gradient(dem)[1])

        hillshade = (
            255
            * (
                (np.cos(sun_elevation) * np.cos(slope))
                + (np.sin(sun_elevation) * np.sin(slope) * np.cos(aspect - sun_azimuth))
            )
            / 2
            + 128
        )

        return hillshade

    def plot_raster(self, titulo):
        """
        Crea gráfica con hillshade de fondo.

        Args:
            titulo (str): Título de la gráfica.

        Returns:
            tuple: Figura y ejes del gráfico.
        """

        # Plot raster data with hillshade background
        fig, ax = plt.subplots(figsize=self.figsize)
        ax.imshow(self.hillshade, cmap="gray", extent=self.extent)

        plt.title(titulo + "\n")
        plt.axis("off")
        plt.tight_layout()

        return fig, ax


class TRIGRS(geohazards):

    def __init__(
        self,
        dem_path,
        geo,
    ):

        super().__init__(dem_path, geo)

    def __call__(self, out_path, geo_columns: list, hora, cri, amenaza=False):

        self.out_path = out_path

        self.dem, self.slope, self.zonas, self.zs, self.fdir = self.Insumos()

        error = self.GridMatch(self.rows, self.cols)

        if not error:
            n, imax, rows, cols, nwf = self.TopoIndex(self.rows, self.cols)

        if n == 0:
            if not os.path.exists(f"{self.out_path}/Resultados"):
                os.makedirs(f"{self.out_path}/Resultados")

            cohesion = self.geo[geo_columns[0]].values
            friccion = self.geo[geo_columns[1]].values
            gamma = self.geo[geo_columns[2]].values
            ks = self.geo[geo_columns[3]].values

            def read_result(file_path):
                data = np.genfromtxt(file_path, skip_header=6, delimiter=" ")
                data = np.where(data == -9999, np.nan, data)
                data = np.where(data >= 10, 10, data)
                return data

            if amenaza:

                all_fs = []

                params = [
                    ("original", cohesion, friccion, gamma, ks),
                    ("c", cohesion * (1 + 0.4), friccion, gamma, ks),
                    ("f", cohesion, friccion * (1 + 0.13), gamma, ks),
                    ("g", cohesion, friccion, gamma * (1 + 0.07), ks),
                    ("c1", cohesion * (1 - 0.4), friccion, gamma, ks),
                    ("f1", cohesion, friccion * (1 - 0.13), gamma, ks),
                    ("g1", cohesion, friccion, gamma * (1 - 0.07), ks),
                ]

                for param_name, c, f, g, k in params:
                    print(
                        f"Calculando {'parámetros originales...' if param_name == 'original' else f'{param_name}...'}"
                    )

                    self.tr_in_creation(
                        imax,
                        rows,
                        cols,
                        nwf,
                        hora,
                        cri,
                        c,
                        f,
                        g,
                        k,
                        output_suffix=param_name,
                    )
                    self.TRIGRS_main()

                    fs = read_result(
                        f"{out_path}/Resultados/TRfs_min_{param_name}_1.txt"
                    )
                    fs = xr.DataArray(
                        fs, coords=[self.dem.coords["y"], self.dem.coords["x"]]
                    )
                    fs.rio.write_nodata(-9999, inplace=True)
                    fs.rio.write_crs(self.dem.rio.crs, inplace=True)

                    all_fs.append(fs)

                # Concatenate all DataArrays along a new dimension and then compute cell-wise mean and std
                self.rasters = xr.concat(all_fs, dim="simulation")
                mean_raster = self.rasters.mean(dim="simulation")
                std_raster = self.rasters.std(dim="simulation")

                Ind_conf = (mean_raster - 1) / std_raster
                Ind_conf = np.where(Ind_conf < 0, 0, Ind_conf)
                Ind_conf = np.where(Ind_conf > 10, 10, Ind_conf)
                Ind_conf = xr.DataArray(
                    Ind_conf, coords=[self.dem.coords["y"], self.dem.coords["x"]]
                )
                Ind_conf.rio.write_nodata(-9999, inplace=True)
                Ind_conf.rio.write_crs(self.dem.rio.crs, inplace=True)

                return Ind_conf

            else:
                self.tr_in_creation(
                    imax,
                    rows,
                    cols,
                    nwf,
                    hora,
                    cri,
                    cohesion,
                    friccion,
                    gamma,
                    ks,
                    output_suffix="M",
                )
                self.TRIGRS_main()

                fs = read_result(f"{out_path}/Resultados/TRfs_min_M_1.txt")
                fs = xr.DataArray(
                    fs, coords=[self.dem.coords["y"], self.dem.coords["x"]]
                )
                fs.rio.write_nodata(-9999, inplace=True)
                fs.rio.write_crs(self.dem.rio.crs, inplace=True)

                return fs

    def Insumos(self):

        fdir = self.flowdir()

        # Pendiente
        slope = self.Slope(unit="deg")

        # Espesor
        zs = self.Catani()

        # Zonas
        self.geo.geometry = self.geo.geometry.map(lambda x: x.buffer(10).union(x))

        self.zones = self.geo["Zona"].max().astype(int)

        zonas = make_geocube(
            vector_data=self.geo, measurements=["Zona"], like=self.dem, fill=np.nan
        )["Zona"]

        zonas = zonas.rio.reproject_match(self.dem)
        fdir = fdir.rio.reproject_match(self.dem)
        slope = slope.rio.reproject_match(self.dem)
        zs = zs.rio.reproject_match(self.dem)

        # Create a mask where ANY raster contains NaNs
        common_mask = (
            np.isnan(self.dem)
            | np.isnan(zonas)
            | np.isnan(zs)
            | np.isnan(fdir)
            | np.isnan(slope)
        )

        # Apply common mask to all rasters
        dem = self.dem.where(~common_mask)
        zonas = zonas.where(~common_mask)
        zs = zs.where(~common_mask)
        fdir = fdir.where(~common_mask)
        slope = slope.where(~common_mask)

        if (
            dem.isnull().sum().values
            == zs.isnull().sum().values
            == fdir.isnull().sum().values
            == slope.isnull().sum().values
            == zonas.isnull().sum().values
        ):
            print("\nNaN match in all rasters.\n")
            print("----- Exporting ASCII. -----")

            self.exportASCII(dem, f"{self.out_path}/dem.asc")
            self.exportASCII(slope, f"{self.out_path}/slope.asc")
            self.exportASCII(zonas, f"{self.out_path}/zonas.asc", fmt="%d")
            self.exportASCII(zs, f"{self.out_path}/zs.asc")
            self.exportASCII(fdir, f"{self.out_path}/flowdir.asc", fmt="%d")

            print("----- ASCII exported succesfully. -----\n")

            self.rows, self.cols = dem.sizes["y"], dem.sizes["x"]

        else:

            print(f"Dem NaN: {dem.isnull().sum().values}")
            print(f"Slope NaN: {slope.isnull().sum().values}")
            print(f"Zs NaN: {zs.isnull().sum().values}")
            print(f"FlowDir NaN: {fdir.isnull().sum().values}")
            print(f"Zonas NaN: {zonas.isnull().sum().values}")

            raise Exception("ASCII do not exported. NaN do not match.")

        return dem, slope, zonas, zs, fdir

    def GridMatch(self, rows, cols):

        # Create the content string with variables
        content = "number of grid files to test\n"
        content += "5\n"
        content += "rows,columns\n"
        content += f"{rows},{cols}\n"
        content += "name of input files (text string, up to 255 characters per line; one file per line, list master grid first)\n"
        content += "dem.asc\n"
        content += "zonas.asc\n"
        content += "slope.asc\n"
        content += "flowdir.asc\n"
        content += "zs.asc\n"
        content += "*** Note, Flow-direction grids need additional processing beyond the capabilities of GridMatch."

        # Write the content to the file
        with open(f"{self.out_path}/gm_in.txt", "w") as file:
            file.write(content)

        print("GridMatch input created successfully.")
        print(f"----- Executing gridmatch.exe. -----")

        os.chdir(self.out_path)
        subprocess.run(
            [f"{self.out_path}/gridmatch.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print(f"----- gridmatch.exe finished. -----")

        # Results
        mismatches = {}

        with open(f"{self.out_path}/GridMatchLog.txt", "r") as file:
            lines = file.readlines()

        # Iterate over the grid results section and extract the grid names and number of mismatches
        for i, line in enumerate(lines):
            if " Results for grid" in line:
                grid_name = lines[i + 1].strip()
            if " Number of mismatches found:" in line:
                mismatches_line = lines[i]
                mismatches_count = int(mismatches_line.split(":")[1].strip())
                mismatches[grid_name] = mismatches_count

        if all(value == 0 for value in mismatches.values()):
            print("GridMatch did not found mismatches. You can procede.\n")
            error = 0

        else:
            # Print the mismatches count for each grid
            for grid_name, count in mismatches.items():
                print(f"Mismatches found for {grid_name}: {count}")

            error = 1

        return error

    def TopoIndex(self, rows, cols):

        iterations = 100

        # Create the content string with variables
        content = "Name of project (up to 255 characters)\n"
        content += "project\n"
        content += (
            "Rows, Columns, flow-direction numbering scheme (ESRI=1, TopoIndex=2)\n"
        )
        content += f"{rows},{cols}, 1\n"
        content += "Exponent, Number of iterations\n"
        content += f"-1, {iterations}\n"
        content += "Name of elevation grid file\n"
        content += "dem.asc\n"
        content += "Name of direction grid\n"
        content += "flowdir.asc\n"
        content += "Save listing of D8 downslope neighbor cells? Enter T (.true.) or F (.false.)\n"
        content += "T\n"
        content += "Save grid of D8 downslope neighbor cells? Enter T (.true.) or F (.false.)\n"
        content += "T\n"
        content += "Save cell index number grid? Enter T (.true.) or F (.false.)\n"
        content += "T\n"
        content += "Save list of cell number and corresponding index number? Enter T (.true.) or F (.false.)\n"
        content += "T\n"
        content += "Save flow-direction grid remapped from ESRI to TopoIndex? Enter T (.true.) or F (.false.)\n"
        content += "T\n"
        content += "Name of folder to store output?\n"
        content += "tpx\\\n"
        content += "ID code for output files? (8 characters or less)\n"
        content += "project\n"

        # Write the content to the file
        with open(f"{self.out_path}/tpx_in.txt", "w") as file:
            file.write(content)

        print("TopoIndex input created successfully.\n")
        print(f"----- Executing TopoIndex.exe with {iterations} iterations. -----")

        os.chdir(self.out_path)
        if not os.path.exists(f"{self.out_path}/tpx"):
            os.makedirs(f"{self.out_path}/tpx")
        subprocess.run(
            [f"{self.out_path}/TopoIndex.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print(f"----- TopoIndex.exe finished. -----")

        # Results

        with open(f"{self.out_path}/TopoIndexLog.txt", "r") as file:
            text = file.read()

            success = "TopoIndex finished normally" in text
            error = "Corrections did not converge" in text

            if success:
                print("TopoIndex finished normally. You can procede.\n")
                imax, rows, cols, nwf = re.findall(
                    r"\b\d+\b",
                    re.search(
                        r"Data cells, Rows, Columns, Downslope cells\n(.*?)\n",
                        text,
                        re.DOTALL,
                    ).group(1),
                )
                n = 0
            if error:
                last_line = text.splitlines()[-1].strip()
                matches = re.findall(r"\d+", text.splitlines()[-2:-1][0])
                n = int(matches[-1])
                print(f"TopoIndex did not finished succesfully.\n{last_line}\n")
                print(f"Cells that do not converge: {n}\n")
                imax = rows = cols = nwf = 0

        return n, imax, rows, cols, nwf

    def tr_in_creation(
        self,
        imax,
        rows,
        cols,
        nwf,
        hora,
        i,
        cohesion,
        friccion,
        gamma,
        ks,
        output_suffix,
    ):

        # tr_in file creation
        # Define the variable values
        tx = 10
        nmax1 = 30
        nzs = 10
        mmax = 30
        nper = 1
        zmin = 0.001
        uww = 9800
        t = hora * 3600
        zones = self.zones
        zmax = depth = -3
        rizero = 1.0e-6
        min_slope_angle = 0
        cri = i / (1000 * 3600)  # Intensidad en m/s

        cohesion = cohesion * 1000
        phi = friccion
        gamma = gamma * 1000
        k_sat = ks
        diffus = ks * 100
        theta_sat = [-0.23] * zones
        theta_res = [-0.48] * zones
        alpha = [-0.06] * zones

        capt = [0, t]

        slope_file = f"{self.out_path}/slope.asc"
        zone_file = f"{self.out_path}/zonas.asc"
        depth_file = f"{self.out_path}/zs.asc"
        init_depth_file = f"{self.out_path}/zs.asc"
        infil_rate_file = "none"
        rainfall_files = "none"

        runoff_receptor_file = "tpx\\TIdscelGrid_project.txt"
        runoff_order_file = "tpx\\TIcelindxList_project.txt"
        runoff_cell_list_file = "tpx\\TIdscelList_project.txt"
        runoff_weighting_file = "tpx\\TIwfactorList_project.txt"
        output_folder = "Resultados\\"

        save_runoff_grid = False
        save_factor_of_safety_grid = True
        save_depth_of_safety_grid = False
        save_pore_pressure_grid = False
        save_infil_rate_grid = False
        save_unsat_zone_flux_grid = False
        save_pressure_head_flag = 0
        num_output_times = 1
        output_times = t
        skip_other_timesteps = False
        use_analytic_solution = True
        estimate_positive_pressure_head = True
        use_psi0 = True
        log_mass_balance = True
        flow_direction = "gener"
        add_steady_background_flux = True

        # Generate the text
        content = "Name of project (up to 255 characters)\n"
        content += "Project\n"
        content += "imax, row, col, nwf, tx, nmax\n"
        content += f"{imax}, {rows}, {cols}, {nwf}, {tx}, {nmax1}\n"
        content += "nzs, mmax, nper, zmin, uww, t, zones\n"
        content += f"{nzs}, {mmax}, {nper}, {zmin}, {uww}, {t}, {zones}\n"
        content += "zmax, depth, rizero, Min_Slope_Angle (degrees)\n"
        content += f"{zmax}, {depth}, {rizero}, {min_slope_angle}\n"

        for i in range(zones):
            content += f"zone,{i+1}\n"
            content += "cohesion,phi,uws,diffus,K-sat,Theta-sat,Theta-res,Alpha\n"
            content += f"{cohesion[i]},{phi[i]},{gamma[i]},{diffus[i]},{k_sat[i]},{theta_sat[i]},{theta_res[i]},{alpha[i]}\n"

        content += "cri(1), cri(2), ..., cri(nper)\n"
        content += f"{cri}\n"
        content += "capt(1), capt(2), ..., capt(n), capt(n+1)\n"
        content += f"{','.join(map(str, capt))}\n"
        content += "File name of slope angle grid (slofil)\n"
        content += f"{slope_file}\n"
        content += "File name of property zone grid (zonfil)\n"
        content += f"{zone_file}\n"
        content += "File name of depth grid (zfil)\n"
        content += f"{depth_file}\n"
        content += "File name of initial depth of water table grid (depfil)\n"
        content += f"{init_depth_file}\n"
        content += "File name of initial infiltration rate grid (rizerofil)\n"
        content += f"{infil_rate_file}\n"
        content += (
            "List of file name(s) of rainfall intensity for each period, (rifil())\n"
        )
        content += f"{rainfall_files}\n"
        content += "File name of grid of D8 runoff receptor cell numbers (nxtfil)\n"
        content += f"{runoff_receptor_file}\n"
        content += "File name of list of defining runoff computation order (ndxfil)\n"
        content += f"{runoff_order_file}\n"
        content += "File name of list of all runoff receptor cells (dscfil)\n"
        content += f"{runoff_cell_list_file}\n"
        content += "File name of list of runoff weighting factors (wffil)\n"
        content += f"{runoff_weighting_file}\n"
        content += "Folder where output grid files will be stored (folder)\n"
        content += f"{output_folder}\n"
        content += "Identification code to be added to names of output files (suffix)\n"
        content += f"{output_suffix}\n"
        content += "Save grid files of runoff? Enter T (.true.) or F (.false.)\n"
        content += f"{str(save_runoff_grid)}\n"
        content += (
            "Save grid of minimum factor of safety? Enter T (.true.) or F (.false.)\n"
        )
        content += f"{str(save_factor_of_safety_grid)}\n"
        content += "Save grid of depth of minimum factor of safety? Enter T (.true.) or F (.false.)\n"
        content += f"{str(save_depth_of_safety_grid)}\n"
        content += "Save grid of pore pressure at depth of minimum factor of safety? Enter T (.true.) or F (.false.)\n"
        content += f"{str(save_pore_pressure_grid)}\n"
        content += "Save grid files of actual infiltration rate? Enter T (.true.) or F (.false.)\n"
        content += f"{str(save_infil_rate_grid)}\n"
        content += "Save grid files of unsaturated zone basal flux? Enter T (.true.) or F (.false.)\n"
        content += f"{str(save_unsat_zone_flux_grid)}\n"
        content += 'Save listing of pressure head and factor of safety ("flag")? (Enter -2 detailed, -1 normal, 0 none)\n'
        content += f"{str(save_pressure_head_flag)}\n"
        content += "Number of times to save output grids\n"
        content += f"{num_output_times}\n"
        content += "Times of output grids\n"
        content += f"{output_times}\n"
        content += "Skip other timesteps? Enter T (.true.) or F (.false.)\n"
        content += f"{str(skip_other_timesteps)}\n"
        content += "Use analytic solution for fillable porosity? Enter T (.true.) or F (.false.)\n"
        content += f"{str(use_analytic_solution)}\n"
        content += "Estimate positive pressure head in rising water table zone (i.e. in lower part of unsat zone)? Enter T (.true.) or F (.false.)\n"
        content += f"{str(estimate_positive_pressure_head)}\n"
        content += "Use psi0=-1/alpha? Enter T (.true.) or F (.false.) (False selects the default value, psi0=0)\n"
        content += f"{str(use_psi0)}\n"
        content += "Log mass balance results? Enter T (.true.) or F (.false.)\n"
        content += f"{str(log_mass_balance)}\n"
        content += 'Flow direction (enter "gener", "slope", or "hydro")\n'
        content += f"{flow_direction}\n"
        content += "Add steady background flux to transient infiltration rate to prevent drying beyond the initial conditions during periods of zero infiltration?\n"
        content += f"{str(add_steady_background_flux)}\n"

        # Write the content to the file
        with open(f"{self.out_path}/tr_in.txt", "w") as file:
            file.write(content)

        print("--- TRIGRS input created successfully. ---")

        return

    def TRIGRS_main(self):

        print(f"----- Executing TRIGRS.exe. -----")

        subprocess.run(
            [f"{self.out_path}/TRIGRS.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print(f"----- TRIGRS.exe finished. -----")

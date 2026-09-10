import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pyproj import Transformer

transformer = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)

st = pd.read_pickle("/Users/BenMaglio/develop/projects/boulder_county/data/processed_data/sawtooth_ismn.pkl")
wb = pd.read_pickle("/Users/BenMaglio/develop/projects/boulder_county/data/processed_data/wildbasin_ismn.pkl")
bw = pd.read_pickle("/Users/BenMaglio/develop/projects/boulder_county/data/processed_data/boulder_14_W.pkl")

sme2 = xr.open_dataset("/Users/BenMaglio/develop/projects/boulder_county/data/processed_data/nisar_test_stack.nc", engine='netcdf4')

fig, ax = plt.subplots(1,3)

ax[0].plot(st.index, st['0.2032-0.2032m']['value'].replace(-9999, np.nan), label='0.2032m')
ax[0].plot(st.index, st['0.508-0.508m']['value'].replace(-9999, np.nan), label='0.508m')
ax[0].plot(st.index, st['1.016-1.016m']['value'].replace(-9999, np.nan), label='1.016m')

x1, y1 = transformer.transform(st.attrs['lon'], st.attrs['lat'])

sme2.soilMoisture.sel(xCoordinates=x1, yCoordinates=y1, method="nearest").plot(ax=ax[0], label='nisar', color='r')

ax[1].plot(wb.index, wb['0.2032-0.2032m']['value'].replace(-9999, np.nan), label='0.2032m')
ax[1].plot(wb.index, wb['0.508-0.508m']['value'].replace(-9999, np.nan), label='0.508m')

x2, y2 = transformer.transform(wb.attrs['lon'], wb.attrs['lat'])

sme2.soilMoisture.sel(xCoordinates=x2, yCoordinates=y2, method="nearest").plot(ax=ax[1], label='nisar', color='r')

ax[2].plot(bw.index, bw['0.05-0.05m']['value'].replace(-9999, np.nan), label='0.05m')
ax[2].plot(bw.index, bw['0.1-0.1m']['value'].replace(-9999, np.nan), label='0.1m')

x3, y3 = transformer.transform(bw.attrs['lon'], bw.attrs['lat'])

sme2.soilMoisture.sel(xCoordinates=x3, yCoordinates=y3, method="nearest").plot(ax=ax[2], label='nisar', color='r')

ax[0].legend()
ax[1].legend()
ax[2].legend()

ax[0].set_title("Sawtooth")
ax[1].set_title("Wild Basin")
ax[2].set_title("Boulder County 14W")

plt.show()

fig, ax =plt.subplots(1,3)
sme2.soilMoistureUncertainty.sel(xCoordinates=x1, yCoordinates=y1, method="nearest").plot(ax=ax[0], label='nisar', color='r')
sme2.soilMoistureUncertainty.sel(xCoordinates=x2, yCoordinates=y2, method="nearest").plot(ax=ax[1], label='nisar', color='r')
sme2.soilMoistureUncertainty.sel(xCoordinates=x3, yCoordinates=y3, method="nearest").plot(ax=ax[2], label='nisar', color='r')

ax[0].set_title("Sawtooth")
ax[1].set_title("Wild Basin")
ax[2].set_title("Boulder County 14W")
plt.tight_layout()
plt.show()




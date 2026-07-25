import urllib.request
import os

idf_url = "https://raw.githubusercontent.com/NREL/EnergyPlus/develop/testfiles/1ZoneUncontrolled.idf"
epw_url = "https://raw.githubusercontent.com/NREL/EnergyPlus/develop/weather/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw"

print("Downloading baseline.idf...")
urllib.request.urlretrieve(idf_url, "baseline.idf")

print("Downloading weather.epw...")
urllib.request.urlretrieve(epw_url, "weather.epw")

print("Download complete. Models are ready!")

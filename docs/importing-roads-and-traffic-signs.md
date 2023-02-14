
# Importing roads and traffic signs

**Importing Nationaal Wegen Bestand**
1. Get the latest Nationaal Wegen Bestand (National Road Network)
	- Navigate to the website where you can find 'Nationaal Wegen Bestand': https://downloads.rijkswaterstaatdata.nl/nwb-wegen/geogegevens/shapefile/Nederland_totaal/.
	- Find the latest version, for example november 2022 (https://downloads.rijkswaterstaatdata.nl/nwb-wegen/geogegevens/shapefile/Nederland_totaal/01-11-2022.zip)
2. Download the network. On Linux we used:
	- '''curl -o nwb.zip https://downloads.rijkswaterstaatdata.nl/nwb-wegen/geogegevens/shapefile/Nederland_totaal/01-11-2022.zip'''
	- unzip the file, on command line we used '''unzip nwb.zip'''
	- navigate to the Wegvakken directory, for example '''cd 01-11-2022/Wegvakken/'''
	- there you will find 'Wegvakken.shp'
3. Import the network to the database, we used shp2pgsql to do this
    - Check the .env file in the repo for the right settings
    - check if you can connect to the dabase and if it has a schema named 'bereikbaarheid'
    - '''shp2pgsql -I -s 28992 'Wegvakken.shp' bereikbaarheid.nwb_wegvakken  | psql -h database -p 5432 -U bereikbaarheid_user -d bereikbaarheid'''
4. Check if the import was succesful and the table bereikbaarheid.nwb_wegvakken if filled correctly

**Importing Traffic Signs**
1. On docs.ndw.nu you can find the documentation of the dataset: https://docs.ndw.nu/api/trafficsigns/nl/index.html 
    - Download the traffic signs data for the whole country: https://data.ndw.nu/api/rest/static-road-data/traffic-signs/v2/current-state?&content-type=csv (file is about 500 MB )
    - Import the file to the database. Save the geometry column as EPSG 28992 (Amersfoort / RD New) so both the network and signs has the same EPSG  system.
    - We did this with QGIS to saved it as 'bereikbaarheid.heel_nl_20230120_verkeersborden_actueel_beeld'. 
4. Check if the table 'bereikbaarheid.heel_nl_20230120_verkeersborden_actueel_beeld' exists and has records

Variables stored in separate files (Header+values)

Filename

	Data_separate_files_header_startdate(YYYYMMDD)_enddate(YYYYMMDD)_userid_randomstring_currrentdate(YYYYMMDD).zip
	
	e.g., Data_separate_files_header_20050316_20050601.zip

	
Folder structure

	Networkname
		Stationname

		
Dataset Filename

	CSE_Network_Station_Variablename_depthfrom_depthto_startdate_enddate.ext

	CSE	- Continental Scale Experiment (CSE) acronym, if not applicable use Networkname
	Network	- Network abbreviation (e.g., OZNET)
	Station	- Station name (e.g., Widgiewa)
	Variablename - Name of the variable in the file (e.g., Soil-Moisture)
	depthfrom - Depth in the ground in which the variable was observed (upper boundary)
	depthto	- Depth in the ground in which the variable was observed (lower boundary)
	startdate -	Date of the first dataset in the file (format YYYYMMDD)
	enddate	- Date of the last dataset in the file (format YYYYMMDD)
	ext	- Extension .stm (Soil Temperature and Soil Moisture Data Set see CEOP standard)
	
	e.g., OZNET_OZNET_Widgiewa_Soil-Temperature_0.150000_0.150000_20010103_20090812.stm

	
File Content Sample
	
	REMEDHUS   REMEDHUS        Zamarron          41.24100    -5.54300  855.00    0.05    0.05  (Header)
	2005/03/16 00:00    10.30 U	M	(Records)
	2005/03/16 01:00     9.80 U M

	
Header

	CSE Identifier - Continental Scale Experiment (CSE) acronym, if not applicable use Networkname
	Network	- Network abbreviation (e.g., OZNET)
	Station	- Station name (e.g., Widgiewa)
	Latitude - Decimal degrees. South is negative.
	Longitude - Decimal degrees. West is negative.
	Elevation - Meters above sea level
	Depth from - Depth in the ground in which the variable was observed (upper boundary)
	Depth to - Depth in the ground in which the variable was observed (lower boundary)

	
Record

	UTC Actual Date and Time
	yyyy/mm/dd HH:MM
	Variable Value
	ISMN Quality Flag
	Data Provider Quality Flag, if existing


Network Information

	SNOTEL
		Abstract: The Natural Resources Conservation Service (NRCS) installs, operates, and maintains an extensive, automated system to collect snowpack and related climatic data in the Western United States called SNOTEL (for SNOwpack TELemetry). The system evolved from NRCS"s Congressional mandate in the mid-1930"s "to measure snowpack in the mountains of the West and forecast the water supply." The programs began with manual measurements of snow courses; since 1980, SNOTEL has reliably and efficiently collected the data needed to produce water supply forecasts and to support the resource management activities of NRCS and others.
		Continent: Americas
		Country: USA
		Stations: 509
		Status: running
		Data Range: from 1980-01-01 
		Type: project
		Url: http://www.wcc.nrcs.usda.gov/
		Reference: Leavesley et al (2010), ‘A modelling framework for improved agricultural water-supply forecasting’;

Leavesley, G., David, O., Garen, D., Lea, J., Marron, J., Pagano, T., Perkins, T. & Strobel, M. (2008), ‘A modeling framework for improved agricultural water supply forecasting’, AGU Fall Meeting Abstracts;
		Variables: air temperature, snow depth, snow water equivalent, soil moisture, soil temperature, 
		Soil Moisture Depths: 0.00 - 0.00 m, 0.05 - 0.05 m, 0.10 - 0.10 m, 0.20 - 0.20 m, 0.30 - 0.30 m, 0.36 - 0.36 m, 0.40 - 0.40 m, 0.46 - 0.46 m, 0.51 - 0.51 m, 0.61 - 0.61 m, 0.69 - 0.69 m, 0.81 - 0.81 m, 0.99 - 0.99 m, 1.02 - 1.02 m, 2.03 - 2.03 m
		Soil Moisture Sensors: not-specified, Stevens-Hydraprobe-Analog, Stevens-Hydraprobe-Digital, 

	USCRN
		Abstract: Soil moisture NRT network USCRN (Climate Reference Network) in United States;the  datasets of 114 stations were collected and processed by the National Oceanicand Atmospheric Administration"s National Climatic Data Center (NOAA"s NCDC)
		Continent: Americas
		Country: USA
		Stations: 131
		Status: running
		Data Range: from 2009-06-09 
		Type: meteo
		Url: https://www.ncei.noaa.gov/access/crn/
		Reference: Bell, J. E., M. A. Palecki, C. B. Baker, W. G. Collins, J. H. Lawrimore, R. D. Leeper, M. E. Hall, J. Kochendorfer, T. P. Meyers, T. Wilson, and H. J. Diamond. 2013: U.S. Climate Reference Network soil moisture and temperature observations. J. Hydrometeorol., 14, 977-988, https://doi.org/10.1175/JHM-D-12-0146.1;
		Variables: air temperature, precipitation, soil moisture, soil temperature, surface temperature, 
		Soil Moisture Depths: 0.05 - 0.05 m, 0.10 - 0.10 m, 0.20 - 0.20 m, 0.50 - 0.50 m, 1.00 - 1.00 m
		Soil Moisture Sensors: Stevens-Hydraprobe-Digital, 


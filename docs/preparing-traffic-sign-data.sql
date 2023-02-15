-- select relevant data voor specific county to register later the corrections and supplementions
select
id ,
"ndwId",
"rvvCode",
"blackCode",
"textSigns",
roadname,
wvk_id,
concat('https://www.google.com/maps/place/',latitude,'+',longitude) as google_maps
from bereikbaarheid.heel_nl_20230120_verkeersborden_actueel_beeld
where countycode ='GM0344'  -- deze lijst is uitbreidbaar
and "rvvCode"  in ('C7','C7(Zone)','C7A','C7B','C10','C17','C18','C19','C20','C21')
ALTER TABLE bereikbaarheid.heel_nl_20230120_verkeersborden_actueel_beeld ADD PRIMARY KEY ("ndwId");
-- save the data in a spreadsheet where it can be corrected and supplemented

-- create an empty table where correction for your county can be added
CREATE TABLE bereikbaarheid.traffic_signs_gm0344_erratum (
	id int4 NULL,
	controle_status varchar(29) NULL,
	type_bord varchar(29) NULL,
	wvk_id_validated int4 NULL,
	bord_waarde float8 NULL,
	onderbord varchar(299) NULL,
	opmerking varchar(299) NULL);

-- fill bereikbaarheid.traffic_signs_gm0344_erratum with corrections from the spreadsheet

/* Note: The Traffic sign data has errors that can be corrected in this way. But more important, the Traffic Sign data of NDW is not useable for routing purposes so with the raw data you cannot determine if road is (in)accessible for a specific vehicle. Therefore we supplement the data with 3 columns:
 1) There is no information if a sign has exemptions ('uitzonderingen') or is an advance notice ('vooraankondiging')
 2) The road direction on which the sign is applicable is not stated.
 3) The column 'BlackCode with the value of the bord is not a float but text so it cannot be use to compare the vehicle value with the sign value.
 */

-- create an empty table where the source data and the corrections are combined
CREATE TABLE bereikbaarheid.traffic_signs_enriched (
	id int4 NULL,
	rvvcode varchar NULL,
	textsigns varchar NULL,
	wvk_id int4 NULL,
	"name" varchar NULL,
	image varchar NULL,
	controle_status varchar(29) NULL,
	type_bord varchar(29) NULL,
	wvk_id_validated int4 NULL,
	bord_waarde float8 NULL,
	onderbord varchar(299) NULL,
	opmerking varchar(299) NULL,
	geom public.geometry(point, 28992) NULL
);
ALTER TABLE bereikbaarheid.nwb_wegvakken_selection_gm0344_erratum ADD PRIMARY KEY ("id");
ALTER TABLE bereikbaarheid.traffic_signs_gm0344_erratum ADD PRIMARY KEY ("id");

-- check in the spreadsheet all the traffic signs manually , correct and supplement the data where needed
-- insert the data from the spreadsheet in bereikbaarheid.traffic_signs_gm0344_erratum

-- combine the source trafficsign data with the correction to get an enriched version
-- this is done for the traffic signs with the mentioned RVV codes
-- you can either create the table and recreate of truncate it and refill it (if exists).
drop table if exists bereikbaarheid.traffic_signs_enriched;
--truncate bereikbaarheid.traffic_signs_enriched;
--insert into bereikbaarheid.traffic_signs_enriched
select
b.id ,
b.ndwid,
b.rvvcode,
b.blackcode,
b.textsigns,
b.roadname as name,
b.image,
b.side,
b.wvk_id,
concat('https://www.google.com/maps/place/',b.latitude,'+',b.longitude) as google_maps,
e.controle_status,
e.type_bord,
e.wvk_id_validated,
e.bord_waarde,
e.onderbord,
e.opmerking,
b.geom
into bereikbaarheid.traffic_signs_enriched
from bereikbaarheid.heel_nl_20230120_verkeersborden_actueel_beeld b
left join bereikbaarheid.traffic_signs_gm0344_erratum e
on b.id=e.id
where b.countycode ='GM0344'  -- deze lijst is uitbreidbaar
and b.rvvcode  in ('C7','C7(Zone)','C7A','C7B','C10','C17','C18','C19','C20','C21');
ALTER TABLE bereikbaarheid.traffic_signs_enriched ADD PRIMARY KEY (id);

-- Traffic sign data is ready and will be combined with the Network with the script 'preparing-network-routing-algorithm.sql'

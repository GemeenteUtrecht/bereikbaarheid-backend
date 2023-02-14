-- add primary key to table nwb_wegvakken
ALTER TABLE bereikbaarheid.nwb_wegvakken ADD PRIMARY KEY (wvk_id);

-- select the edges from specific county for the erratum table
-- add this data in a spreadsheet and correct mistakes
-- this is a temporary to fix errors, if the quality of the source increases this step can be omitted.
select
w.wvk_id::int as id,
w.jte_id_beg::int as source,
w.jte_id_end::int as target,
w.bst_code,
case when w.bst_code in ('BU','FP','VP','OVB','CADO','RP')then false else true end as bst_code_binair,
w.rijrichtng,
w.stt_naam,
w.gme_id,
w.wegbehsrt,
w.frc,
w.geom,
gme_id
from bereikbaarheid.nwb_wegvakken w
where  gme_id=344

-- create an empty erratum table to fix nwb errors
create table bereikbaarheid.nwb_wegvakken_selection_erratum
(id int,
bst_code varchar (4),
rijrichtng varchar (1));


-- fill the erratum table with the corrections from a spreadsheet

-- generate the table nwb_wegvakken_selection_enriched
-- This is a undirected graph where corrections have been taken into account
-- the bst_code legenda can be found on zie https://www.nationaalwegenbestand.nl/download_file/185/220 (page 41)
drop table if exists bereikbaarheid.nwb_wegvakken_selection_enriched;
select w.wvk_id::int as id, --i.bst_code, e.bst_code,
w.jte_id_beg::int as source,
w.jte_id_end::int as target,
case	when e.bst_code in ('FP','VP','BU') then e.bst_code
		when e.bst_code ='auto' then null
		else w.bst_code
		end as bst_code,
case	when e.rijrichtng in ('H','B','T') then e.rijrichtng
		else w.rijrichtng end as rijrichtng,

case	when e.bst_code in ('FP','VP','BU') then false
		when e.bst_code in ('auto') then true
		when w.bst_code in ('BU','FP','VP','OVB','CADO','RP')then false
		else true end as bst_code_binair,
w.stt_naam,
w.gme_id,
w.wegbehsrt,
w.frc,
st_length(w.geom)/(50000/3600) as cost, -- 50.000 meter in 3600 seconden ;NB this is not the legal speed, just for routing purposes
w.geom,
st_transform(w.geom,4326) as geom4326
into bereikbaarheid.nwb_wegvakken_selection_enriched
from bereikbaarheid.nwb_wegvakken w
left join bereikbaarheid.nwb_wegvakken_selection_gm0344_erratum e
on w.wvk_id=e.id
where st_intersects(w.geom,(select st_buffer(geom,2000) from bereikbaarheid.gemeenten where identificatie='GM0344'))=true ;
ALTER TABLE bereikbaarheid.nwb_wegvakken_selection_enriched ADD PRIMARY KEY (id);

-- generate a directed graph that includes all the relevant information from the traffic signs
drop table if exists bereikbaarheid.nwb_wegvakken_selection_enriched_directed ;
select x.id::int,
x.source::int,
x.target::int,
x.frc,
x.gme_id,
x.wegbehsrt,
x.cost::float,
case when bordc07.c07 =1 then true when bordc07.c07 = 0 then false else false end as c07,
case when bordc07a.c07a =1 then true when bordc07a.c07a = 0 then false else false end as c07a,
case when bordc10.c10 =1 then true when bordc10.c10 = 0 then false else false end as c10,
borden17_21.c17,
borden17_21.c18,
borden17_21.c19,
borden17_21.c20,
borden17_21.c21,
bst.bst_code_binair,
x.geom::geometry(MultiLinestring,28992) as geom,
st_transform(x.geom,4326)::geometry(MultiLinestring,4326) as geom4326
into bereikbaarheid.nwb_wegvakken_selection_enriched_directed
from (
select t1.id as id,
t1.source,
t1.target,
t1.frc,
t1.gme_id,
t1.wegbehsrt,
case when t1.rijrichtng in ('B','H','O') and t1.bst_code_binair = true then st_length(t1.geom)/(50000/3600) else -1 end as cost, -- 50.000 meter in 3600 seconden ;NB this is not the legal speed, just for routing purposes
t1.geom as geom
from bereikbaarheid.nwb_wegvakken_selection_enriched t1
union all
select t2.id*-1 as id, -- negative numbers are the reversed from the normal edge to mirror
t2.target, -- this is deliberately the opposite from above to mirror
t2.source, -- this is deliberately the opposite from above to mirror
t2.frc as frc,
t2.gme_id,
t2.wegbehsrt,
case when  t2.rijrichtng in ('B','T','O') and t2.bst_code_binair= true then st_length(t2.geom)/(50000/3600) else -1 end as cost, -- 50.000 meter in 3600 seconden ;NB this is not the legal speed, just for routing purposes
st_reverse(t2.geom) as geom -- the geometry is reversed to mirror
from bereikbaarheid.nwb_wegvakken_selection_enriched t2
) as x
left join (	select
			vb.wvk_id_validated as wvk_id,
			min(case when vb.rvvcode = 'C17' then vb.bord_waarde else NULL end) as c17,
			min(case when vb.rvvcode = 'C18' then vb.bord_waarde else NULL end) as c18,
			min(case when vb.rvvcode = 'C19' then vb.bord_waarde else NULL end) as c19,
			min(case when vb.rvvcode = 'C20' then vb.bord_waarde else NULL end) as c20,
			min(case when vb.rvvcode = 'C21' or vb.rvvcode = 'C21_ZB' then vb.bord_waarde else NULL end) as c21
			from  bereikbaarheid.traffic_signs_enriched vb
			where  vb.wvk_id_validated  <> 0
			and vb.type_bord in ('verplichting')
			group by  vb.wvk_id_validated
			) as borden17_21
on x.id=borden17_21.wvk_id
left join (	select distinct wvk_id_validated as wvk_id,
			1 as c07
			from bereikbaarheid.traffic_signs_enriched vb
			where vb.rvvcode in ('C7','C7b','C7(Zone)') and vb.type_bord in ('verplichting')
			)as bordc07
on x.id=bordc07.wvk_id
left join (	select distinct wvk_id_validated as wvk_id,
			1 as c07a
			from bereikbaarheid.traffic_signs_enriched vb
			where vb.rvvcode in ('C7a') and vb.type_bord in ('verplichting')
			)as bordc07a
on x.id=bordc07a.wvk_id
left join (	select distinct wvk_id_validated as wvk_id,
			1 as c10
			from bereikbaarheid.traffic_signs_enriched vb
			where vb.rvvcode in ('C10') and vb.type_bord in ('verplichting')
			)as bordc10
on x.id=bordc10.wvk_id
left join bereikbaarheid.nwb_wegvakken_selection_enriched bst
on abs(x.id)=bst.id ;
ALTER TABLE bereikbaarheid.nwb_wegvakken_selection_enriched_directed ADD PRIMARY KEY (id);

-- make a table that consistent of all the node id's in the network
-- this is used to determine to which noded the shortest path algorith should try to find a path
drop table if exists bereikbaarheid.nwb_wegvakken_selection_node;
select distinct node::int --, geom::geometry(Point,28992)
into bereikbaarheid.nwb_wegvakken_selection_node
from (
select source as node--, st_startpoint(st_linemerge(geom)) as geom
from bereikbaarheid.nwb_wegvakken_selection_enriched_directed
union all
select target as node -- , st_endpoint(st_linemerge(geom)) as geom
from bereikbaarheid.nwb_wegvakken_selection_enriched_directed
) as x ;
ALTER TABLE bereikbaarheid.nwb_wegvakken_selection_node ADD PRIMARY KEY (node);

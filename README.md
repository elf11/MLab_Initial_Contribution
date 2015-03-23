# MLab_Initial_Contribution


This is still a work in progress, I am not extremely happy with how the graphs look like, it's not exactly relevant, still have to do the graph for the RTT Query.

1. I have started using bigQuery by looking through the examples presented on the Mlab page https://cloud.google.com/bigquery/docs/dataset-mlab , I first run the querries using the GUI provided by Google Api inside the browser, then I've set up bigQuery command line tool on my Ubuntu machine.
 There weren't any major problems that I've run into while playing with the command line tool or the GUI tool for that matter. The only thing that had the potential to raise problems was how to connect your bigQuery tool to your Google API Console, but I had experience with that before in one of my projects so it wasn't a hurdle.

2. Next, I've read the PDE Charts document and played with the available charts from the "Broadband performance using M-Lab data" set.
I've created a python script that runs the a bigQuery request using the bq tool command line and extracts the data from it in csv format. While being at it, I used the python script to generate some graphs for period of times and see how different parameters were varying over those period of times.
Below are my findings.

query1:
servers	date	total_bytes	clients

direction,country,local_ip,clients,date,total_bytes_transferred
transfer from client-to-server, over the last 6 months of 2012, all the servers are from USA, the graphs are for the number of clients for each server and the total bytes tranferred from each server to all the clients.

Still have to refine this query, the plotted data is not useful at all in this stage.

select 
  local_ip as servers,
  date,
  sum(total_bytes_transferred) as total_bytes,
  sum(clients) as clients
from (
select 
  web100_log_entry.connection_spec.local_ip as local_ip,
  COUNT(DISTINCT web100_log_entry.connection_spec.remote_ip) as clients,
  INTEGER(UTC_USEC_TO_DAY(web100_log_entry.log_time * 1000000)/1000000) as date,
  SUM(web100_log_entry.snap.HCThruOctetsReceived) as total_bytes_transferred 
from 
  [measurement-lab:m_lab.2012_07], [measurement-lab:m_lab.2012_08], [measurement-lab:m_lab.2012_09], 
  [measurement-lab:m_lab.2012_10], [measurement-lab:m_lab.2012_11], [measurement-lab:m_lab.2012_12] 
where 
  IS_EXPLICITLY_DEFINED(web100_log_entry.log_time) AND 
  IS_EXPLICITLY_DEFINED(web100_log_entry.connection_spec.local_ip) AND 
  IS_EXPLICITLY_DEFINED(web100_log_entry.connection_spec.remote_ip) AND 
  IS_EXPLICITLY_DEFINED(project) AND 
  project = 0 AND 
  IS_EXPLICITLY_DEFINED(connection_spec.data_direction) AND 
  connection_spec.data_direction = 0 AND 
  IS_EXPLICITLY_DEFINED(web100_log_entry.snap.HCThruOctetsReceived) AND 
  web100_log_entry.snap.HCThruOctetsReceived >= 8192 AND 
  IS_EXPLICITLY_DEFINED(web100_log_entry.snap.State) AND 
  (web100_log_entry.snap.State == 1 || (web100_log_entry.snap.State >= 5  && web100_log_entry.snap.State <= 11)) AND 
  IS_EXPLICITLY_DEFINED(connection_spec.server_geolocation.country_code) AND 
  connection_spec.server_geolocation.country_code = 'US' 
group by 
  date, local_ip 
order by date
) 
where
  clients > 1000
group each by
  servers, date
order by date;

For 1000 rows selected:

![alt tag](https://raw.githubusercontent.com/elf11/MLab_Initial_Contribution/master/example02_query1_1000rows_limit.png)

For 100 rows selected:

![alt tag](https://raw.githubusercontent.com/elf11/MLab_Initial_Contribution/master/example02_query1_100rows_limit.png)

(Still trying to figure out how to interpret this better...)

query2:

One of the model querries from the PDE document; I've aggregated the data based by the date and the throughput sum and order by date.

select 
  date,
  SUM(throughput) as throughput 
from (
  SELECT 
    web100_log_entry.connection_spec.remote_ip as client, 
    web100_log_entry.connection_spec.local_ip as server, 
    web100_log_entry.snap.HCThruOctetsReceived/web100_log_entry.snap.Duration as throughput, 
    INTEGER(UTC_USEC_TO_DAY(web100_log_entry.log_time * 1000000)/1000000) as date 
  FROM 
    [measurement-lab:m_lab.2012_07], [measurement-lab:m_lab.2012_08],  [measurement-lab:m_lab.2012_09], 
    [measurement-lab:m_lab.2012_10],  [measurement-lab:m_lab.2012_11], [measurement-lab:m_lab.2012_12]
  WHERE 
    IS_EXPLICITLY_DEFINED(web100_log_entry.connection_spec.remote_ip) AND 
    IS_EXPLICITLY_DEFINED(web100_log_entry.connection_spec.local_ip) AND 
    IS_EXPLICITLY_DEFINED(web100_log_entry.snap.HCThruOctetsReceived) AND 
    IS_EXPLICITLY_DEFINED(web100_log_entry.snap.Duration) AND 
    IS_EXPLICITLY_DEFINED(project) AND 
    project = 0 AND 
    IS_EXPLICITLY_DEFINED(connection_spec.data_direction) AND 
    connection_spec.data_direction = 0 AND 
    IS_EXPLICITLY_DEFINED(web100_log_entry.is_last_entry) AND 
    web100_log_entry.is_last_entry = True AND 
    web100_log_entry.snap.HCThruOctetsReceived >= 8192 AND 
    web100_log_entry.snap.Duration >= 900000 AND 
    web100_log_entry.snap.Duration < 3600000000 AND 
    (web100_log_entry.snap.State == 1 OR (web100_log_entry.snap.State >= 5 AND web100_log_entry.snap.State <= 11))
  ) 
  group by 
    date 
  order by 
    date;

![alt tag](https://raw.githubusercontent.com/elf11/MLab_Initial_Contribution/master/example01_from_query2.png)

RTT: the query used to pull RTT data from the M-Lab BigQuery dataset.
It selects the following columns: logged time (log_time),M-Lab server IP (connection_spec.server_ip), destination IP for traceroute hop - towards the client - paris_traceroute_hop.dest_ip, average of RTT in the same traceroute and hop.
The Query is performed using the Paris traceroute M-Lab utility tool and for entries logged on between 1st July 2014 and 2nd July 2014 (00:00:00 GMT). Also the field paris_traceroute_hop.rtt must not be null, the RTT data exists. The result is grouped by time and the IPs, in this way I can average multiple traceroute rtt entries.
data structure:
date	server	dest	rtt

SELECT
	log_time as date,
	connection_spec.server_ip as server,
	paris_traceroute_hop.dest_ip as dest,
	AVG(paris_traceroute_hop.rtt) AS rtt
FROM 
	[measurement-lab:m_lab.2014_07]
WHERE
	project = 3 AND
    	log_time > 1404172800 AND
	log_time < 1404259200 AND
	log_time IS NOT NULL AND
	connection_spec.server_ip IS NOT NULL AND
	paris_traceroute_hop.dest_ip IS NOT NULL AND
	paris_traceroute_hop.rtt IS NOT NULL AND
	connection_spec.client_ip != paris_traceroute_hop.dest_ip
GROUP EACH BY
	date,
	server,
	dest;

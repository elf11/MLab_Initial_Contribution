# MLab_Initial_Contribution

Initial contribution for the Socieconomic geography of access & performance MLab Outreachy project. 

This document describes my initial contribution to the MLab project and my first contact with BigQuery, how I structured and visualised the data and some preliminary conclusions.

1. I have started using bigQuery by looking through the examples presented on the Mlab page https://cloud.google.com/bigquery/docs/dataset-mlab , I first run the querries using the GUI provided by Google Api inside the browser, then I've set up bigQuery command line tool on my Ubuntu machine.
 There weren't any major problems that I've run into while playing with the command line tool or the GUI tool for that matter. The only thing that had the potential to raise problems was how to connect your bigQuery tool to your Google API Console, but I had experience with that before in one of my projects so it wasn't a hurdle.

2. Next, I've read the PDE Charts document and played with the available charts from the "Broadband performance using M-Lab data" set.
I've created a python script that runs the a bigQuery request using the bq tool command line and extracts the data from it in csv format. While being at it, I used the python script to generate some graphs for period of times and see how different parameters were varying over those period of times.

The following queries have been run using the bg.py script:

	python bg.py <id_query>

Where id_query might be 1,2, or eventually 3. The analysis of the querries and the graphs generated by them is not complete yet. I am still working through it and figuring out how to present them in a more friendly manner from which I could extract something useful.

<b> Analysis </b>

The following analysis is done based on the 3 model querries that I've run from the bg.py script. I've initially started small with the querries, and tried to visualize some of the smaller models presented on the big-query MLab data-set page, then I've expanded and run and visualised more complex querries.

The following considerations are available for the first 2 examples:

* the way I decided to structure the query was highly influenced by the PDE Charts document https://code.google.com/p/m-lab/wiki/PDEChartsNDT , in there there were presented common sense rules about how to restrict the queries and to not permit incomplete tests to affect the data; I've mostly used the conditions presented in there on how to identify and take out the incomplete tests
* next, I've considered that I should run the tests for a significant period of time, I've firstly considered to run the queries for data pertaining to the second half of 2012 (July - December). Then, after running the querries a few times and trying to sort out and correlate what I was expecting with what the data was showing I've realised that a shorter amount of time might be more appropriate, so I've decided to run the queries on the July month's data (2012).
* the general structure of the queries was influenced mainly by what I wanted to measure, I've run both queries with transfer from the client to the server connection_spec.data_direction = 0 , meaning that I've measured the upload
* something else that I've realized after reanalyzing the queries was the fact that I've ignored the web100_log_entry.is_last_entry = True , as said in the PDEChartsNDT documentation this indicates to BigQuery the result of the tests.
* some of the problems I've encountered while structuring and visualizing the results of the queries were that there was too much data and couldn't figure out a nice/neat way to make it easily readable

<b>First query<b> 

It is actually the second query in my bg.py script, it can be selected by running : python bg.py 2

This is a variation on the upload throughput query from the PDEChartsNDT documentation.  What I've did was to aggregate the transferred upload throughput for each day over a period of time of 6 months initially, the last 6 months of the 2012 year. In this case I was expecting the graph to look quite stable with some spikes around important dates in the year. The visualization of the dates on the graph are quite skewed - have to figure out how to make them look normal, but it can be seen that there's an increase in the upload from month to month, having a peak over october-november ant then going slightly down. The group by and order by date aggregation was done to be able to have statistics monthly, in a nice format.

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

* The graphs outputs the upload throughput on Y over a time period that is defined on X.
* The graph over the last 6 months can be seen in the figure below
![alt tag](https://raw.githubusercontent.com/elf11/MLab_Initial_Contribution/master/query2_6months.png)

* The graph over July 2012 can be seen below (It can be observed that there's also a little ascending trend during this month - it will be interesting to correlate this with any major internet attacks or events that happened at that time)
![alt tag](https://raw.githubusercontent.com/elf11/MLab_Initial_Contribution/master/query2_july.png)


<b>Second Query<b>

It is actually the first query in my bg.py script, it can be selected by running : python bg.py 1

The query selects the all the USA servers to which a number of at least 1000 clients have done an upload over the month of July 2012. The structure of the returned data of the query is like this:
	servers		date 	total_bytes	clients
The query is ordered by date, to have the data returned in order. I still have to refine this query, I consider that the plotted data is not useful at all in this stage. I've tried to limit the number of rows returned by the query to around 100, still it wasn't pretty. The thing is that the graph that I am trying to plot is the uploaded data per client at one US server. The uploaded throughput in bytes has been first transformed in GB then it has been divided by the number of clients (distinct) that connected to that server.

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
	  [measurement-lab:m_lab.2012_07]
	where 
	  IS_EXPLICITLY_DEFINED(web100_log_entry.log_time) AND 
	  IS_EXPLICITLY_DEFINED(web100_log_entry.connection_spec.local_ip) AND 
	  IS_EXPLICITLY_DEFINED(web100_log_entry.connection_spec.remote_ip) AND 
	  IS_EXPLICITLY_DEFINED(project) AND 
	  project = 0 AND 
	  IS_EXPLICITLY_DEFINED(connection_spec.data_direction) AND 
	  connection_spec.data_direction = 0 AND 
	  IS_EXPLICITLY_DEFINED(web100_log_entry.is_last_entry) AND 
	  web100_log_entry.is_last_entry = True AND
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

* The graph represents the US server on the X axis, and the uploaded throuput/client on the Y axis. So it's basically how much was an US server loaded by upload from clients. (Though it still looks skewed.)
![alt tag](https://raw.githubusercontent.com/elf11/MLab_Initial_Contribution/master/query1.png)


<b>Third Query</b>

In this query tried to use another tool from M-Lab the paris-traceroute utility. I used the paris-traceroute utility (project=3) to pull RTT data from the M-Lab BigQuery dataset. The query selects the following columns:
* logged time (log_time)
* M-Lab server IP (connection_spec.server_ip) 
* destination IP for traceroute hop - towards the client - paris_traceroute_hop.dest_ip 
* average of RTT in the same traceroute and hop

The query can be run by running my bg.py script like this: pythong bg.py 3

The query checks that the RTT field is valid (not null) paris_traceroute_hop.rtt and it was performed between 1st of July 2014 and 2nd of July 2014 (00:00:00 GMT). I've groupped the result by time and the IPs. In this way I could average multiple traceroute rtt entries.
The initial query looked like the one below, and returned the RTT (round time trip) between a server and a client, but I wanted to see a statistics of the number of clients and the average rtt for all the clients to each distinct server. This was a globally run query, it can be improved by adding restrictions to only run it for USA.

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

* The modified query that I've run is the following:

		SELECT
		  server,
		  count(distinct server) as server_no,
		  count(distinct dest) as client_no,
		  AVG(rtt) as rtt,
		FROM (
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
				dest
		) GROUP BY 
			server
		ORDER BY
			rtt;

* The graph that I created visualises the first 500 results, and plots the number of clients(X) and the average RTT (Y).
* The result that I was expecting was that even though for each individual client-server the RTT was sometimes quite high, on average, for all the clients connected to the same server the RTT is stable (same for all, it gets averaged to almost the same value). The loss is not so bad on average. The results of the query proved me wrong, meaning that some servers still have a bad RTT with their clients on average, sometimes huge, for example there are servers with an average number of clients around 2000 which have and RTT around 400. It looks like on average servers with a bigger number of clients fare better than those with a smaller number when it comes to RTT, but for this to be relevant we should have other type of information about those servers (like their loading, capacity etc). Also, most of those servers are clustered around the 30-80 mark on RTT for a number of clients between ~2800 and 6000.

![alt tag](https://raw.githubusercontent.com/elf11/MLab_Initial_Contribution/master/query3.png)


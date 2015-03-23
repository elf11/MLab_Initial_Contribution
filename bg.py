#!/usr/bin/python

import sys, getopt
import csv
import os
import tempfile
import time
import matplotlib.pyplot as pyplot
from matplotlib.dates import date2num
import datetime

# query1 struct:
#(initially) direction,country,local_ip,clients,date,total_bytes_transferred
# (after aggregating)servers	date	total_bytes	clients
#query2 struct:
#date, throughput
#query3 struct:
#date	server	dest	rtt


def bigquery(query):
	tmpname="/tmp/tmpbq.%s" % time.time()
	# load query
	l = open("/tmp/log.txt", 'a')
	if query is None:
		os.system("""echo "None" > %s """ % tmpname)
	else:
		cmd = "bq -q --format=csv query --max_rows=10000000 \"%s\" > %s" % (query, tmpname)
		print >>l, cmd
		l.write(cmd+"\n")
		l.flush()
		l.close()
		os.system(cmd)
	
	# load csv output
	rows = csv.reader(open(tmpname, 'r'), delimiter=",")
	header=rows.next()
	values = {}
	values.update(dict(zip(header,[ [] for i in range(0,len(header)) ])))
	# parse into dict
	for line in rows:
		for i,h in enumerate(header):
			try:
				values[h].append(float(line[i]))
			except:
				try:
					values[h].append(line[i])
				except Exception, e:
					raise Exception(cmd + str(e))

	return values

def main(argv):
#if __name__ == "__main__":
	query1 = "select local_ip as servers, date, sum(total_bytes_transferred) as total_bytes, sum(clients) as clients from (select web100_log_entry.connection_spec.local_ip as local_ip, COUNT(DISTINCT web100_log_entry.connection_spec.remote_ip) as clients, INTEGER(UTC_USEC_TO_DAY(web100_log_entry.log_time * 1000000)/1000000) as date, SUM(web100_log_entry.snap.HCThruOctetsReceived) as total_bytes_transferred from [measurement-lab:m_lab.2012_07], [measurement-lab:m_lab.2012_08], [measurement-lab:m_lab.2012_09], [measurement-lab:m_lab.2012_10], [measurement-lab:m_lab.2012_11],[measurement-lab:m_lab.2012_12] where IS_EXPLICITLY_DEFINED(web100_log_entry.log_time) AND IS_EXPLICITLY_DEFINED(web100_log_entry.connection_spec.local_ip) AND IS_EXPLICITLY_DEFINED(web100_log_entry.connection_spec.remote_ip) AND IS_EXPLICITLY_DEFINED(project) AND project = 0 AND IS_EXPLICITLY_DEFINED(connection_spec.data_direction) AND connection_spec.data_direction = 0 AND IS_EXPLICITLY_DEFINED(web100_log_entry.snap.HCThruOctetsReceived) AND web100_log_entry.snap.HCThruOctetsReceived >= 8192 AND IS_EXPLICITLY_DEFINED(web100_log_entry.snap.State) AND  (web100_log_entry.snap.State == 1 || (web100_log_entry.snap.State >= 5  && web100_log_entry.snap.State <= 11)) AND IS_EXPLICITLY_DEFINED(connection_spec.server_geolocation.country_code) AND connection_spec.server_geolocation.country_code = 'US' group by date, local_ip order by date) where clients > 1000 group each by servers, date order by date;"
	query2 = "select date,SUM(throughput) as throughput from (SELECT web100_log_entry.connection_spec.remote_ip as client, web100_log_entry.connection_spec.local_ip as server, web100_log_entry.snap.HCThruOctetsReceived/web100_log_entry.snap.Duration as throughput, INTEGER(UTC_USEC_TO_DAY(web100_log_entry.log_time * 1000000)/1000000) as date FROM [measurement-lab:m_lab.2012_07], [measurement-lab:m_lab.2012_08],  [measurement-lab:m_lab.2012_09], [measurement-lab:m_lab.2012_10],  [measurement-lab:m_lab.2012_11], [measurement-lab:m_lab.2012_12]  WHERE IS_EXPLICITLY_DEFINED(web100_log_entry.connection_spec.remote_ip) AND IS_EXPLICITLY_DEFINED(web100_log_entry.connection_spec.local_ip) AND IS_EXPLICITLY_DEFINED(web100_log_entry.snap.HCThruOctetsReceived) AND IS_EXPLICITLY_DEFINED(web100_log_entry.snap.Duration) AND IS_EXPLICITLY_DEFINED(project) AND project = 0 AND IS_EXPLICITLY_DEFINED(connection_spec.data_direction) AND connection_spec.data_direction = 0 AND IS_EXPLICITLY_DEFINED(web100_log_entry.is_last_entry) AND web100_log_entry.is_last_entry = True AND web100_log_entry.snap.HCThruOctetsReceived >= 8192 AND web100_log_entry.snap.Duration >= 900000 AND web100_log_entry.snap.Duration < 3600000000 AND (web100_log_entry.snap.State == 1 OR (web100_log_entry.snap.State >= 5 AND web100_log_entry.snap.State <= 11))) group by date order by date;"
	query3 = "SELECT log_time as date, connection_spec.server_ip as server, paris_traceroute_hop.dest_ip as dest, AVG(paris_traceroute_hop.rtt) AS rtt FROM [measurement-lab:m_lab.2014_07] WHERE project = 3 AND log_time > 1404172800 AND log_time < 1404259200 AND log_time IS NOT NULL AND connection_spec.server_ip IS NOT NULL AND paris_traceroute_hop.dest_ip IS NOT NULL AND paris_traceroute_hop.rtt IS NOT NULL AND connection_spec.client_ip != paris_traceroute_hop.dest_ip GROUP EACH BY date, server, dest;"


	query_no = int(sys.argv[1])

	if query_no == 1: #run this with a limit of rows... the graph doesn't look too good :( - 1000, 100 row limit
		diction = bigquery(query1)
		server_list = []
		throughput_list = []
		date_list = []
		clients = []
		for key, val in diction.iteritems():
			if key == 'servers':
				server_list = diction[key]
			if key == 'total_bytes':
				throughput_list = diction[key]
			if key == 'clients':
				clients = diction[key]
			if key == 'date':
				date_list = diction[key]
			#print key, 'corresponds to', diction[key]
			#print key, 'clients ', clients

		throughput_by_clients = []
		for i, j in zip(throughput_list, clients):
			throughput_by_clients.append(i/j)

		#take the index of the servers - and represents them on
		# the x-axis as the index, not the IP address of the server
		my_xticks = []
		for i, lval in enumerate(server_list):
			my_xticks.append(i)

		x1 = [val for val in server_list]
		y1 = [val for val in throughput_by_clients]
		fig = pyplot.figure()
		graph = fig.add_subplot(111)

		graph.plot(my_xticks, y1, 'r-o')
		graph.set_xticks(my_xticks)
		pyplot.savefig('example02.png')

	elif query_no == 2: 
		diction = bigquery(query2)
		date_list = []
		throughput_list = []
		for key, val in diction.iteritems():
			if key == 'date':
				val_list = diction[key]
				date_list = val_list
			if key == 'throughput':
				val_list = diction[key]
				for i, lval in enumerate(val_list):
					val_list[i] = lval / 1024
				throughput_list = val_list
			#print key, 'corresponds to', diction[key]

		x = [val for val in date_list]
		y = [val for val in throughput_list]

		fig = pyplot.figure()
		graph = fig.add_subplot(111)

		graph.plot(x, y, 'r-o')
		graph.set_xticks(x)
		graph.set_xticklabels(
			[datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d') for date in date_list]
			)

		pyplot.savefig('example01.png')
	#elif query_no == 3: #will run this one with a limit of 100 rows
	#	diction = bigquery(query1)

if __name__ == "__main__":
	main(sys.argv[1:])
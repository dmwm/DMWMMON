# Read HDFS storage dump and reformat info needed by SpaceMon

import datetime
import calendar


# Input dates are assumed to be UTC

while True:
    try:
	fileln = raw_input()
	fields = fileln.split()
	date_text = fields[5] + " " + fields[6]
	date = datetime.datetime.strptime(date_text, "%Y-%m-%d %H:%M")
	print "/hdfs" + fields[7] + "|" + fields[4] + "|" + str(calendar.timegm(date.utctimetuple())) + "|N/A"
    except EOFError:
	break


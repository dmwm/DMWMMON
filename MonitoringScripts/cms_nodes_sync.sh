#!/bin/sh
# N. Ratnikova Sep, 01, 2015
# cms_nodes_sync.sh 
#  * gets the list of node names for CMS sites from the following three sources:
#    SiteDB, phedex data service, dmwmmon data service 
#  * compares the lists and reports any discrepancies found, assuming the siteDB 
#    is the primary source of information 
#  * relies on valid grid authentication needed for access to CMS web interfaces
#
#####
# For temporary files under /tmp
tmpwork=`mktemp -d` 

function cleanup {
	# Perform program exit housekeeping
	rm -r $tmpwork
	exit $1
}
trap cleanup SIGHUP SIGINT SIGTERM

function print_title {
  for i in {1..70}; do echo -n "#"; done
  echo -e "\n#   $1"
  for i in {1..70}; do echo -n "#"; done
  echo
}

# URLs for the nodes lists: 

sitedb_nodes_url="http://cmsweb.cern.ch/sitedb/data/prod/site-names"
phedex_nodes_url="https://cmsweb.cern.ch/phedex/datasvc/perl/prod/nodes"
dmwmmon_nodes_url="https://cmsweb.cern.ch/dmwmmon/datasvc/perl/nodes"

# Specify all commands with a full path for a cron job to find them
# NOTE: these setting may differ on various systems

proxy_info_cmd=/usr/bin/grid-proxy-info # some systems may only have voms-proxy-info
wget_cmd="/usr/bin/wget -q"
awk_cmd=/usr/bin/awk
cat_cmd=/bin/cat 

# TODO: add existence check 
myproxy=`${proxy_info_cmd} -path`

# Temporary files: 
sitedb_out=${tmpwork}/sitedb.out
sitedb_list=${tmpwork}/sitedb.phedex-nodes.list
phedex_out=${tmpwork}/phedex_datasvc.out
phedex_list=${tmpwork}/phedex.datasvc-nodes.list
dmwmmon_out=${tmpwork}/dmwmmon_datasvc.out
dmwmmon_list=${tmpwork}/dmwmmon.datasvc-nodes.list
report=${tmpwork}/report.txt

#####
# Getting list of phedex nodes from the siteDB:

$wget_cmd --no-check-certificate --certificate=$myproxy \
--private-key=$myproxy --ca-certificate=$myproxy \
-O  $sitedb_out $sitedb_nodes_url

$cat_cmd $sitedb_out | $awk_cmd -F\" '/"phedex"/ {print $6}' | sort -u > \
$sitedb_list

#####
# Getting list of phedex nodes from phedex datasvc:

$wget_cmd --no-check-certificate --certificate=$myproxy \
--private-key=$myproxy --ca-certificate=$myproxy  \
-O $phedex_out $phedex_nodes_url

$cat_cmd $phedex_out |  $awk_cmd -F\'  '/NAME/ {print $4}' | sort -u > \
$phedex_list

#####
# Getting list of phedex nodes from dmwmmon datasvc:

$wget_cmd --no-check-certificate --certificate=$myproxy \
--private-key=$myproxy --ca-certificate=$myproxy \
-O $dmwmmon_out $dmwmmon_nodes_url

$cat_cmd $dmwmmon_out | $awk_cmd -F\'  '/NAME/ {print $4}' | sort -u  > \
$dmwmmon_list

# Constructing the report message: 
echo "#  Report created on "  `date` >> $report
print_title "Comparing lists of node names from the following sources : \n\
#     $sitedb_nodes_url \n\
#     $phedex_nodes_url \n\
#     $dmwmmon_nodes_url " >> $report

print_title "Nodes in SITEDB and not in TMDB: " >> $report
for f in `cat $sitedb_list`
do grep -q $f $phedex_list || echo "     $f" >> $report
done 

print_title "Nodes in TMDB and not in SITEDB: " >> $report
for f in `cat $phedex_list`
do grep -q $f $sitedb_list || echo "     $f" >> $report
done 

print_title "Nodes in DMWMMON  and not in SITEDB:" >> $report
for f in `cat $dmwmmon_list`
do grep -q $f $sitedb_list || echo "     $f" >> $report
done 

print_title "Nodes in SITEDB and not in DMWMMON: " >> $report
for f in `cat $sitedb_list`
do grep -q $f $dmwmmon_list || echo "     $f" >> $report
done

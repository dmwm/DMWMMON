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

# URLs for the nodes lists: 

sitedb_nodes="http://cmsweb.cern.ch/sitedb/data/prod/site-names"
phedex_nodes="https://cmsweb.cern.ch/phedex/datasvc/perl/prod/nodes"
dmwmmon_nodes="https://cmsweb.cern.ch/dmwmmon/datasvc/perl/nodes"

# Specify all commands with a full path for a cron job to find them
# NOTE: these setting may differ on various systems

proxy_info_cmd=/usr/bin/grid-proxy-info # some systems may only have voms-proxy-info
wget_cmd="/usr/bin/wget -q"
awk_cmd=/usr/bin/awk
cat_cmd=/bin/cat 

# TODO: add existence check 
myproxy=`${proxy_info_cmd} -path`

#####
# Getting list of phedex nodes from the siteDB:

$wget_cmd --no-check-certificate --certificate=$myproxy --private-key=$myproxy --ca-certificate=$myproxy  --ca-directory=/etc/grid-security/certificates -O ${tmpwork}/sitedb.out $sitedb_nodes
$cat_cmd ${tmpwork}/sitedb.out |  $awk_cmd -F\" '/"phedex"/ {print $6}' | sort -u  > ${tmpwork}/sitedb.phedex-nodes.list

#####
# Getting list of phedex nodes from phedex datasvc:

$wget_cmd --no-check-certificate --certificate=$myproxy --private-key=$myproxy --ca-certificate=$myproxy  --ca-directory=/etc/grid-security/certificates -O ${tmpwork}/phedex_datasvc.out $phedex_nodes
$cat_cmd ${tmpwork}/phedex_datasvc.out |  $awk_cmd -F\'  '/NAME/ {print $4}' | sort -u > ${tmpwork}/phedex.phedex-nodes.list

#####
# Getting list of phedex nodes from dmwmmon datasvc:

$wget_cmd --no-check-certificate --certificate=$myproxy --private-key=$myproxy --ca-certificate=$myproxy  --ca-directory=/etc/grid-security/certificates -O ${tmpwork}/dmwmmon_datasvc.out $dmwmmon_nodes
$cat_cmd ${tmpwork}/dmwmmon_datasvc.out |  $awk_cmd -F\'  '/NAME/ {print $4}' | sort -u  > ${tmpwork}/dmwmmon.phedex-nodes.list

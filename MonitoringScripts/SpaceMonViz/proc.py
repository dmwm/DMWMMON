import argparse
import hashlib
from datetime import datetime
import json

# command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("lfn2pfn", help="json file containing lfn2pfn mapping") # "lfn2pfn.js"
parser.add_argument("fdump", help="formatted dump records") # "dump3"
parser.add_argument("output", help="output records file") # "dump4"
args = parser.parse_args()

# user input for ES index
ESindex = raw_input("Enter an index for ES: ") # "test"

# get lfn2pfn mapping
with open(args.lfn2pfn) as file1:
    l2pd = json.load(file1) # read json file containing the mapping
l2pmap = {} # python dict that will contain the mapping
for d in l2pd['phedex']['mapping']: # data service implementation related
    if (d['pfn'] is None): # if pfn is null do not consider site at all
        print "Warning: no pfn for ", d['node'] # print warning
    else:
        l2pmap[d['node']] = d['pfn']
# corrections to lfn2pfn mapping
l2pmap['T2_US_Florida'] = "/store/"
l2pmap['T2_KR_KNU'] = "/store/"
l2pmap['T1_DE_KIT_Disk'] = "/pnfs/gridka.de/cms/disk-only/store"
l2pmap['T2_FR_IPHC'] = "/dpm/in2p3.fr/home/cmsphedex/store"
l2pmap['T2_HU_Budapest'] = "/dpm/kfki.hu/home/cms/phedex/store/"

# process records
outfile = open(args.output, 'w') # output file for curl ES loading
with open(args.fdump, 'r') as file2: # read records file
    for line in file2:
        pred = {} # needed for curl ES loading
        pred['index'] = {}
        d = json.loads(line) # single dump record
        if d['name'] in l2pmap.keys():
            # add a final forward slash to 'dir' if not present
            if d['dir'][-1] != '/': d['dir']+='/'
            # 'rlvl' represents how deep in directory tree is 'dir'
            # in comparison with the 'store' folder in lfn2pfn mapping
            # note: it just compares the number of slashes in their paths
            rlvl = d['dir'].count('/') - l2pmap[d['name']].count('/')
            d['rlvl'] = rlvl
            pred['index']['_index'] = ESindex
            #pred['index']['_index'] = ESindex + '-' + str(datetime.fromtimestamp(d['timestamp']).year)
            pred['index']['_type'] = "dump_record"
            e = {} # create subset of record fields in order to create reliable md5
            for k in ('timestamp', 'name', 'dir'):
                e[k] = d[k]
            pred['index']['_id'] = hashlib.md5(json.dumps(e, sort_keys=True)).hexdigest()
            # write to the output file
            json.dump(pred, outfile)
            outfile.write("\n")
            json.dump(d, outfile)
            outfile.write("\n")
        else: # discard record if pfn for its site is not present
            print "Warning. Record discarded because of lack of pfn:", d

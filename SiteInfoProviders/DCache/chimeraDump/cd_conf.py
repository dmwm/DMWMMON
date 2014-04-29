#!/usr/bin/env python
#Configuration of the chimera dump script

import time

mgz='bz2'
confversion='c6'

##################################################
#Change this part if you did not use the dCache defaults

db = 'chimera'
host = 'localhost'
port = 5432
user = 'postgres'
passwd = ''
rootdir = 'pnfs'

#####################################################
#Normally no need to change this, here new queries can be add and the filename can be changed

tmpname = '/tmp/pnfs-dump-'+'-'.join([str(i).zfill(2) for i in time.localtime()[0:5]])
# {"cli-Tag" : ["select part","from part","where part"],"xml-Tag"} 
sqldict = {
'pool' : \
  [("t_locationinfo.ipnfsid,iname,iparent,ilocation", "t_locationinfo, t_dirs ", "t_dirs.ipnfsid = t_locationinfo.ipnfsid"),('dCache:location',)],
'disk' : \
  [("t_locationinfo.ipnfsid,iname,iparent,istate","t_locationinfo, t_dirs","ilocation like '%s' and t_dirs.ipnfsid = t_locationinfo.ipnfsid"),('dCache:state',)],
'dump' :\
  [("t_dirs.ipnfsid,iname,iparent,isize", "t_dirs, t_inodes", "itype = '32768' and t_dirs.ipnfsid <> '000000000000000000000000000000000000' and t_dirs.ipnfsid = t_inodes.ipnfsid"),('size',)],
'atime' :\
  [("t_dirs.ipnfsid,iname,iparent,date_part('epoch', date_trunc('seconds', iatime ))", "t_dirs, t_inodes", "itype = '32768' and t_dirs.ipnfsid <> '000000000000000000000000000000000000' and t_dirs.ipnfsid = t_inodes.ipnfsid"),('dCache:atime',)],
'checksum' : \
  [("t_dirs.ipnfsid,iname,iparent,isum","t_dirs, t_inodes_checksum","t_dirs.ipnfsid = t_inodes_checksum.ipnfsid"),('checksum',)],
'NoP' : \
  [("t_dirs.ipnfsid,iname,iparent,isize", "t_dirs,t_inodes", "itype = '32768' and t_dirs.ipnfsid not in (select ipnfsid from t_locationinfo) and t_dirs.ipnfsid = t_inodes.ipnfsid"),('size',)], 
'Mpools' : \
  [("t_locationinfo.ipnfsid,iname,iparent,ilocation","t_locationinfo, t_dirs","t_dirs.ipnfsid in (select ipnfsid from t_locationinfo group by ipnfsid having count(ilocation) > 1) and t_dirs.ipnfsid = t_locationinfo.ipnfsid"),('dCache:location',)], 
'Spools' : \
  [("t_locationinfo.ipnfsid,iname,iparent,ilocation","t_locationinfo, t_dirs","t_dirs.ipnfsid in (select ipnfsid from t_locationinfo group by ipnfsid having count(ilocation) = 1) and t_dirs.ipnfsid = t_locationinfo.ipnfsid"),('dCache:location',)],
'fulldump' : \
 [("t_dirs.ipnfsid,iname,iparent,isize,istate,ilocation,date_part('epoch', date_trunc('seconds', t_inodes.iatime)),isum", "t_inodes,t_locationinfo,t_dirs,t_inodes_checksum", "t_dirs.ipnfsid = t_locationinfo.ipnfsid and t_dirs.ipnfsid = t_inodes.ipnfsid and t_dirs.ipnfsid = t_inodes_checksum.ipnfsid"),('size','dCache:state','dCache:location','dCache:atime','checksum')]#,'dCache:pinned','dCache:atime','dCache:mtime')]
}

############################33
# No some things to keep the code more readable, mostly helptext

usage = """
    %prog [-h] [-o output file>] [-s <string of pattern or pool name>] [-v <vo>] [--check <dump|pool|checksum|atime|NoP|Mpools|Spools|disk|fulldump>] [-f|--file <filename>] [-a] [-g] [-d|--debug] [-D|--Debug] \n

Example: 
  Give a xml file with all data in Path /pnfs/ifh.de/data/atlas:   
     python %prog -s /pnfs/ifh.de/data/atlas -v atlas
  Give ascii output with all files from the dataset and there pool location
     python %prog -a -s mc08.106020.PythiaWenu_1Lepton.recon.AOD.e352_s462_r541_tid028693 --check pool
  Give ascii of all files on a certain pool
     python %prog -a -s pool01-01 --check disk
  Give ascii of all Files not on any pool compressed with gzip
     python %prog -a --check NoP -g
"""

mydescription="""DESCRIPTION: Running %prog without options will give this help, options not given are filled with the default values from
the cd_conf.py file (if unaltered the dCache chimera default values)
and makes a bz2 (gz file with option <-g>) compressed xml file with all files in the SE, (even the dcache.conf file).
With -a  a (faster) output in ascii is given, still compressed.
With -c the kind of dump can be changed where dump is the default
dump will give the size, pool will give the location, checksum will give the checksum of every file ,
disk will give all files on the pool given with the string in -s, atime will give the time the file first appears in chimera.
NoP will search for files (whose path match -s string) not registered in any pool,
Mpools will give files (whose path match -s string) which are on multiple pools
Spools will give files (whose path match -s string) that are only on one pool
With -s  you can give a string which have to be in every path
OR if --check disk a string which defines the pools to list.
With -d some logging information and all directories and files will be written in a file with the same name and .log added. this will be a VERY LARGE file, be careful with your /tmp disk space
With -D even more logging information is written into the log file
With -f you can load a file with pnfsids, the script will only look for files in the list and in chimera
"""


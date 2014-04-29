#!/usr/bin/env python

import sys,time
from string import lower, strip
try:
    from xml.sax.saxutils import escape
except:
    sys.exit("""xml.sax python modul needed, please install""")
try: #Import some variables from the config file, which is thought to be in the same directory
    from cd_conf import host,passwd,port,user,db,tmpname,sqldict,mydescription,usage,mgz,rootdir,confversion
except:
    sys.exit("""No correct cd_conf.py file found in this directory (or the Pythonpath)""")

neededconvversion = 'c6'
if confversion <> neededconvversion: sys.exit("Sorry, you have the wrong configuration file (Version %s), please use the current one: %s" % (confversion,neededconvversion))

if len(sys.argv)<2:
    sys.argv.append('-h')
try:
    from optparse import OptionParser
    parser = OptionParser(usage=usage, version="%prog 0.9.1", description=mydescription)
    parser.add_option('-o', '--output', help = "Name of outputfile, xml.bz2 will be added in any case", action = "store", dest = "filen", default = tmpname)
    parser.add_option('-s', '--string', help = "String applied on search result: either Path like /data/atlas/atlasmcdisk or pool like pool-01", action = "store", dest = "pat", default = None)
    parser.add_option('-v', '--vo', help = "Name of vo: just for xml file", action = "store", dest = "vo", default = '')
    parser.add_option('-r', '--root', help = "Name of root directory of dCache", action = "store", dest = "rootdir", default = 'pnfs')
    parser.add_option('-a', '--ascii', help = "Output in ascii text", action = "store_true", dest = "ascii", default = False)
    parser.add_option('-g', '--gzip', help = "Use gzip compression", action = "store_true", dest = "mgz", default = False)
    parser.add_option('-d', '--debug', help = "Debug Modus, may create BIG log files in /tmp", action = "store_true",dest = "debug", default = False)
    parser.add_option('-D', '--Debug', help = "More Debugging Modus, may create BIG log files in /tmp", action = "store_true",dest = "mdebug", default = False)
    parser.add_option('-c', '--check', help = "Different checks: pool: give location info; dump give size info; checksum give checksum info; disk give all files on pool from string,atime gives first appearance in DB, NoP, Mpools, Spools search files not on pools, on multiple pools or on a single pool", action = "store", dest = "check", default = "dump")
    parser.add_option('-f', '--file', help = "File with given pnfsids which should be queried", action = "store", dest = "infile", default = '')
    (options, args) = parser.parse_args()
    filen=options.filen
    vo=lower(strip(options.vo))
    infile=options.infile
    pat=options.pat
    ascii=options.ascii
    debug=options.debug
    mdebug=options.mdebug
    rootdir=options.rootdir
    if mdebug: debug=True
    if options.mgz: mgz='gz'
    try:
        check,xmltag=sqldict[options.check]
    except:
        sys.exit("Error: Check Option not defined")
except ImportError:
    print "No option parser available, using hardcoded defaults"
    filen=tmpname
    vo=None
    pat=None
    ascii=False
    mgz='bz2'
    debug=False
    mdebug=False
    infile=''
    check,xmltag = sqldict['dump']

try:
    import pgdb
    moduletype='pgdb'
except ImportError:
    print "No pgdb module found, might help to install postgresql-python\n Will try psycopg"
    try:
        import psycopg2 
        moduletype='psycopg2'
    except ImportError:
        sys.exit("No psycopg2 module found, might help to install python-psycopg2-debuginfo-2.0.6-1.el5ipa.x86_64.rpm")

#Global Variables:
dirs={} #The dictionary with all dir pathes and their pnfsids as keys
global spaces
spaces=' '

def dbconnect(moduletype):
    """ """
    if moduletype=='pgdb':
        try:
            mhost="%s:%i" % (host,port)
            con=pgdb.connect(database=db,user=user, host=mhost, password=passwd)
            #con=pg.connect(db,host,port,None,None,user,passwd)
        except:
            sys.exit("Connection to database failed")
    else:
        try:
            con=psycopg2.connect("dbname=%s user=%s host=%s port=%i password=%s" % (db,user,host,port,passwd))
        except:
            sys.exit("Connection to database failed")
    return con

def getresult(con,cmd):
    """ """
    cur = con.cursor()
    cur.execute(cmd)
    result=cur.fetchall()
    #if mdebug: l.write(spaces+"SQLResult: %s \n" % result)
    return result 

def get_root():
    """ """
    cmd = " select iparent from t_dirs where iname like '%s' " % rootdir
    try:
        rootpnfsid = getresult(con,cmd)[0][0]
    except IndexError:
        sys.exit("Query for given Rootdir: '%s' did not work" % rootdir)
    return rootpnfsid

def search_parent(child):
  """ """
  cmd = "select ipnfsid,iname,iparent from t_dirs where ipnfsid = '%s' and iname not in ('.','..')" % child[2]
  global spaces
  if mdebug: l.write("%sSQLQuery: %s \n" % (spaces,cmd))
  mycont = True
  try: # catch orphaned pnfsids, => pnfsids which are parents, but do nothave a parent themselves
      parent = getresult(con,cmd)[0]
      if debug: l.write(spaces+"Found Parent: %s (pnfsid: %s) of dir %s \n" % (parent[1],parent[2],parent[0]))
  except IndexError:
      l.write("Error: pnfsid %s is parent but has no parent himself\n" % child[2])
      l.write("->Error hint: %s orphaned\n" % child[1])
      return False
  #####    
  dirs[child[2]] = ["/%s" % parent[1],False]
  if mdebug:l.write(spaces+"Dirs: %s %s %s \n" % (child[2],dirs[child[2]][0],dirs[child[2]][1]))
  if parent[2] not in dirs:
    if parent[2] <> rootpnfsid: 
      try: #catch loops, => a pnfsid is its own grandpa or even grandgrandpa
          if mdebug:l.write(spaces+"Search Parent: %s %s %s \n" % (parent[0],parent[1],parent[2]))
          if debug:spaces+=' '
          mycont = search_parent(parent)
          if debug:spaces=spaces[0:-1]
      except RuntimeError:
          message = "Error: Problems with pnfsid: %s or its parent with pnfsid: %s, maybe circular reference, be careful\n" % (parent[0],parent[2])
          l.write(message)
          l.write("->Error hint: %s\n" % parent[1])
          print "Found problems with database, use dump with care!!!\n"
          mycont = False
      #####
  else:
      dirs[child[2]]=[dirs[parent[2]][0] + dirs[child[2]][0],True]  
      if mdebug:l.write(spaces+"Written: %s\n" % dirs[child[2]])
  if mycont: # This will only fail when a loop was found
      if child[0] in dirs and not dirs[child[0]][1]:
          if mdebug:l.write(spaces+"Filling: %s %s %s\n" % (child[0],dirs[child[2]][0],dirs[child[0]][0]))
          dirs[child[0]] = [dirs[child[2]][0] + dirs[child[0]][0],True]
      if not dirs[child[2]][1]:
          dirs[child[2]][1] = True
  else:  # then the dir should be deleted to find  all other dirs pointing to this loop
      if debug: l.write("Directory Problem, deleted %s from list" % dirs[child[2]][0])
      if not dirs[child[2]][1]: del dirs[child[2]] #Delete entry if it is part of a loop
  return mycont

try: #to open the bzipped logfile
  filed=filen+'.log.bz2'
  import bz2
  l=bz2.BZ2File(filed,'w')
except:
  sys.exit("Error: Couldn't open logfile: %s.log.bz2" % filen)
    
if xmltag in ['dCache:state',]:
    cmd="select %s from %s where %s" % check % pat
    pat=''
else:
    cmd="select %s from %s where %s" % check

########reading the list of all files, this might take some time
print '   started at:            ',time.localtime()[0:6]
con=dbconnect(moduletype)
if mdebug: l.write("SQLQuery: %s \n" % cmd)
flist=getresult(con,cmd)
print '   files query done:      ',time.localtime()[0:6]
####

rootpnfsid = get_root()   # Get the pnfsid of the directory tree, needed as a stop criteria
if debug: l.write("Rootdir used: %s %s" % (rootdir,rootpnfsid))

if not ascii: filen+='.xml'
try: # to open the output file, gzipped or bzipped
 filen+='.' + mgz
 if mgz == 'gz':
  import gzip
  f=gzip.open(filen,'w')
 else:
  import bz2
  f=bz2.BZ2File(filen,'w')
except:
 print "zip module not found, write without compressing" #which is nothing good at all
 f=open(filen,'w')

if not ascii: # again for syncat xml output
    f.write("""<?xml version="1.0" encoding="UTF-8"?>\n""")
    if xmltag in ["size","checksum",""]: 
        f.write("""<cat xmlns="http://www.dcache.org/PROPOSED/2008/01/Cat">\n""")
    else:
        f.write("""<cat xmlns="http://www.dcache.org/PROPOSED/2008/01/Cat"
        xmlns:dCache="http://www.dcache.org/PROPOSED/2008/01/Cat/dCache">\n""")
    f.write("""<dump recorded="%04i-%02i-%02iT%02i:%02i:%02iZ">\n""" % time.gmtime()[0:6])
    if vo: f.write("""<for>vo:%s</for>\n""" % vo)
    f.write("""<entry-set>\n""")

if infile:
    try:
        from sets import Set
    except:
        sys.exit("Module sets not found, option -f not possible")
    try:
        infi=open(infile,'r')
    except:
        sys.exit("File for input not found: %s" % infile)
    cs=Set([i.rstrip('\n').strip() for i in infi.readlines()])
    infi.close()
    chimset=Set([i[0] for i in flist])
    checkpnfs=cs.intersection(chimset)
    if debug: l.write(spaces+"Number of files in input file AND chimera DB: %i" % len(checkpnfs))
    if debug: l.write(spaces+"Number of files in input file: %i" % len(cs))
    if infile: print '   import file merge done:',time.localtime()[0:6] 

for i in flist: # Get for each file the directory tree
  if infile:
      if debug:l.write("%sExcluding files not in %s" % (spaces,infile))
      if i[0] not in checkpnfs: continue
  if mdebug:l.write("%sLooking at %s\n" % (spaces,i[2]))
  if i[2] not in dirs:
    if debug:spaces+=' '
    mycont = search_parent(i)
    if debug:spaces=spaces[0:-1]
    if debug: l.write(spaces+dirs[i[2]][0]+i[1]+' '+str(i[3])+'\n')
    if not mycont: continue
  if pat and pat not in dirs[i[2]][0]: continue
  if ascii: entry='%s %s' % (i[0],dirs[i[2]][0]+'/'+i[1])
  else: entry='<entry name="%s">' % (dirs[i[2]][0]+'/'+i[1])
  for j in xrange(3,len(i)):
      if ascii:entry+=' %s' % str(i[j])
      else: entry+='<%s>%s</%s>' % (xmltag[j-3],escape(str(i[j])),xmltag[j-3])
  if ascii:entry+='\n' 
  else:entry+='</entry>\n' 
  f.write(entry)
#  if not ascii:
#      f.write('<entry name="%s"><%s>%s</%s></entry>\n' %(dirs[i[2]][0]+'/'+i[1],xmltag,escape(str(i[3])),xmltag))
#  else:
#      f.write('%s %s %s\n' %(i[0],dirs[i[2]][0]+'/'+i[1],str(i[3])))

if not ascii: # again for syncat xml output
    f.write(""" </entry-set>
</dump>
</cat> 
""")

#Close all
con.close()
f.close()
l.close()

print '   Directory query done:  ',time.localtime()[0:6]
print '   Number of files:       ',len(flist)
print '   Numberof directories:  ',len(dirs)
print '   Output file:           ',filen
if not pat: print "      All entries written in the file, even ADMIN/CONFIG files" 

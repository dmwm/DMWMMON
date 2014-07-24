#! /usr/bin/python
#Script for list files recursively in DPM
#author: sartiran@llr.in2p3.fr

import sys,os, subprocess
import datetime, time
import MySQLdb

usage= ''

helpmsg= """
Script for getting a a filelist in xml format in dpm

Usage: dpmdump.py [-dbcfg FILE] [-rootdir <DIR>] [-dirlist <COMMA SEPARATED DIRLIST>] [-delay <SECS>] [-out <FILE>] [-only_csum] [-nocsum_file <FILE>] [-help]

OPTIONS AND AGRUMENTS

-dbcfg   <FILE>      : configuration file for db access with the line <user>/<password>@<host>. Defaults are: /opt/lcg/etc/DPMCONFIG and /opt/lcg/etc/NSCONFIG

-rootdir <DIR>       : base directory from which start the list of files. Default value is '/dpm'
                       WARNING: you should not put final '/'.

-dirlist <LIST>      : comma separated list of subdirectory to scan. Default is '/' (i.e. all the root directory).

-out     <FILE>      : output file. Default is 'dump.xml'.

-help                : print this help

"""

debug_flag=False

def debug_msg(msg):
    if(debug_flag):
        print msg

def sql_query(conn,sql):
    cursor=conn.cursor()
    cursor.execute(sql)
    return cursor.fetchall()

def get_files(conn,dirid):
    sql="select fileid,name,filesize,ctime,csumtype,csumvalue,mtime,atime from Cns_file_metadata where parent_fileid=%s and filemode>30000" % dirid
    return sql_query(conn,sql)

def get_dirs(conn,current):
    ret=[]
    sql="select fileid,name from Cns_file_metadata where parent_fileid=%s and filemode<30000" % current['id']
    for row in sql_query(conn,sql):
        ret.append({'name': current['name']+row[1]+'/','id' : row[0]})
    return ret

def get_id(directory):
    proc=subprocess.Popen("/usr/bin/dpns-ls -id %s|awk '{print $1}'"%directory,stdout=subprocess.PIPE,shell=True)
    (output,error)=proc.communicate()
    p_status = proc.wait()
    return output

def print_files(fhandle,conn,current):
    for row in get_files(conn,current['id']):
        fileid=str(row[0])
        name=current['name']+str(row[1])
        size=str(row[2])
        ctime=int(row[3])
        csum=str(row[4])+':'+str(row[5])
        mtime=str(row[6])
        atime=str(row[7])

        if fileid=='':
            continue


        content="<entry name=" + '"' + name + '"' + "><size>" + size + "</size><ctime>" + str(ctime) +"</ctime><atime>"+str(atime)+"</atime><mtime>"+str(mtime)+"</mtime><checksum>"+csum+"</checksum></entry>"+"\n"
        fhandle.write(content)
    return

def scan_directory(conn,directory,outfile):
    fhandle=open(outfile,'a')

    dbhandle=MySQLdb.connect(host=conn['host'],user=conn['user'],passwd=conn['pwd'],db=conn['db'])

    directories=[{'name':directory,'id':get_id(directory)}]

    while(len(directories)>0):
        current=directories.pop()
        print_files(fhandle,dbhandle,current)
        directories.extend(get_dirs(dbhandle,current))


    fhandle.close()
    dbhandle.close()

def print_header(outfile):
    fhandle=open(outfile,'w')
    curtime=datetime.datetime.isoformat(datetime.datetime.now())
    header="<?xml version="+'"'+"1.0"+'"'+" encoding="+'"'+"iso-8859-1"+'"'+"?>"
    header=header+"<dump recorded=" + '"' + curtime + '"' + "><for>vo:cms</for>"+"\n"+"<entry-set>"+"\n"
    fhandle.write(header)
    fhandle.close()

def print_footer(outfile):
    fhandle=open(outfile,'a')
    fhandle.write("</entry-set></dump>\n")
    fhandle.close()

def getdb_params(cfgfile):
    conn={}
    f=open(cfgfile,'r')
    dpmconfstr=f.readline()
    conn['user']=dpmconfstr.split('/')[0]
    conn['pwd']=dpmconfstr.split('/')[1].split('@')[0]
    conn['host']=dpmconfstr.split('/')[1].split('@')[1].split('\n')[0]
    conn['db']='cns_db'
    f.close()
    return conn



rootdir='/dpm'
outfile="dump.xml"
startdate=time.time()
dirlist=['/']
cfgfile=''

i=1
while(i<len(sys.argv)):
    if(sys.argv[i]=='-rootdir'):
        rootdir=sys.argv[i+1]
        i=i+2
    elif(sys.argv[i]=='-dbcfg'):
        cfgfile=sys.argv[i+1]
        i=i+2
    elif(sys.argv[i]=='-dirlist'):
        dirlist=sys.argv[i+1].split(',')
        i=i+2
    elif(sys.argv[i]=='-delay'):
        startdate=startdate - int(sys.argv[i+1])
        i=i+2
    elif(sys.argv[i]=='-out'):
        outfile=sys.argv[i+1]
        i=i+2
    elif(sys.argv[i]=='-nocsum_file'):
        nocsum_file=sys.argv[i+1]
        i=i+2
    elif(sys.argv[i]=='-help'):
        print  helpmsg
        sys.exit(0)
        i=i+1
    else:
        print 'Unrecognized option'
        print usage
        sys.exit(1)



if(cfgfile == ''):
    if os.path.exists('/usr/etc/DPMCONFIG'):
        cfgfile='/usr/etc/DPMCONFIG'
    else:
        cfgfile='/usr/etc/NSCONFIG'


conn=getdb_params(cfgfile)
print_header(outfile)

for item in dirlist:
    directory=rootdir+item
    scan_directory(conn,directory,outfile)

print_footer(outfile)


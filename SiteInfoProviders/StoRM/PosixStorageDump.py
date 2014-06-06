#!/usr/bin/python

'''
Posix StorageDump v1.5
Multiprocces
Support for adler32, md5 and sha256 hash.
Silent mode
Python > 2.5
author: Iban Cabrillo
'''

import os
import sys
import glob
import time
import hashlib
import datetime
import argparse
import fileinput
import subprocess
from multiprocessing import Pool

def hashfile(file, hash, blocksize=65536):
    '''
    Calc the md5 or sha256 (pass in hash value) chksum value for a giving file
    '''
    if hash == 'md5':
        hasher = hashlib.md5()
    elif hash == 'sha256':
        hasher = hashlib.sha256()

    with open(file, 'rb') as f:
        for block in iter(lambda: f.read(blocksize), ""):
            hasher.update(block)
    return hasher.hexdigest()


def hashadler32(file, blocksize=65536):
    '''
    Calc the adler32 chksum value for a giving file
    '''
    from zlib import adler32

    val = 1
    fp=open(file)
    while True:
        data = fp.read(blocksize)
        if not data:
            break
        val = adler32(data, val)
        if val < 0:
            val += 2**32
    return hex(val)[2:10].zfill(8).lower()


def get_local_cksum(surl):
    '''
    Get the cksum store at local file level. If the file has no cksum value we should calc it.
    '''
    if hash == 'adler32':
        name = 'user.storm.checksum.adler32'
    else:
        name = 'user.checksum.%s' % hash

    output, error = subprocess.Popen(['getfattr', '--only-values', '--absolute-names', '-n', name, surl], stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    #print 'output:[',output,']'

    if len(output) == 0:
        if hash == 'adler32':
            value = hashadler32(surl).rstrip('\n').lstrip('0')
            #Makes name avaible to be used under StoRM
        else:
            value = hashfile(surl, hash).rstrip('\n')

        if verb:
            print "No checksum value found for file %s. Processing..." % surl.replace(localpath,'')
            #Calc de adler32 value
        setcksum, error = subprocess.Popen(['setfattr', '-n', name, '-v', value, surl], stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        return value
    else:
        return output.rstrip('\n')


def get_local_timestamp(surl):
    '''
    Get the mtime store for local file as extra attribute. If the file has no this
    value stored we calc it.
    '''

    #Look for the adler32 value
    output, error = subprocess.Popen(['getfattr', '--only-values', '--absolute-names', '-n', 'user.timestamp', surl], stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    #print 'output:[',output,']'
    #print 'error:[',error,']'

    if len(output) == 0:

        if verb:
            print "No timestamp value found for file %s. Processing..." % surl.replace(localpath,'')

        #Calc de timestamp value
        timestamp = str(os.stat(surl).st_ctime).rstrip('\n')

        # Set the timstamp value for the file.
        settimestamp, error = subprocess.Popen(['setfattr', '-n', 'user.timestamp', '-v', timestamp, surl], stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

        return timestamp

    else:

        return output.rstrip('\n')


def get_local_size(surl):
    '''
    Get the size store for local file as extra attribute. If the file has no this
    value stored we calc it.
    '''

    #Look for the adler32 value
    output, error = subprocess.Popen(['getfattr', '--only-values', '--absolute-names', '-n', 'user.size', surl], stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    #print 'output:[',output,']'
    #print 'error:[',error,']'

    if len(output) == 0:

        if verb:
            print "No size value found as extra attribute for file %s. Processing..." % surl.replace(localpath,'')

        #Calc de timestamp value
        size = str(os.stat(surl).st_size).rstrip('\n')

        # Set the timstamp value for the file.
        setsize, error = subprocess.Popen(['setfattr', '-n', 'user.size', '-v', size, surl], stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        return size

    else:

        return output.rstrip('\n')

def print_storage_dump(lfn, size, ctime, cksum):
    '''
    Create a file with keys: lfn, size, timestamp, cksum
    '''

    f = open(outfile, 'a')

    f.write(lfn)
    f.write('|')
    f.write(size)
    f.write('|')
    f.write(ctime)
    f.write('|')
    f.write(cksum)
    f.write('\n')


def threats(surl):
    '''
    Print the correct format for txt file.
    for user's files the cksum value is omited.
    '''

    if hash == 'adler32' or hash == 'md5' or hash == 'sha256':
        print_storage_dump(surl.replace(localpath,''), get_local_size(surl), get_local_timestamp(surl), get_local_cksum(surl))
    else:
        print_storage_dump(surl.replace(localpath,''), get_local_size(surl), get_local_timestamp(surl), 'N/A')

def merge_files():

    file_list = glob.glob('/tmp/DumpFile*%s*.txt' % datetime.date.today())

    #print file_list
    with open('DumpFile.%s.txt' % datetime.date.today(), 'w') as file:
        input_lines = fileinput.input(file_list)
        file.writelines(input_lines)

    print "writing output file as DumpFile.%s.txt" % datetime.date.today()

def getopts():
    '''
    Get the command line arguments
    '''

    parser = argparse.ArgumentParser(description='Process inline variables')

    parser.add_argument('-a', '--all', action='store_false', dest='dumpall', help='Storage Dump all the FS under path (overwrite -d value)')
    parser.add_argument('-v', '--verb', action='store_true', dest='verb', help='Default silent mode. overwrite -v versose')
    parser.add_argument('-m', '--1month', action='store_true', dest='dumpolder1', help='Storage Dump files older them 1 Month  under path (overwrite -d value)')
    parser.add_argument('-c', '--cksum', dest='cksum', help='Look chksum value if it doesn\'t exist then calc it (values adler32 (default), md5, sha256)')
    parser.add_argument('-d', '--days', dest='days', default='7', help='Dump files at FS newer than \"days\" (default value 7)')
    parser.add_argument('-n', '--ncores', dest='ncores', default='4', help='Number of cores to be used (default 4)')
    parser.add_argument('-p', '--paths', dest='paths', nargs='+', required=True, help='Path to look for files, Mandatory')

    return parser.parse_args()

if __name__ == '__main__':


###########################Globals################################
##################################################################

    try:
        myargs = getopts()
        all = myargs.dumpall
        month = myargs.dumpolder1
        hash = myargs.cksum
        days = myargs.days
        paths = myargs.paths
        ncores = myargs.ncores
        verb = myargs.verb
        #print all, verb, month, hash, days, ncores, paths

    except KeyError:
        print "missing some mandatory parameters, please run <StorageDumps.py -h >"
        sys.exit()

    try:
        for path in paths:
            outfile = '/tmp/DumpFile.%s.%s.txt' % (filter(None,path.split('/'))[-1],datetime.date.today())
            localpath = path[:path.rfind("/store")]
            if not os.path.isfile(outfile):
                for tupla in os.walk(path, followlinks=True):
                    if tupla[2]:
                        po = Pool(processes=int(ncores))
                    #try:
                        if all:
                            t = datetime.date(2000,01,01)
                            if time.mktime(t.timetuple()) <= os.path.getctime(tupla[0]):
                                #for file in tupla[2]:
                                lista = [ tupla[0]+'/'+f for f in tupla[2] ]
                                result = po.map_async(threats, lista)
                                result.wait()

                        elif month:
                            t = datetime.date.today() - datetime.timedelta(days=30)
                            if time.mktime(t.timetuple()) >= os.path.getctime(tupla[0]):
                                #for file in tupla[2]:
                                lista = [ tupla[0]+'/'+f for f in tupla[2] ]
                                result = po.map_async(threats, lista)
                                result.wait()

                        else:
                            t = datetime.date.today() - datetime.timedelta(days=int(days))
                            #print tupla[0], os.path.getctime(tupla[0]), time.mktime(t.timetuple())
                            if time.mktime(t.timetuple()) <= os.path.getctime(tupla[0]):
		                    #for file in tupla[2]:
                                lista = [ tupla[0]+'/'+f for f in tupla[2] ]
                                result = po.map_async(threats, lista)
                                result.wait()
	              #except OSError:
                      #print "Path no accesible %s" % surl
	                  #pass
                        po.close()
                        po.join()
        merge_files()

    except IndexError:
        print "Maybe a empty line at some file"
        pass

#!/bin/sh

#Technology:          
# hadoop/bestman

#Reference Site:     
# T2_US_Wisconsin (Carl Vuosalo)
 

begintime=`date +%s`
OUTPUTDIR=/scratch/SpaceMon
SCRIPTDIR=/usr/local/bin/spaceMon
mkdir -p $OUTPUTDIR
find $OUTPUTDIR -mtime +15 -name '*stor*.log' -exec rm {} \;
OUTFILE="$OUTPUTDIR/storage-dump-wisc.$begintime.txt"
TMPFILE=$OUTPUTDIR/tmpdump.lst
touch $OUTFILE
echo "BEGIN TIME $begintime `date`" > $OUTFILE.log
(
	export TZ=UTC
	hadoop fs -ls -R /store > $TMPFILE
	grep -v '^d' $TMPFILE | python $SCRIPTDIR/procfilelist.py >> $OUTFILE
)
rm $TMPFILE

su cmsprod -c "/cvmfs/cms.cern.ch/spacemon-client/slc6_amd64_gcc493/cms/spacemon-client/1.0.2/DMWMMON/SpaceMon/Utilities/spacemon --dump $OUTFILE --node T2_US_Wisconsin --upload" >> $OUTFILE.log 2>&1 
rm $OUTFILE
echo "END TIME `date +%s` `date`" >> $OUTFILE.log 

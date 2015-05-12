#!/bin/sh

begintime=`date +%s`
OUTFILE="storage_dump_vandyT2.$begintime.txt"
touch $OUTFILE
echo "BEGIN TIME $begintime `date`" > $OUTFILE.log

setpkgs -a lio
lio_getattr -rd 1000 -new_obj "%s|" -attr_fmt "%.0s%s" -attr_sep "|" -al system.exnode.size,system.create,user.gridftp.adler32 '@:/cms/store/hidata/HIRun2013/PAHighPt/RECO/HighPtPA-PromptSkim-v1/*' | sed -e 's/(null)//g' >> $OUTFILE

echo "END TIME `date +%s` `date`" >> $OUTFILE.log 

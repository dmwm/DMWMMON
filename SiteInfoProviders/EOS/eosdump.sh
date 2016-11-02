#!/bin/bash

now=`date +%Y-%m-%d-%H-%M-%S`

# keep the slash at the end, otherwise the regexp will fail
eosDir="/eos/cms/store/"

# will automatically pick the CMS version
eosCommand="/afs/cern.ch/project/eos/installation/cms/bin/eos.select"

findFiles="$eosCommand find -f --ctime --mtime --checksum --size"
findDirs="$eosCommand find -d --maxdepth 1"

output_dir="/afs/cern.ch/work/p/phedex/public/eos_dump"

#
# normally we only would call an eos find on /eos/cms/store,
# but this finds too many files, blows up in memory and
# eventually segfaults
#
# to work around this, call an eos find on each subdirectory,
# for some even subdirectories two level down and for one
# even three levels down
#
for subDir in `$findDirs $eosDir | awk '{print $1}' | sed 's|root://eoscms.cern.ch/||'`
do
    # for these directories to second level splitting
    key="^$eosDir\b(unmerged|lhe|group|backfill|user|express|cmst3|mc|data|caf|t0streamer)\b/"
    if [[ "$subDir" =~ $key ]]; then
	for subSubDir in `$findDirs $subDir | awk '{print $1}'| sed 's|root://eoscms.cern.ch/||'`
        do
	    # for t0streamer/Data do third level splitting
	    key="^$eosDir\b(t0streamer)\b/\b(Data)\b/"
	    if [[ "$subSubDir" =~ $key ]]; then
		for subSubSubDir in `$findDirs $subSubDir | awk '{print $1}'| sed 's|root://eoscms.cern.ch/||'`
		do
		    key="^$subSubDir[^ ]+/"
		    if [[ $subSubSubDir =~ $key ]]; then
			$findFiles $subSubSubDir
		    fi
		done
	    else
		key="^$subDir[^ ]+/"
		if [[ $subSubDir =~ $key ]]; then
		    $findFiles $subSubDir
		fi
	    fi
	done
    else
	key="^$eosDir[^ ]+/"
	if [[ $subDir =~ $key ]]; then
            $findFiles $subDir
	fi
    fi
done | gzip -9 > $output_dir/eos_files_$now.txt.gz;

#
# eos file dump is written to a dated file, only at
# the end (when there was no erros) will the generic
# link be updated
#
# only keep the last two days eos dumps on disk
#
if [ $? -ne 0 ]; then
    rm $outputDir/eos_files_$now.txt.gz
else
    (cd $output_dir ; ln -sfn eos_files_$now.txt.gz eos_files.txt.gz)
    find $output_dir -maxdepth 1 -name "eos_files_*.txt.gz" -mtime +2 -exec rm {} \;
fi

# Test production environment for SpaceMon independent from PHEDEX
# Code now resides in DMWMMON github repo. 

unset PERL5LIB
export DMWMMON_ROOT=/storage/local/data1/home/natasha/work/SPACEMON/TESTS/GIT_REPO_MOVE_1/dmwm
export PERL5LIB=$DMWMMON_ROOT:$PERL5LIB
export PATH=$DMWMMON_ROOT/DMWMMON/SpaceMon/Utilities:$PATH
#grid-proxy-init -bits 1024
export myproxy=`grid-proxy-info -path`
export EDITOR=nano # for git commits
cd $DMWMMON_ROOT/DMWMMON
git status
echo -e "run:\n emacs " `git status |grep  modified: | awk '{print $NF}'` "&"

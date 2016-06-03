# Simple Makefile to create environment setup script from template 
# 
# Run 'make'  or 'make install' to update the setup script whenever 
# the template is changed
#

.PHONY: install

sourcedir = $(shell pwd)
template = Utilities/setup.template

install: Utilities/setup.sh

Utilities/setup.sh: $(template) Makefile
	cat $(template) | sed s'|%sourcedir%|$(sourcedir)|' > Utilities/setup.sh

#!/bin/bash

PYTHON=/opt/python/3.6/bin/python
if [ ! -e $PYTHON ]; then
    PYTHON=`which python3`
fi
echo $PYTHON

if [ -e ./install_test ]; then
    rm -fr install_test
fi

$PYTHON -m venv install_test
source install_test/bin/activate;
find handoff -name '__pycache__' | xargs rm -fr;
python setup.py clean --all;
rm -fr dist;
rm -fr build;
rm -fr handoff.egg-info;
python setup.py install;

SITE_PKG_DIR="./install_test/lib/python3.6/site-packages"
PKG_DIR=`ls $SITE_PKG_DIR | grep handoff`

# tree $SITE_PKG_DIR/$PKG_DIR/handoff
DIFF=`diff --exclude=__pycache__ -r $SITE_PKG_DIR/$PKG_DIR/handoff ./handoff`
if [ -z "$DIFF" ]
then 
    echo "All file are included in the package.";
else
    echo $DIFF
    echo "Check MANIFEST.in"
    exit 1;
fi

# Note: Don't insert spaces in the next line
handoff&>install_test/msg
if [ -z `cat install_test/msg | grep "usage: handoff"` ]; then
    cat install_test/msg
    echo "handoff is not properly installed"
    exit 1;
fi

deactivate
echo "Install test finished successfully"

#!/bin/bash

# create docs
cd enviro/compute_docs/
make html
cd ../..

# empty out because mv cannot overwrite non empty sub-folders
rm -rf out/*

# move to /out dir
mv -f enviro/compute_docs/_build/html/* out

# delete unnecessary stuff in _build folder
#rm -rf enviro/compute_docs/_build/

# create .nojekyll-file
touch out/.nojekyll

# delete .buildinfo
#rm -rf out/.buildinfo

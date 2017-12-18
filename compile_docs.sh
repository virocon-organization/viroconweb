#!/bin/bash

# create docs
cd enviro/compute_docs/
make html
cd ../..

# move to /out dir
mv enviro/compute_docs/_build/html/ ./out

# delete unnecessary stuff in _build folder
rm -rf enviro/compute_docs/_build/

# create .nojekyll-file
touch out/.nojekyll

# delete .buildinfo
rm -rf out/.buildinfo

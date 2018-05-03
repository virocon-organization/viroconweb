# ViroCon

[![Build Status](https://travis-ci.org/ahaselsteiner/viroconweb.svg?branch=master)](https://travis-ci.org/ahaselsteiner/viroconweb)
[![Coverage Status](https://coveralls.io/repos/github/ahaselsteiner/viroconweb/badge.svg?branch=master&service=github)](https://coveralls.io/github/ahaselsteiner/virocon?branch=master)

ViroCon is an easy-to-use web-based software to compute environmental contours.

## About

This is the code of the web application
[ViroCon](https://serene-sierra-98066.herokuapp.com).

**ViroCon is currently under development. There is no stable version yet. At
this moment the version hosted at Heroku might be different from the repo's
Master branch.**

ViroCon helps you to design marine structures, which need to withstand load
combinations based on wave, wind and current. It lets you define extreme
environmental conditions with a given return period using the environmental
contour method.

The following methods are available:
* Fitting a probabilistic model to measurement data using maximum likelihood
estimation
* Defining a probabilistic model with the conditonal modeling approach (CMA)
* Computing an environmental contour using either the
  * inverse first order reliability method (IFORM) or the
  * highest density contour (HDC) method

ViroCon is written in Python 3.6.4 and uses the web framework Django 1.11.11.
 The software is seperated in two main packages, viroconweb and viroconcom.
 This is the repository of viroconcom, which is the web application.
 The second package, viroconcom, handles the statistical computations and
 has its own [repository](https://github.com/ahaselsteiner/viroconcom).

## How to use ViroCon

If you want to compute environmental contours with a simple web-based user
interface, go to our hosted application at
https://serene-sierra-98066.herokuapp.com

Here we will input a GIF that shows how a users interacts with the app.

If you want to compute environmental contours with Python, use the package we
built for the needed statistical computations,
[viroconcom](https://github.com/ahaselsteiner/viroconcom).

Here we will input a GIF that shows how a user uses pip install to install
viroconcom and then computes a environmental contour.


## Documentation
**Code** The code's documentation can be found
[here](https://ahaselsteiner.github.io/viroconweb/). Currently, this is the
documentation of the 'viroconcom' package, we will update it to become ViroCon's
documentation.

**Methods** The app has a help page, which describes the implemented methods in
detail. It can be found
[here](https://serene-sierra-98066.herokuapp.com/info/help).

**Paper** We are currently writing an academic paper describing ViroCon. We will
provide the a linkt to it here.

## Contributing
There are various ways you can contribute.

**Issue** If you spotted a bug, have an idea for an improvement or a new
 feature please open a issue. You can either leave it to us to work on the
 issue or do it yourself.

**Fork** If you want to work on an issue yourself please fork the repository,
then develop the feature in your copy of the repository and finally
file a pull request to merge it into our repository.

**Run app** To run a copy of ViroCon locally use the following
commands:
```
git clone https://github.com/ahaselsteiner/viroconweb
pip install -r requirements.txt
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
Then you should reach a local version of ViroCon at http://localhost:8000

**Conventions** We follow the python styleguide PEP8:
https://www.python.org/dev/peps/pep-0008

## License
This software is licensed under the MIT license. For more information, read the
file [LICENSE](https://github.com/ahaselsteiner/viroconweb/blob/master/LICENSE).
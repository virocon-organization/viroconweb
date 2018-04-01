# ViroCon

[![Build Status](https://travis-ci.org/ahaselsteiner/virocon.svg?branch=master)](https://travis-ci.org/ahaselsteiner/virocon)
[![Coverage Status](https://coveralls.io/repos/github/ahaselsteiner/virocon/badge.svg?branch=master&service=github)](https://coveralls.io/github/ahaselsteiner/virocon?branch=master)

ViroCon is an easy-to-use web-based software to compute environmental contours.

## About

This is the code of the web application
[ViroCon](https://serene-sierra-98066.herokuapp.com).

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

ViroCon is written in Python 3.6.4, Django 1.11.11 and uses our package
[viroconcom](https://github.com/ahaselsteiner/viroconcom) for 
statistical computations.

## How to use ViroCon

If you want to compute environmental contours with a simple web-based user 
interface, go to our hosted application at
https://serene-sierra-98066.herokuapp.com

Here we will input a GIF that shows how a users interacts with the app here.

If you want to compute environmental contours with Python, use the package we 
built for the needed statistical computations, 
[viroconcom](https://github.com/ahaselsteiner/viroconcom).

Here we will input a GIF that shows how a user uses pip install to install 
viroconcom and then computes a environmental contour.


## Documentation
**Code** The code's documentation can be found 
[here](https://ahaselsteiner.github.io/virocon/).

**Methods** The app has a help page, which describes the implemented methods in 
detail. It can be found [here](https://serene-sierra-98066.herokuapp.com/help).

**Paper** We are currently writing an academic paper describing ViroCon. We will
provide the a linkt to it here. 

## Contributing
There are various ways you can contribute.

**Issue** If you spotted a bug or have an idea for an improvement please 
open a issue.

**Fork** If you want to fix a bug yourself or want to develop a new feature 
please fork the repository, then develop the feature in your copy and finally 
file a pull request.

**Run app** To run a copy of ViroCon locally use the following 
commands:
```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
Then you should reach a local version of your app at http://localhost:8000

## License
This software is licensed under the MIT license. For more information, read the 
file [LICENSE](https://github.com/ahaselsteiner/virocon/blob/master/LICENSE).
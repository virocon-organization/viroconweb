"""
Settings for the contour app.

These constants are used in different modules of contour package.
"""

PATH_MEDIA = 'contour/media/'
PATH_USER_GENERATED = 'user_generated/'
PATH_MEASUREMENT = 'measurement/'
PATH_PROB_MODEL = 'prob_model/'
PATH_CONTOUR = 'contour/'
LATEX_REPORT_NAME = 'latex_report.pdf'
EEDC_FILE_NAME = 'design_conditions.csv'

# Maximum computing time in seconds for performing a fit, calculating a
# a contour or saving the contour to the data bsase. The time limit is only
# used in production. Heroku would throw a its own timeout error after 30 s.
MAX_COMPUTING_TIME_PRODUCTION = 15.0

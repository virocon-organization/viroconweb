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

# Maximum computing time in seconds for performing a fit or calculating a
# a contour. The time limit is only used in production.
MAX_COMPUTING_TIME_PRODUCTION = 2.0

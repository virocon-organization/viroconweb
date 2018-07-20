"""
Settings for the contour app.

These constants are used in different modules of the contour package.
"""
from viroconweb.settings import RUN_MODE

PATH_MEDIA = 'contour/media/'
PATH_USER_GENERATED = 'user_generated/'
PATH_MEASUREMENT = 'measurement/'
PATH_PROB_MODEL = 'prob_model/'
PATH_CONTOUR = 'contour/'
LATEX_REPORT_NAME = 'latex_report.pdf'
EEDC_FILE_NAME = 'design_conditions.csv'
VIROCON_CITATION = 'A.F. Haselsteiner, J. Lehmkuhl, T. Pape, K.-L. Windmeier, ' \
                   'K.-D. Thoben (2018): ViroCon: A software to compute ' \
                   'multivariate extremes using the environmental contour ' \
                   'method. Manuscript in preparation.'

# Set a maximum computing time in seconds for performing a fit, calculating a
# a contour or saving the contour to the data base. The time limit is important
# for production. Heroku would throw its own timeout error after 30 s.
if RUN_MODE == 'production':
    MAX_COMPUTING_TIME = 15.0
else:
    MAX_COMPUTING_TIME = 120.0

# Saving all coordinates to the database is slow since a lot of operations
# might be necessary. Consequenetly, this can be turned off.
DO_SAVE_CONTOUR_COORDINATES_IN_DB = False

# Maximum file size in MiB of a measurement file that is allowed to be uploaded.
MAX_FILE_SIZE_M_IN_MIB = 100

NR_LINES_HEADER = 2
MAX_LENGTH_FILE_NAME = 120

import os
import numpy as np
from django.core.exceptions import ValidationError


def validate_file_extension(value):
    """
    The function validates the attached file suffix. The suffix have to be '.csv'
    :param value: the uploaded measure_file
    :return: 
    """
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.csv']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')


def validate_contour_coordinates(contour_coordinates):
    """
    Valides contour coordinates.

    They are not allowed to contain NaN or inf.

    Parameters
    ----------
    contour_coordinates : n-dimensional matrix
        The coordinates of the environmental contour.
        The format is defined by compute_interface.iform() and
        compute_interface.hdc().

    Raises
    -------
    ValidationError,
        If the contour coordinates contain unsupported values like
        NaN or inf.
    """
    for i in range(len(contour_coordinates)): # Loop over  multiple contour paths
        for j in range(len(contour_coordinates[i])): # Loop over the EEDC vectors
            for k in range(len(contour_coordinates[i][j])): # Loop over scalars
                scalar = contour_coordinates[i][j][k]
                if np.isnan(scalar):
                    raise ValidationError('The contour coordinates contain '
                                          'values, which are set to NaN.')
                if np.isinf(scalar):
                    print('Raising ValidationError because of inf.')
                    raise ValidationError('The contour coordinates contain '
                                          'values, which are set to inf '
                                          '(Infinity).')

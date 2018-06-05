"""
Validators to check e.g. uploaded data or calculated contours.
"""
import re

import numpy as np
from django.core.exceptions import ValidationError

from .settings import MAX_FILE_SIZE_M_IN_MIB, MAX_LENGTH_FILE_NAME


def validate_contour_coordinates(contour_coordinates):
    """
    Validates contour coordinates.

    They are not allowed to contain NaN or inf.

    Parameters
    ----------
    contour_coordinates : list of list of numpy.ndarray,
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

def validate_csv_upload(value):
    """

    Parameters
    ----------
    value : django.core.files.File,
        The file that the user wants to upload.

    Raises
    ------
    ValidationError,
        If the file is too large ot does not have the right format.
    """

    # Validate the file name's length.
    if len(value.name) > MAX_LENGTH_FILE_NAME:
        raise ValidationError(
            'File name too long. The size should not exceed ' +
            str(MAX_LENGTH_FILE_NAME) + ' characters, but was ' +
            str(len(value.name)) + ' characters.')

    # Validate the file size.
    limit = MAX_FILE_SIZE_M_IN_MIB * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed ' +
                              str(MAX_FILE_SIZE_M_IN_MIB) + ' MiB.')
    elif value.size == 0:
        raise ValidationError("File is empty.")

    # Validate if it is a text file.
    try:
        input_str = value.read().decode("utf-8")
    except UnicodeDecodeError:
        raise ValidationError("Only plain text files are allowed.")


    input_lines = input_str.splitlines()
    header_line_1 = input_lines[0]
    header_line_2 = input_lines[1]
    body = "\n".join(input_lines[2:]) + "\n"

    # Validate the header and start with the first line, which should contain
    # the variable names.
    header_parts = header_line_1.split(";")
    if len(header_parts) == 0:
        raise ValidationError("Empty header.", code="invalid")
    var_num = int(len(header_parts))

    h_pattern_str = r"^(?:[^;]{1,50};){1,9}[^;]{1,50}$"
    h_pattern = re.compile(h_pattern_str, re.ASCII)

    header_is_ok = False
    result = h_pattern.match(header_line_1)
    if result:
        header_is_ok = (result.end()-result.start() == len(header_line_1))

    if not header_is_ok:
        raise ValidationError("Error in header's first line.", code="invalid")

    # Valide the second line, which should contain the variable symbols.
    header_parts = header_line_2.split(";")
    if int(len(header_parts)) != var_num:
        raise ValidationError("Error in the header's second line. "
                              "A variable symbol for each variable must "
                              "be provided.", code="invalid")

    h_pattern_str = r"^(?:[^,\s]{1,5};){1,9}[^;\s]{1,5}$"
    h_pattern = re.compile(h_pattern_str, re.ASCII)

    header_is_ok = False
    result = h_pattern.match(header_line_2)
    if result:
        header_is_ok = (result.end()-result.start() == len(header_line_2))

    if not header_is_ok:
        raise ValidationError("Error in header's second line.", code="invalid")

    # Validate the body.
    if len(body) == 0:
        raise ValidationError("Empty body.", code="invalid")

    b_pattern_str = (r"(?:(?:\s*\d+[\.,]?\d*\s*;){1," + str(var_num-1)
                     + r"}\s*\d+[\.,]?\d*\s*\n)+")
    b_pattern = re.compile(b_pattern_str, re.ASCII)

    body_is_ok = False
    result = b_pattern.match(body)
    if result:
        body_is_ok = result.end()-result.start() == len(body)
        if not body_is_ok:
            end_of_line = body.find("\n", result.end())
            start_of_line = body.rfind("\n", 0, result.end())
            if end_of_line == -1:
                end_of_line = len(body)
            if start_of_line == -1:
                start_of_line = 0
            error_line = body[start_of_line : end_of_line].strip()
            if len(error_line) > 50:
                error_line = error_line[0:50] + "..."
            raise ValidationError("Error in the following line: %(err_line)s",
                                  code="invalid",
                                  params={"err_line" : error_line})
    else:
        if not body_is_ok:
            raise ValidationError("Error in body.", code="invalid")
    value.seek(0)

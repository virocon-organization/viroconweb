import os
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

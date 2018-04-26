import re
from django.core.exceptions import ValidationError



def validate_csv_upload(value):

    #check file size
    limit = 100 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 100 MiB.')
    elif value.size == 0:
        raise ValidationError("File is empty.")

    #check if text file
    try:
        input_str = value.read().decode("utf-8")
    except UnicodeDecodeError:
        raise ValidationError("Only plain text files are allowed.")


    input_lines = input_str.splitlines()
    header = input_lines[0]
    body = "\n".join(input_lines[1:]) + "\n"

    #check header
    header_parts = header.split(";")
    if len(header_parts) == 0:
        raise ValidationError("Empty header.", code="invalid")
    if len(header_parts) % 2 != 0:
        raise ValidationError("Long name and symbol are needed "
                              "for each variable.", code="invalid")

    var_num = int(len(header_parts) / 2)

    h_pattern_str = r"^(?:[^;]{1,50};\s*[^,\s]{1,5}\s*;){1,9}" \
                    r"[^;]{1,50};\s*[^;\s]{1,5}$"
    h_pattern = re.compile(h_pattern_str, re.ASCII)

    header_is_ok = False
    result = h_pattern.match(header)
    if result:
        header_is_ok = (result.end()-result.start() == len(header))

    if not header_is_ok:
        raise ValidationError("Error in header.", code="invalid")

    #check body
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

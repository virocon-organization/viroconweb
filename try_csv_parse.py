
import os
import re

here = os.path.abspath(os.path.dirname(__file__))
testfile_path = os.path.join(here, r"tests/test_files/1yeardata_vanem2012pdf_withHeader.csv")

with open(testfile_path, "r") as tf:
    test_str = tf.read()

test_strs = test_str.splitlines()
header = test_strs[0]
body = "\n".join(test_strs[1:]) + "\n"

header_parts = header.split(";")
if len(header_parts) == 0:
    print("empty header")
if len(header_parts) % 2 != 0:
    print("long name and symbol needed for each variable")

var_num = int(len(header_parts) / 2)

h_pattern_str = r"^(?:[^;]{1,50};\s*[^,\s]{1,5}\s*;){1,9}" \
                r"[^;]{1,50};\s*[^;\s]{1,5}$"
h_pattern = re.compile(h_pattern_str, re.ASCII)
header_is_ok = False
result = h_pattern.match(header)
if result:
    header_is_ok = result.end()-result.start() == len(header)


b_pattern_str = (r"(?:(?:\s*\d+[\.,]?\d*\s*;){1," + str(var_num-1)
                 + r"}\s*\d+[\.,]?\d*\s*\n)+")

b_pattern = re.compile(b_pattern_str, re.ASCII)
body_is_ok = False
result = b_pattern.match(body)
if result:
    body_is_ok = result.end()-result.start() == len(body)
#    if not body_is_ok:
#        try:
#            end_of_line = body.index(beg=result.end())
#            start_of_line = body[0:result.end():-1].index()
#            result.end()
#        except ValueError:
#            print("body is not ok)



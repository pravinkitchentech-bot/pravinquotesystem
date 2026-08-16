import re

# Read files
with open('employee.html', 'r', encoding='utf-8', errors='ignore') as f:
    emp_lines = f.readlines()

with open('admin.html', 'r', encoding='utf-8', errors='ignore') as f:
    admin_lines = f.readlines()

# Extract Block 1 from employee.html (lines 1412 to 2594)
# Note: 1-indexed lines 1412 to 2594 correspond to 0-indexed indices 1411 to 2594
block1_code = "".join(emp_lines[1411:2594])

# Extract Block 2 from employee.html (lines 2840 to 3294)
# Note: 1-indexed lines 2840 to 3294 correspond to 0-indexed indices 2839 to 3294
block2_code = "".join(emp_lines[2839:3294])

# The text to insert:
merged_code = "\n" + block1_code + "\n" + block2_code + "\n"

# In admin.html:
# We want to replace from line 2018 (after '        };') to line 2540.
# Let's inspect admin.html line 2018 (0-indexed index 2017)
target_line = admin_lines[2017]
assert 'const ACCESSORY_LIST' in target_line, f"Unexpected content in admin.html line 2018: {target_line}"

# Let's verify line 2540 (0-indexed index 2539)
end_line = admin_lines[2539]
assert '};' in end_line, f"Unexpected content in admin.html line 2540: {end_line}"

# We will modify admin_lines:
# admin_lines[0:2017] -> keeps up to line 2017 (including 2017)
# But line 2018 (index 2017) has: '        }; const ACCESSORY_LIST = ['
# We want to change index 2017 to just '        };\n'
new_admin_lines = admin_lines[:2017]
new_admin_lines.append('        };\n')

# Append the merged_code
new_admin_lines.append(merged_code)

# Append everything after line 2540 (index 2540 onwards)
new_admin_lines.extend(admin_lines[2540:])

# Write to a test file first to check
with open('admin_test.html', 'w', encoding='utf-8') as f:
    f.writelines(new_admin_lines)

print("Merged admin_test.html written successfully!")

import re

# Read files
with open('employee.html', 'r', encoding='utf-8', errors='ignore') as f:
    emp_lines = f.readlines()

with open('admin.html', 'r', encoding='utf-8', errors='ignore') as f:
    admin_lines = f.readlines()

# Extract Block 1 from employee.html (lines 1412 to 2594)
block1_code = "".join(emp_lines[1411:2594])

# Extract Block 2 from employee.html (lines 2840 to 3294)
block2_code = "".join(emp_lines[2839:3294])

# The text to insert:
merged_code = "\n" + block1_code + "\n" + block2_code + "\n"

# Verify lines and prepare replacement in admin.html
# We want to replace from line 2018 (index 2017) to line 2540 (index 2539)
assert 'const ACCESSORY_LIST' in admin_lines[2017]
assert '};' in admin_lines[2539]

# Reassemble admin.html lines
new_admin_lines = admin_lines[:2017]
new_admin_lines.append('        };\n')
new_admin_lines.append(merged_code)
new_admin_lines.extend(admin_lines[2540:])

# Now, we also want to find and replace the getMaterialFormulaInfo function in the merged admin lines.
# Let's join them into a single string
admin_content = "".join(new_admin_lines)

# Find getMaterialFormulaInfo(itemId, opt, defaultType) { ... }
# Since there are inner braces, we need a brace-matching parser to replace it cleanly.
func_pattern = re.compile(r'function getMaterialFormulaInfo\s*\(\s*itemId\s*,\s*opt\s*,\s*defaultType\s*\)\s*\{')
match = func_pattern.search(admin_content)
if match:
    start_idx = match.start()
    open_brace_idx = match.end() - 1
    # Count braces to find the end of the function
    counter = 1
    idx = open_brace_idx + 1
    while idx < len(admin_content) and counter > 0:
        c = admin_content[idx]
        if c == '{':
            counter += 1
        elif c == '}':
            counter -= 1
        idx += 1
    
    if counter == 0:
        # Replacement code
        replacement_func = """function getMaterialFormulaInfo(itemId, opt, defaultType) {
            const label = typeof opt === 'string' ? opt : (opt && opt.label ? opt.label : '');
            let customFormulas = {};
            try {
                customFormulas = JSON.parse(localStorage.getItem('pks_material_formulas')) || {};
            } catch (e) { }

            const key = `${itemId}-${label}`;
            let formulaType = customFormulas[key] || customFormulas[label];

            if (!formulaType) {
                if (typeof opt === 'object') {
                    if (opt.formulaType) {
                        formulaType = opt.formulaType;
                    } else if (opt.fields) {
                        const f = opt.fields;
                        if (f.includes("L") && f.includes("W") && f.includes("H")) formulaType = "(L+W)*H";
                        else if (f.includes("L") && f.includes("H")) formulaType = "L*H";
                        else if (f.includes("L") && f.includes("W")) formulaType = "L*W";
                        else if (f.includes("SQFT")) formulaType = "SQFT";
                        else if (f.includes("QTY")) formulaType = "QTY";
                    }
                }
                if (!formulaType) {
                    if (defaultType) {
                        formulaType = defaultType;
                    } else {
                        formulaType = getStandardFormulaInfo(itemId, label).formulaType;
                    }
                }
            }

            if (formulaType === "L*H") {
                return { fields: ["L", "H"], formulaType: "L*H", note: "LxH/144" };
            }
            if (formulaType === "L*W") {
                return { fields: ["L", "W"], formulaType: "L*W", note: "LxW/144" };
            }
            if (formulaType === "SQFT") {
                return { fields: ["SQFT"], formulaType: "SQFT", note: "direct sq.ft" };
            }
            if (formulaType === "QTY") {
                return { fields: ["QTY"], formulaType: "QTY", note: "qty" };
            }
            return { fields: ["L", "W", "H"], formulaType: "(L+W)*H", note: "(L+W)×H/144" };
        }"""
        
        # Replace the function
        admin_content = admin_content[:start_idx] + replacement_func + admin_content[idx:]
        print("Replaced getMaterialFormulaInfo successfully!")
    else:
        print("Failed to find end of getMaterialFormulaInfo")
else:
    print("Failed to find getMaterialFormulaInfo definition")

# Write to admin.html (overwrite)
with open('admin.html', 'w', encoding='utf-8') as f:
    f.write(admin_content)

print("Updated admin.html successfully!")

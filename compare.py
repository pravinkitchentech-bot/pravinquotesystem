import re
import json

def get_content(fn):
    with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

admin = get_content('admin.html')
emp = get_content('employee.html')

def extract_js_object(content, var_name):
    # Find something like: const var_name = or let var_name =
    pattern = re.compile(r'(?:const|let|var)\s+' + re.escape(var_name) + r'\s*=')
    match = pattern.search(content)
    if not match:
        return None
    
    # Now scan forward from the end of the match to find the closing brace/bracket
    start_idx = match.end()
    
    # Skip whitespace to find the opening character
    idx = start_idx
    while idx < len(content) and content[idx].isspace():
        idx += 1
        
    if idx >= len(content):
        return None
        
    open_char = content[idx]
    if open_char == '[':
        close_char = ']'
    elif open_char == '{':
        close_char = '}'
    else:
        # Maybe it starts directly (e.g. string or number)
        # Scan until semicolon or newline
        end_idx = idx
        while end_idx < len(content) and content[end_idx] not in (';', '\n'):
            end_idx += 1
        return content[idx:end_idx].strip()
        
    # Brace/bracket counting
    counter = 1
    end_idx = idx + 1
    while end_idx < len(content) and counter > 0:
        c = content[end_idx]
        if c == open_char:
            counter += 1
        elif c == close_char:
            counter -= 1
        end_idx += 1
        
    if counter == 0:
        return content[idx:end_idx]
    return None

# Let's extract options lists from employee.html
# We want to find variables ending with _OPTS, _LIST, _PANEL, _OPTS_ONLY, etc.
# We can just extract standard names
vars_to_extract = [
    'STD_CABINET', 'BREAKFAST_OPEN_BOX_OPTS', 'WALL_PANEL', 'BREAKFAST_WALL_PANEL', 'BEAM', 'SPICE', 
    'LEDGE', 'PARTITION', 'MP_LAM_BOX_DOOR', 'MP_LAM_ACR_WPC_BOX_DOOR', 'BED_SIDE_BOX_OPTS', 
    'ECO_WALL_PANEL', 'ECO_CABINET_OPTS', 'ECO_BED_SIDE_BOX_OPTS', 'ECO_TV_BOTTOM_CABINET', 
    'MED_CABINET_OPTS', 'MED_BED_SIDE_BOX_OPTS', 'MED_CABINET_BOX_ONLY', 'MED_DRESSING_BOTTOM_OPTS', 
    'MP_LAM_ACR_WPC_BOX_DOOR_ONLY', 'KITCHEN_BOTTOM_OPTS', 'KITCHEN_LOFT_OPTS', 'ACCESSORY_OPTS',
    'FALSE_CELLING_OPTS', 'ENG_WOOD_PARTITION', 'MED_PARTITION', 'ACCESSORY_LIST',
    'ENG_WOOD_KING_BED', 'ENG_WOOD_QUEEN_BED', 'KING_BED_OPTS', 'QUEEN_BED_OPTS',
    'MED_KING_BED_OPTS', 'MED_QUEEN_BED_OPTS', 'MED_BED_OPTS', 'MED_BED_SIDE_BOX_OPTS'
]

emp_opts_map = {}
for var in vars_to_extract:
    obj_str = extract_js_object(emp, var)
    if obj_str:
        # Find all labels: label: "..." or label: '...'
        labels = re.findall(r'label:\s*[\'\"]([^\'\"]+)[\'\"]', obj_str)
        if not labels:
            # Maybe it is a simple array of strings: [ "Option1", "Option2" ]
            labels = re.findall(r'[\'\"]([^\'\"]+)[\'\"]', obj_str)
        if labels:
            emp_opts_map[var] = labels

# Extract options from admin.html as well
admin_opts_map = {}
for var in vars_to_extract:
    obj_str = extract_js_object(admin, var)
    if obj_str:
        labels = re.findall(r'label:\s*[\'\"]([^\'\"]+)[\'\"]', obj_str)
        if not labels:
            labels = re.findall(r'[\'\"]([^\'\"]+)[\'\"]', obj_str)
        if labels:
            admin_opts_map[var] = labels
    # Fallback to employee map if not defined in admin
    if var not in admin_opts_map or not admin_opts_map[var]:
        if var in emp_opts_map:
            admin_opts_map[var] = emp_opts_map[var]

# Parse ROOM_ITEMS, ROOM_ITEMS_MEDIUM, ROOM_ITEMS_ECONOMY
def parse_items_object(obj_str, opts_map):
    if not obj_str:
        return {}
    # Scan for keys: room: [ ... ]
    # We can match: key: [ and find the array
    results = {}
    pattern = re.compile(r'(\w+)\s*:\s*\[')
    matches = list(pattern.finditer(obj_str))
    for i, match in enumerate(matches):
        room_name = match.group(1)
        start_idx = match.end() - 1 # start at '['
        # Scan matching bracket
        counter = 1
        idx = start_idx + 1
        while idx < len(obj_str) and counter > 0:
            c = obj_str[idx]
            if c == '[':
                counter += 1
            elif c == ']':
                counter -= 1
            idx += 1
        if counter == 0:
            array_str = obj_str[start_idx:idx]
            # Parse items within this array: { id: X, name: "...", options: ... }
            # Let's match all curly braces in this array
            item_pattern = re.compile(r'\{([^{}]+)\}')
            items = []
            for item_match in item_pattern.finditer(array_str):
                item_body = item_match.group(1)
                id_match = re.search(r'id\s*:\s*(\d+)', item_body)
                name_match = re.search(r'name\s*:\s*[\'\"]([^\'\"]+)[\'\"]', item_body)
                options_match = re.search(r'options\s*:\s*([^,}\n]+)', item_body)
                if id_match and name_match:
                    iid = int(id_match.group(1))
                    iname = name_match.group(1)
                    opts_expr = options_match.group(1).strip() if options_match else '[]'
                    
                    # Parse opts_expr
                    if opts_expr.startswith('[') and opts_expr.endswith(']'):
                        opts = re.findall(r'[\'\"]([^\'\"]+)[\'\"]', opts_expr)
                    else:
                        opts = opts_map.get(opts_expr, opts_expr)
                    items.append({'id': iid, 'name': iname, 'options': opts})
            results[room_name] = items
    return results

print('Parsing Admin ROOM_ITEMS...')
admin_items_all = {
    'ROOM_ITEMS': parse_items_object(extract_js_object(admin, 'ROOM_ITEMS'), admin_opts_map),
    'ROOM_ITEMS_MEDIUM': parse_items_object(extract_js_object(admin, 'ROOM_ITEMS_MEDIUM'), admin_opts_map),
    'ROOM_ITEMS_ECONOMY': parse_items_object(extract_js_object(admin, 'ROOM_ITEMS_ECONOMY'), admin_opts_map)
}

print('Parsing Employee ROOM_ITEMS...')
emp_items_all = {
    'ROOM_ITEMS': parse_items_object(extract_js_object(emp, 'ROOM_ITEMS'), emp_opts_map),
    'ROOM_ITEMS_MEDIUM': parse_items_object(extract_js_object(emp, 'ROOM_ITEMS_MEDIUM'), emp_opts_map),
    'ROOM_ITEMS_ECONOMY': parse_items_object(extract_js_object(emp, 'ROOM_ITEMS_ECONOMY'), emp_opts_map)
}

# Compare
mismatches_found = False
for mode in ['ROOM_ITEMS', 'ROOM_ITEMS_MEDIUM', 'ROOM_ITEMS_ECONOMY']:
    print(f'\n=== MODE: {mode} ===')
    adm_mode = admin_items_all.get(mode, {})
    emp_mode = emp_items_all.get(mode, {})
    
    for room in sorted(set(adm_mode.keys()) | set(emp_mode.keys())):
        adm_items = {item['id']: item for item in adm_mode.get(room, [])}
        emp_items = {item['id']: item for item in emp_mode.get(room, [])}
        
        for iid in sorted(set(adm_items.keys()) | set(emp_items.keys())):
            a_item = adm_items.get(iid)
            e_item = emp_items.get(iid)
            if not a_item or not e_item:
                print(f'  Room {room}: Item {iid} mismatch: Admin={a_item is not None}, Emp={e_item is not None}')
                mismatches_found = True
                continue
            
            a_opts = a_item['options']
            e_opts = e_item['options']
            
            # Resolve if string
            if isinstance(a_opts, str):
                a_opts = admin_opts_map.get(a_opts, a_opts)
            if isinstance(e_opts, str):
                e_opts = emp_opts_map.get(e_opts, e_opts)
                
            if isinstance(a_opts, str): a_opts = [a_opts]
            if isinstance(e_opts, str): e_opts = [e_opts]
            
            a_set = set((o or '').strip() for o in a_opts if isinstance(o, str))
            e_set = set((o or '').strip() for o in e_opts if isinstance(o, str))
            
            if a_set != e_set:
                mismatches_found = True
                print(f'  Room {room}: Item {iid} ({a_item["name"]}) options mismatch:')
                print(f'    Admin only: {sorted(a_set - e_set)}')
                print(f'    Emp only  : {sorted(e_set - a_set)}')

if not mismatches_found:
    print('No mismatches found between ROOM_ITEMS, ROOM_ITEMS_MEDIUM, and ROOM_ITEMS_ECONOMY options!')

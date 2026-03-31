"""Debug script to trace diagram detection."""
import re

def is_ascii_diagram(code_text):
    """Check if code block is an ASCII diagram (vs OCL or other code)."""
    # OCL indicators
    ocl_keywords = ['context', 'pre:', 'post:', 'inv:', 'self.', 'implies', 'forAll', 'exists']
    text_lower = code_text.lower()

    for keyword in ocl_keywords:
        if keyword.lower() in text_lower:
            return False

    # Check for box-drawing characters (Unicode and ASCII)
    box_chars = '┌┐└┘│─┬┴├┤╔╗╚╝║═+|'
    has_box = any(c in code_text for c in box_chars)

    return has_box

def is_file_structure(code_text):
    """Check if code block is a file structure tree."""
    return '├──' in code_text or '└──' in code_text or '│' in code_text

def is_ui_mockup(code_text):
    """Check if code block is a UI mockup (ASCII art interface)."""
    plus_count = code_text.count('+')
    dash_count = code_text.count('-')
    pipe_count = code_text.count('|')

    if plus_count > 10 and (dash_count > 50 or pipe_count > 30):
        return True

    ui_elements = ['[Dashboard]', '[Help]', '[Back]', '[Save', '[Cancel]',
                   '[Start', '[Stop', '[Apply', '[View', 'Interface:',
                   'Purpose:', 'Inputs:', 'Outputs:']
    return any(elem in code_text for elem in ui_elements)

with open('ADD_Scarecrow_Drone.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find code blocks manually
lines = content.split('\n')
in_block = False
block_start = 0
blocks = []
current_block = []

for i, line in enumerate(lines):
    if line.strip().startswith('```'):
        if in_block:
            # End of block
            blocks.append((block_start, '\n'.join(current_block)))
            current_block = []
            in_block = False
        else:
            # Start of block
            block_start = i
            in_block = True
    elif in_block:
        current_block.append(line)

print(f"Found {len(blocks)} code blocks\n")

diagram_count = 0
file_struct_count = 0
ui_count = 0
ocl_count = 0
other_count = 0

for i, (line_num, code) in enumerate(blocks):
    is_diag = is_ascii_diagram(code)
    is_file = is_file_structure(code)
    is_ui = is_ui_mockup(code)

    if is_file:
        file_struct_count += 1
        block_type = "FILE_STRUCTURE"
    elif is_ui:
        ui_count += 1
        block_type = "UI_MOCKUP"
    elif is_diag:
        diagram_count += 1
        block_type = "ASCII_DIAGRAM"
    elif 'context' in code.lower() or 'pre:' in code.lower():
        ocl_count += 1
        block_type = "OCL"
    else:
        other_count += 1
        block_type = "OTHER"

    first_line = code.split('\n')[0][:40] if code else "(empty)"
    # Remove non-ASCII for printing
    first_line_ascii = ''.join(c if ord(c) < 128 else '?' for c in first_line)
    if i < 30:
        print(f"Block {i+1} @ line {line_num}: {block_type} - {first_line_ascii}")

print(f"\nSummary:")
print(f"  ASCII Diagrams: {diagram_count}")
print(f"  File Structures: {file_struct_count}")
print(f"  UI Mockups: {ui_count}")
print(f"  OCL Code: {ocl_count}")
print(f"  Other: {other_count}")

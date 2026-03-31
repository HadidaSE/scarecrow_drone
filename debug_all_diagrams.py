"""Debug what sections are being detected with full box chars."""
import re

with open('ADD_Scarecrow_Drone.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find h3 headings before code blocks
lines = content.split('\n')
in_block = False
current_h3 = ''
block_start = 0

diagrams_found = []

box_chars = '┌┐└┘│─┬┴├┤╔╗╚╝║═+|-'
ocl_keywords = ['context', 'pre:', 'post:', 'inv:', 'self.', 'implies', 'forAll', 'exists']

for i, line in enumerate(lines):
    if line.startswith('### '):
        current_h3 = line[4:].strip()
    if line.strip().startswith('```') and not in_block:
        in_block = True
        block_start = i
    elif line.strip().startswith('```') and in_block:
        in_block = False
        # Get block content
        block_content = '\n'.join(lines[block_start+1:i])

        # Check for box chars
        has_box = any(c in block_content for c in box_chars)

        # Check for OCL
        text_lower = block_content.lower()
        is_ocl = any(kw.lower() in text_lower for kw in ocl_keywords)

        if has_box and not is_ocl and current_h3:
            # Normalize the key like the script does
            key = current_h3.replace(' ', '_')
            key = re.sub(r'^[\d.]+\s*', '', key)
            diagrams_found.append((current_h3, key, block_start))

print(f"Diagrams found with their normalized keys ({len(diagrams_found)} total):")
for orig, key, line_num in diagrams_found:
    print(f"  Line {line_num}: {repr(orig)} -> {repr(key)}")

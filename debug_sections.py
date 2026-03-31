"""Debug what sections are being detected."""
import re

with open('ADD_Scarecrow_Drone.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find h3 headings before code blocks
lines = content.split('\n')
in_block = False
current_h3 = ''

diagrams_found = []

for i, line in enumerate(lines):
    if line.startswith('### '):
        current_h3 = line[4:].strip()
    if line.strip().startswith('```') and not in_block:
        in_block = True
        # Check next few lines for box chars
        if i+2 < len(lines):
            next_lines = lines[i+1:i+5]
            combined = ''.join(next_lines)
            has_box = any(c in combined for c in '|+-')
            if has_box and current_h3:
                # Normalize the key like the script does
                key = current_h3.replace(' ', '_')
                key = re.sub(r'^[\d.]+\s*', '', key)
                diagrams_found.append((current_h3, key))
    elif line.strip().startswith('```') and in_block:
        in_block = False

print("Diagrams found with their normalized keys:")
for orig, key in diagrams_found[:20]:
    print(f"  {orig!r} -> {key!r}")

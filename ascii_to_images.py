"""
Convert ASCII art diagrams from ADD_Scarecrow_Drone.md to PNG images.
Uses PIL/Pillow to render text with monospace font.
"""

import os
import re
from PIL import Image, ImageDraw, ImageFont

# Create output directory
OUTPUT_DIR = 'diagram_images'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_monospace_font(size=14):
    """Get a monospace font, with fallbacks."""
    font_options = [
        'C:/Windows/Fonts/consola.ttf',  # Consolas
        'C:/Windows/Fonts/cour.ttf',      # Courier New
        'C:/Windows/Fonts/lucon.ttf',     # Lucida Console
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',  # Linux
        '/System/Library/Fonts/Menlo.ttc',  # macOS
    ]

    for font_path in font_options:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue

    # Fallback to default
    return ImageFont.load_default()

def ascii_to_image(ascii_text, output_path, title=None, font_size=14, padding=40):
    """Convert ASCII art text to a PNG image."""

    # Clean up the text
    lines = ascii_text.split('\n')
    # Remove empty lines at start and end
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return False

    # Get font
    font = get_monospace_font(font_size)

    # Calculate dimensions
    # Use a temporary image to measure text
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)

    # Measure character size (use 'M' as reference)
    bbox = temp_draw.textbbox((0, 0), 'M', font=font)
    char_width = bbox[2] - bbox[0]
    char_height = bbox[3] - bbox[1]
    line_height = int(char_height * 1.2)

    # Find max line length
    max_chars = max(len(line) for line in lines)

    # Calculate image size
    title_space = 50 if title else 0
    img_width = int(max_chars * char_width * 0.6) + padding * 2
    img_height = len(lines) * line_height + padding * 2 + title_space

    # Ensure minimum size
    img_width = max(img_width, 400)
    img_height = max(img_height, 200)

    # Create image with white background
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)

    # Draw title if provided
    y_offset = padding
    if title:
        title_font = get_monospace_font(font_size + 4)
        draw.text((padding, y_offset), title, font=title_font, fill='#333333')
        y_offset += title_space

    # Draw each line
    for i, line in enumerate(lines):
        y = y_offset + i * line_height
        draw.text((padding, y), line, font=font, fill='black')

    # Save image
    img.save(output_path, 'PNG')
    print(f"  Created: {output_path}")
    return True

def extract_diagrams_from_markdown(md_path):
    """Extract all ASCII diagrams from the markdown file."""

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    diagrams = []

    # Find all code blocks (not OCL blocks)
    # Pattern: ``` followed by content until next ```
    pattern = r'```(?!ocl)(.*?)\n(.*?)```'
    matches = re.finditer(pattern, content, re.DOTALL)

    # Track section headers to name diagrams
    lines = content.split('\n')
    current_section = ""
    current_subsection = ""

    for match in matches:
        start_pos = match.start()
        code_content = match.group(2)

        # Skip if it's not an ASCII diagram (check for box characters or simple text diagrams)
        has_box_chars = any(c in code_content for c in '┌┐└┘│─┬┴├┤╔╗╚╝║═+|')
        has_arrows = any(c in code_content for c in '→←↑↓▼▲►◄>^v')

        if not has_box_chars and not has_arrows:
            continue

        # Find the section this diagram belongs to
        text_before = content[:start_pos]

        # Find last ## heading
        h2_matches = list(re.finditer(r'^## (.+)$', text_before, re.MULTILINE))
        if h2_matches:
            current_section = h2_matches[-1].group(1).strip()

        # Find last ### heading
        h3_matches = list(re.finditer(r'^### (.+)$', text_before, re.MULTILINE))
        if h3_matches:
            current_subsection = h3_matches[-1].group(1).strip()

        diagrams.append({
            'section': current_section,
            'subsection': current_subsection,
            'content': code_content,
            'position': start_pos
        })

    return diagrams

def sanitize_filename(name):
    """Convert a string to a valid filename."""
    # Remove numbers and dots at the start (like "1.1 ")
    name = re.sub(r'^[\d.]+\s*', '', name)
    # Replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Limit length
    return name[:50].strip('_')

def main():
    md_path = 'ADD_Scarecrow_Drone.md'

    print(f"Reading: {md_path}")
    diagrams = extract_diagrams_from_markdown(md_path)

    print(f"\nFound {len(diagrams)} ASCII diagrams")

    # Track names to avoid duplicates
    name_counts = {}

    for i, diagram in enumerate(diagrams):
        # Create filename from section/subsection
        if diagram['subsection']:
            base_name = sanitize_filename(diagram['subsection'])
        elif diagram['section']:
            base_name = sanitize_filename(diagram['section'])
        else:
            base_name = f"diagram"

        # Handle duplicates
        if base_name in name_counts:
            name_counts[base_name] += 1
            filename = f"{base_name}_{name_counts[base_name]}.png"
        else:
            name_counts[base_name] = 1
            filename = f"{base_name}.png"

        output_path = os.path.join(OUTPUT_DIR, filename)

        print(f"\n[{i+1}/{len(diagrams)}] {diagram['subsection'] or diagram['section']}")

        # Create title from subsection
        title = diagram['subsection'] if diagram['subsection'] else diagram['section']

        ascii_to_image(
            diagram['content'],
            output_path,
            title=None,  # Don't add title to image (will be in document heading)
            font_size=12,
            padding=30
        )

    print(f"\n\nAll diagrams saved to: {OUTPUT_DIR}/")
    print(f"Total: {len(diagrams)} images created")

    # Return list of diagram info for use by docx generator
    return diagrams

if __name__ == '__main__':
    main()

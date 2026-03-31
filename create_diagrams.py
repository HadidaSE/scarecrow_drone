"""
Create professional diagram images for ADD_Scarecrow_Drone.md
Uses matplotlib to create clean, professional diagrams.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, ConnectionPatch
import matplotlib.lines as mlines
import os

# Create output directory
OUTPUT_DIR = 'diagram_images'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Common colors
COLORS = {
    'blue_light': '#E3F2FD',
    'blue': '#2196F3',
    'blue_dark': '#1976D2',
    'green_light': '#E8F5E9',
    'green': '#4CAF50',
    'green_dark': '#388E3C',
    'orange_light': '#FFF3E0',
    'orange': '#FF9800',
    'orange_dark': '#F57C00',
    'purple_light': '#F3E5F5',
    'purple': '#9C27B0',
    'gray_light': '#F5F5F5',
    'gray': '#9E9E9E',
    'white': '#FFFFFF',
    'black': '#212121',
}

def save_figure(fig, name, dpi=250):
    """Save figure to file with high resolution."""
    path = os.path.join(OUTPUT_DIR, f'{name}.png')
    fig.savefig(path, dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  Created: {path}")

def draw_box(ax, x, y, width, height, text, color='#E3F2FD', edge_color='#1976D2',
             fontsize=9, bold=False, text_color='black', corner_radius=0.3):
    """Draw a rounded box with text."""
    box = FancyBboxPatch((x, y), width, height,
                          boxstyle=f"round,pad=0.02,rounding_size={corner_radius}",
                          facecolor=color, edgecolor=edge_color, linewidth=1.5)
    ax.add_patch(box)

    weight = 'bold' if bold else 'normal'
    ax.text(x + width/2, y + height/2, text, fontsize=fontsize,
            ha='center', va='center', fontweight=weight, color=text_color)

def draw_arrow(ax, start, end, color='#555555', style='->', linewidth=1.5):
    """Draw an arrow between two points."""
    ax.annotate('', xy=end, xytext=start,
                arrowprops=dict(arrowstyle=style, color=color, lw=linewidth))

def create_use_case_diagram():
    """Create Use Case Diagram - SIMPLIFIED BASIC VERSION."""
    fig, ax = plt.subplots(1, 1, figsize=(28, 22))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.set_aspect('equal')
    ax.axis('off')

    # System boundary - simple rectangle
    system_box = FancyBboxPatch((18, 10), 64, 60, boxstyle="round,pad=0.02,rounding_size=0.5",
                                 facecolor='#FAFAFA', edgecolor='#333333', linewidth=3)
    ax.add_patch(system_box)
    ax.text(50, 67, 'Scarecrow Drone System', fontsize=24, fontweight='bold', ha='center')

    # Use cases (ellipses) - simpler, fewer, cleaner text
    use_cases = [
        (35, 55, 'Map Area'),
        (35, 40, 'Start Flight'),
        (65, 55, 'Detect Birds'),
        (65, 40, 'Chase Birds'),
        (50, 22, 'Store Data'),
    ]

    for x, y, text in use_cases:
        ellipse = patches.Ellipse((x, y), 22, 10, facecolor='#E3F2FD',
                                   edgecolor='#1976D2', linewidth=2)
        ax.add_patch(ellipse)
        ax.text(x, y, text, fontsize=14, ha='center', va='center', fontweight='bold')

    # Actors - simple stick figures
    # Operator
    ax.plot([8, 8], [38, 44], 'k-', linewidth=3)  # body
    ax.plot([5, 11], [41, 41], 'k-', linewidth=3)  # arms
    ax.plot([8, 5], [38, 33], 'k-', linewidth=3)  # left leg
    ax.plot([8, 11], [38, 33], 'k-', linewidth=3)  # right leg
    circle = plt.Circle((8, 47), 3, facecolor='white', edgecolor='black', linewidth=3)
    ax.add_patch(circle)
    ax.text(8, 28, 'Operator', fontsize=16, ha='center', fontweight='bold')

    # System actor
    ax.plot([92, 92], [38, 44], 'k-', linewidth=3)
    ax.plot([89, 95], [41, 41], 'k-', linewidth=3)
    ax.plot([92, 89], [38, 33], 'k-', linewidth=3)
    ax.plot([92, 95], [38, 33], 'k-', linewidth=3)
    circle2 = plt.Circle((92, 47), 3, facecolor='white', edgecolor='black', linewidth=3)
    ax.add_patch(circle2)
    ax.text(92, 28, 'System', fontsize=16, ha='center', fontweight='bold')

    # Simple connection lines
    ax.plot([11, 24], [45, 55], 'k-', linewidth=2)  # Operator to Map Area
    ax.plot([11, 24], [45, 40], 'k-', linewidth=2)  # Operator to Start Flight

    ax.plot([89, 76], [45, 55], 'k-', linewidth=2)  # System to Detect Birds
    ax.plot([89, 76], [45, 40], 'k-', linewidth=2)  # System to Chase Birds
    ax.plot([89, 61], [38, 22], 'k-', linewidth=2)  # System to Store Data

    save_figure(fig, 'Use_Case_Diagram')

def create_deployment_diagram_part1():
    """Create Deployment Diagram Part 1 - Client and Server - 2X BIGGER CELL TEXT."""
    fig, ax = plt.subplots(1, 1, figsize=(48, 40))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect('equal')
    ax.axis('off')

    # ===== CLIENT MACHINE =====
    client_box = FancyBboxPatch((5, 78), 90, 20, boxstyle="round,pad=0.02,rounding_size=0.5",
                                 facecolor=COLORS['blue_light'], edgecolor=COLORS['blue_dark'], linewidth=4)
    ax.add_patch(client_box)
    ax.text(50, 96, 'Client Machine', fontsize=40, fontweight='bold', ha='center')

    # Web Browser
    draw_box(ax, 10, 80, 80, 15, '', COLORS['white'], COLORS['blue'], corner_radius=0.3)
    ax.text(50, 93, 'Web Browser', fontsize=36, fontweight='bold', ha='center')

    # React Frontend
    draw_box(ax, 15, 81, 70, 10, '', '#BBDEFB', COLORS['blue'], corner_radius=0.2)
    ax.text(50, 89, 'React Frontend (Port 5173)', fontsize=32, fontweight='bold', ha='center')

    # Frontend components - 2x cell text (18 -> 36)
    for i, (name, x) in enumerate([('Dashboard\nPage', 28), ('Flight\nHistory', 50), ('Detection\nGallery', 72)]):
        draw_box(ax, x-10, 82, 20, 6, name, COLORS['white'], '#64B5F6', fontsize=36)

    # Arrow to server
    ax.annotate('', xy=(50, 55), xytext=(50, 78),
                arrowprops=dict(arrowstyle='<->', color='#555', lw=4))
    ax.text(52, 66, 'HTTP/REST\nAPI Calls', fontsize=28, ha='left', style='italic')

    # ===== GROUND STATION =====
    server_box = FancyBboxPatch((5, 5), 90, 50, boxstyle="round,pad=0.02,rounding_size=0.5",
                                 facecolor=COLORS['green_light'], edgecolor=COLORS['green_dark'], linewidth=4)
    ax.add_patch(server_box)
    ax.text(50, 53, 'Ground Station (Server Machine)', fontsize=40, fontweight='bold', ha='center')

    # FastAPI Backend
    draw_box(ax, 10, 28, 80, 23, '', COLORS['white'], COLORS['green'], corner_radius=0.3)
    ax.text(50, 49, 'FastAPI Backend (Port 5000)', fontsize=36, fontweight='bold', ha='center')

    # Controllers
    draw_box(ax, 12, 42, 76, 6, '', '#C8E6C9', COLORS['green'], corner_radius=0.2)
    ax.text(50, 46.5, 'Controllers', fontsize=32, fontweight='bold', ha='center')
    for name, x in [('Drone\nController', 28), ('Flight\nController', 50), ('Connection\nController', 72)]:
        draw_box(ax, x-12, 42.5, 24, 5, name, COLORS['white'], '#81C784', fontsize=32)

    # Services
    draw_box(ax, 12, 35, 76, 6, '', '#C8E6C9', COLORS['green'], corner_radius=0.2)
    ax.text(50, 39.5, 'Services', fontsize=32, fontweight='bold', ha='center')
    for name, x in [('Drone\nService', 28), ('Flight\nService', 50), ('Detection\nService', 72)]:
        draw_box(ax, x-12, 35.5, 24, 5, name, COLORS['white'], '#81C784', fontsize=32)

    # Repositories
    draw_box(ax, 12, 29, 76, 5, '', '#C8E6C9', COLORS['green'], corner_radius=0.2)
    ax.text(50, 32.5, 'Repositories', fontsize=32, fontweight='bold', ha='center')
    for name, x in [('Drone\nRepository', 35), ('Flight\nRepository', 65)]:
        draw_box(ax, x-12, 29.5, 24, 4, name, COLORS['white'], '#81C784', fontsize=32)

    # SQLite Database
    draw_box(ax, 30, 22, 40, 5, 'SQLite Database', '#DCEDC8', '#7CB342', fontsize=32, bold=True)

    # Detection Module
    draw_box(ax, 10, 7, 38, 13, '', COLORS['white'], COLORS['green'], corner_radius=0.3)
    ax.text(29, 18, 'Detection Module (detect.py)', fontsize=28, fontweight='bold', ha='center')
    for name, x in [('FFmpeg\nDecoder', 18), ('YOLO\nModel', 29), ('OpenCV\nProcessing', 40)]:
        draw_box(ax, x-6, 8, 12, 8, name, '#E8F5E9', '#81C784', fontsize=28)

    # File Storage
    draw_box(ax, 52, 7, 38, 13, '', COLORS['white'], COLORS['green'], corner_radius=0.3)
    ax.text(71, 18, 'File Storage', fontsize=28, fontweight='bold', ha='center')
    for name, x in [('recordings/\n(Video files)', 62), ('detection_images/\n(Frames)', 80)]:
        draw_box(ax, x-8, 8, 16, 8, name, '#E8F5E9', '#81C784', fontsize=28)

    save_figure(fig, 'Deployment_Diagram')

def create_deployment_diagram_part2():
    """Create Deployment Diagram Part 2 - Drone - 2X BIGGER CELL TEXT."""
    fig, ax = plt.subplots(1, 1, figsize=(48, 38))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.set_aspect('equal')
    ax.axis('off')

    # Communication arrows at top
    ax.text(50, 73, 'Communication with Ground Station', fontsize=40, fontweight='bold', ha='center')

    ax.annotate('', xy=(25, 68), xytext=(25, 60),
                arrowprops=dict(arrowstyle='<-', color='#555', lw=4))
    ax.text(5, 64, 'MAVLink Commands\n(Flight control, waypoints,\narm/disarm, mode changes)', fontsize=28, ha='left', style='italic')

    ax.annotate('', xy=(75, 60), xytext=(75, 68),
                arrowprops=dict(arrowstyle='<-', color='#555', lw=4))
    ax.text(77, 64, 'RTP/UDP Video Stream\n(GStreamer JPEG @ 5000)', fontsize=28, ha='left', style='italic')

    # ===== DRONE =====
    drone_box = FancyBboxPatch((5, 5), 90, 52, boxstyle="round,pad=0.02,rounding_size=0.5",
                                facecolor=COLORS['orange_light'], edgecolor=COLORS['orange_dark'], linewidth=4)
    ax.add_patch(drone_box)
    ax.text(50, 55, 'Drone (Airborne Unit)', fontsize=40, fontweight='bold', ha='center')

    # Flight Controller
    draw_box(ax, 10, 40, 80, 12, '', COLORS['white'], COLORS['orange'], corner_radius=0.3)
    ax.text(50, 50, 'Flight Controller (Pixhawk)', fontsize=36, fontweight='bold', ha='center')
    draw_box(ax, 12, 41, 76, 8, '', '#FFE0B2', COLORS['orange'], corner_radius=0.2)
    ax.text(50, 47, 'ArduPilot Firmware', fontsize=32, fontweight='bold', ha='center')
    for name, x in [('MAVLink Protocol', 35), ('IMU / Sensors\n(Altitude, Attitude)', 65)]:
        draw_box(ax, x-14, 42, 28, 5, name, COLORS['white'], '#FFCC80', fontsize=36)

    # Companion Computer
    draw_box(ax, 10, 24, 80, 14, '', COLORS['white'], COLORS['orange'], corner_radius=0.3)
    ax.text(50, 36, 'Companion Computer', fontsize=36, fontweight='bold', ha='center')
    for name, x in [('GStreamer\nEncoder', 28), ('Camera\nInterface', 50), ('WiFi/Telemetry\nRadio Link', 72)]:
        draw_box(ax, x-12, 25, 24, 9, name, '#FFE0B2', '#FFCC80', fontsize=36)

    # Hardware
    draw_box(ax, 10, 7, 80, 14, '', COLORS['white'], COLORS['orange'], corner_radius=0.3)
    ax.text(50, 19, 'Hardware Components', fontsize=36, fontweight='bold', ha='center')
    for name, x in [('Camera\n(640x480)', 22), ('Motors\n(x4/x6)', 40), ('Battery\n(LiPo 4S)', 60), ('Deterrent\nModule', 78)]:
        draw_box(ax, x-10, 8, 20, 9, name, '#FFE0B2', '#FFCC80', fontsize=36)

    save_figure(fig, 'Deployment_Diagram_2')

def create_class_diagram():
    """Create Class Diagram - 2.67X CELL TEXT, 2X NAMES."""
    fig, ax = plt.subplots(1, 1, figsize=(50, 40))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title
    ax.text(50, 78, 'Class Diagram', fontsize=48, fontweight='bold', ha='center')

    # Classes with attributes and methods - 4X cell text, 2X names
    classes = [
        {'name': 'Drone', 'x': 5, 'y': 52, 'w': 28, 'h': 24,
         'attrs': ['id: int', 'name: str', 'connection_string: str', 'status: str'],
         'methods': ['connect()', 'disconnect()', 'arm()', 'disarm()']},

        {'name': 'Flight', 'x': 36, 'y': 52, 'w': 28, 'h': 24,
         'attrs': ['id: int', 'drone_id: int', 'start_time: datetime', 'status: str'],
         'methods': ['start()', 'end()', 'abort()']},

        {'name': 'Detection', 'x': 67, 'y': 52, 'w': 28, 'h': 24,
         'attrs': ['id: int', 'flight_id: int', 'timestamp: datetime', 'confidence: float'],
         'methods': ['save_image()', 'get_location()']},

        {'name': 'ChaseEvent', 'x': 67, 'y': 24, 'w': 28, 'h': 22,
         'attrs': ['id: int', 'detection_id: int', 'outcome: str'],
         'methods': ['start_chase()', 'end_chase()']},
    ]

    for cls in classes:
        x, y, w, h = cls['x'], cls['y'], cls['w'], cls['h']

        # Class box header - 2X name size (24 -> 48)
        header_h = 5
        draw_box(ax, x, y+h-header_h, w, header_h, cls['name'], '#BBDEFB', COLORS['blue_dark'],
                fontsize=48, bold=True)

        # Attributes section - 2.67X cell text (18 -> 48)
        attr_h = (h - header_h) * 0.5 if cls['attrs'] else 0
        if cls['attrs']:
            draw_box(ax, x, y + (h-header_h)*0.5, w, attr_h, '', COLORS['white'], COLORS['blue_dark'])
            attr_text = '\n'.join(cls['attrs'])
            ax.text(x + w/2, y + (h-header_h)*0.75, attr_text, fontsize=48, ha='center', va='center',
                   family='monospace')

        # Methods section - 2.67X cell text (18 -> 48)
        method_h = (h - header_h) * 0.5
        if cls['attrs']:
            # With attributes: methods box goes at bottom half
            method_box_y = y
            method_box_h = method_h
            method_text_y = y + method_h / 2
        else:
            # No attributes: methods box spans full area below header
            method_box_y = y
            method_box_h = h - header_h
            method_text_y = y + (h - header_h) / 2

        draw_box(ax, x, method_box_y, w, method_box_h, '', COLORS['white'], COLORS['blue_dark'])
        method_text = '\n'.join(cls['methods'])
        ax.text(x + w/2, method_text_y, method_text, fontsize=48, ha='center', va='center',
               family='monospace')

    # Relationships (lines with labels) - 2.67X text
    # Drone -> Flight (1 to many)
    ax.plot([33, 36], [64, 64], 'k-', linewidth=3)
    ax.text(33.5, 66.5, '1', fontsize=32, fontweight='bold')
    ax.text(35, 66.5, '*', fontsize=35, fontweight='bold')

    # Flight -> Detection (1 to many)
    ax.plot([64, 67], [64, 64], 'k-', linewidth=3)
    ax.text(64.5, 66.5, '1', fontsize=32, fontweight='bold')
    ax.text(66, 66.5, '*', fontsize=35, fontweight='bold')

    # Detection -> ChaseEvent (1 to 0..1)
    ax.plot([81, 81], [52, 46], 'k-', linewidth=3)
    ax.text(82.5, 50, '1', fontsize=32, fontweight='bold')
    ax.text(82.5, 47, '0..1', fontsize=27, fontweight='bold')

    save_figure(fig, 'Class_Diagram')

def create_erd_diagram():
    """Create Entity Relationship Diagram - 2X BIGGER TEXT EVERYWHERE."""
    fig, ax = plt.subplots(1, 1, figsize=(56, 44))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title - 2x (40 -> 80)
    ax.text(50, 78, 'Entity Relationship Diagram', fontsize=80, fontweight='bold', ha='center')

    # Tables - 2X text everywhere
    tables = [
        {'name': 'drones', 'x': 3, 'y': 48, 'fields': [
            ('id', 'INTEGER', 'PK'),
            ('name', 'TEXT', ''),
            ('connection_string', 'TEXT', ''),
            ('status', 'TEXT', ''),
            ('created_at', 'TIMESTAMP', ''),
        ]},
        {'name': 'flights', 'x': 36, 'y': 48, 'fields': [
            ('id', 'INTEGER', 'PK'),
            ('drone_id', 'INTEGER', 'FK'),
            ('start_time', 'TIMESTAMP', ''),
            ('end_time', 'TIMESTAMP', ''),
            ('status', 'TEXT', ''),
        ]},
        {'name': 'detections', 'x': 69, 'y': 48, 'fields': [
            ('id', 'INTEGER', 'PK'),
            ('flight_id', 'INTEGER', 'FK'),
            ('timestamp', 'TIMESTAMP', ''),
            ('confidence', 'REAL', ''),
            ('image_path', 'TEXT', ''),
        ]},
        {'name': 'chase_events', 'x': 69, 'y': 8, 'fields': [
            ('id', 'INTEGER', 'PK'),
            ('detection_id', 'INTEGER', 'FK'),
            ('start_time', 'TIMESTAMP', ''),
            ('end_time', 'TIMESTAMP', ''),
            ('outcome', 'TEXT', ''),
        ]},
    ]

    for tbl in tables:
        x, y = tbl['x'], tbl['y']
        w, h = 28, 6 + len(tbl['fields']) * 4  # Bigger width and row height

        # Table header - 2x (26 -> 52)
        draw_box(ax, x, y+h-6, w, 6, tbl['name'], '#C5CAE9', '#3F51B5', fontsize=52, bold=True)

        # Fields - 2x (18 -> 36)
        for i, (fname, ftype, fkey) in enumerate(tbl['fields']):
            fy = y + h - 6 - (i+1)*4
            draw_box(ax, x, fy, w, 4, '', COLORS['white'], '#3F51B5')

            key_color = '#F44336' if fkey == 'PK' else ('#FF9800' if fkey == 'FK' else 'black')
            key_text = f"[{fkey}] " if fkey else ""
            ax.text(x+1.5, fy+2, f"{key_text}{fname}: {ftype}", fontsize=36, va='center',
                   color=key_color if fkey else 'black', fontweight='bold' if fkey else 'normal')

    # Relationships - 2x text
    # drones -> flights
    ax.annotate('', xy=(36, 62), xytext=(31, 62),
                arrowprops=dict(arrowstyle='-', color='#333', lw=3))
    ax.plot([31, 31], [59, 65], 'k-', linewidth=4)  # "1" side
    ax.text(32.5, 66, '1', fontsize=52, fontweight='bold')
    ax.text(34.5, 66, 'n', fontsize=52, fontweight='bold')

    # flights -> detections
    ax.annotate('', xy=(69, 62), xytext=(64, 62),
                arrowprops=dict(arrowstyle='-', color='#333', lw=3))
    ax.text(65, 66, '1', fontsize=52, fontweight='bold')
    ax.text(67.5, 66, 'n', fontsize=52, fontweight='bold')

    # detections -> chase_events
    ax.plot([83, 83], [48, 34], 'k-', linewidth=3)
    ax.text(84.5, 44, '1', fontsize=52, fontweight='bold')
    ax.text(84.5, 38, '0..1', fontsize=44, fontweight='bold')

    save_figure(fig, 'Data_Objects_Relationships')

def create_database_schema():
    """Create Database Schema Diagram - BIGGER TEXT, no drones/waypoints."""
    fig, ax = plt.subplots(1, 1, figsize=(44, 32))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title - 2x bigger
    ax.text(50, 58, 'Database Schema', fontsize=48, fontweight='bold', ha='center')

    # SQLite icon/box - 2x bigger text
    draw_box(ax, 30, 38, 40, 14, 'SQLite Database\n(database.db)', '#DCEDC8', '#7CB342',
            fontsize=36, bold=True)

    # Tables - removed drones and waypoints, bigger text
    tables = ['flights', 'detections', 'chase_events']
    positions = [(20, 12), (50, 12), (80, 12)]

    for (x, y), name in zip(positions, tables):
        draw_box(ax, x-12, y, 24, 12, name, '#E3F2FD', COLORS['blue_dark'], fontsize=32, bold=True)

    # Lines from database to tables
    for (x, y), name in zip(positions, tables):
        ax.plot([50, x], [38, y+12], 'k-', linewidth=3)

    save_figure(fig, 'Databases')

def create_sequence_diagram(diagram_name, title, participants, messages):
    """Create a sequence diagram - 2X BIGGER TEXT EVERYWHERE."""
    fig, ax = plt.subplots(1, 1, figsize=(56, max(44, len(messages) * 3 + 18)))

    n_participants = len(participants)
    width = 100
    height = len(messages) * 5 + 18

    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title - 2x (36 -> 72)
    ax.text(width/2, height-1, title, fontsize=72, fontweight='bold', ha='center')

    # Participant positions
    spacing = width / (n_participants + 1)
    positions = [(i+1) * spacing for i in range(n_participants)]

    # Draw participants - 2x (22 -> 44)
    for i, (pos, pname) in enumerate(zip(positions, participants)):
        draw_box(ax, pos-12, height-8, 24, 6, pname, '#E3F2FD', COLORS['blue_dark'], fontsize=44, bold=True)
        # Lifeline
        ax.plot([pos, pos], [height-8, 2], 'k--', linewidth=2, alpha=0.5)

    # Draw messages - 2x (20 -> 40)
    y = height - 15
    for msg in messages:
        from_idx, to_idx, label, is_return = msg
        from_x = positions[from_idx]
        to_x = positions[to_idx]

        style = '<-' if is_return else '->'
        linestyle = '--' if is_return else '-'

        ax.annotate('', xy=(to_x, y), xytext=(from_x, y),
                    arrowprops=dict(arrowstyle=style, color='#333', lw=3, linestyle=linestyle))

        mid_x = (from_x + to_x) / 2
        ax.text(mid_x, y + 1.5, label, fontsize=40, ha='center', va='bottom', fontweight='bold')

        y -= 5

    save_figure(fig, diagram_name)

def create_state_machine(name, title, states, transitions):
    """Create a state machine diagram - DOUBLE SIZE TEXT."""
    fig, ax = plt.subplots(1, 1, figsize=(44, 30))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title
    ax.text(50, 67, title, fontsize=40, fontweight='bold', ha='center')

    # Draw states - DOUBLE SIZE text
    for state_name, (x, y), is_initial, is_final in states:
        if is_initial:
            # Initial state (filled circle) - bigger
            circle = plt.Circle((x-14, y), 4, facecolor='black', edgecolor='black')
            ax.add_patch(circle)
            ax.annotate('', xy=(x-9, y), xytext=(x-10, y),
                        arrowprops=dict(arrowstyle='->', color='black', lw=3))

        # State box - DOUBLE SIZE text
        color = '#FFCDD2' if is_final else '#E3F2FD'
        edge = '#D32F2F' if is_final else COLORS['blue_dark']
        draw_box(ax, x-15, y-6, 30, 12, state_name, color, edge, fontsize=28, bold=True)

        if is_final:
            # Final state indicator (double border effect)
            inner = FancyBboxPatch((x-14, y-5), 28, 10, boxstyle="round,pad=0.02,rounding_size=0.2",
                                    facecolor='none', edgecolor='#D32F2F', linewidth=3)
            ax.add_patch(inner)

    # Draw transitions - DOUBLE SIZE text
    for from_state, to_state, label, (fx, fy), (tx, ty), curve in transitions:
        if curve:
            style = f"arc3,rad={curve}"
        else:
            style = "arc3,rad=0"

        ax.annotate('', xy=(tx, ty), xytext=(fx, fy),
                    arrowprops=dict(arrowstyle='->', color='#333', lw=3,
                                   connectionstyle=style))

        # Label position - DOUBLE SIZE text
        mid_x = (fx + tx) / 2
        mid_y = (fy + ty) / 2 + (4 if curve else 2)
        ax.text(mid_x, mid_y, label, fontsize=24, ha='center', va='bottom', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='none'))

    save_figure(fig, name)

def create_package_diagram():
    """Create Package Diagram - 2X BIGGER TEXT EVERYWHERE."""
    fig, ax = plt.subplots(1, 1, figsize=(48, 38))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title - 2x (32 -> 64)
    ax.text(50, 78, 'Package Diagram', fontsize=64, fontweight='bold', ha='center')

    # Packages
    packages = [
        {'name': 'frontend', 'x': 8, 'y': 52, 'w': 28, 'h': 20,
         'sub': ['components/', 'pages/', 'services/', 'hooks/']},
        {'name': 'backend', 'x': 38, 'y': 52, 'w': 28, 'h': 20,
         'sub': ['controllers/', 'services/', 'repositories/', 'models/']},
        {'name': 'detection', 'x': 68, 'y': 52, 'w': 28, 'h': 20,
         'sub': ['detect.py', 'yolo_model/', 'utils/']},
        {'name': 'database', 'x': 38, 'y': 22, 'w': 28, 'h': 18,
         'sub': ['database.db', 'migrations/']},
        {'name': 'shared', 'x': 8, 'y': 22, 'w': 28, 'h': 18,
         'sub': ['types/', 'constants/', 'utils/']},
    ]

    for pkg in packages:
        x, y, w, h = pkg['x'], pkg['y'], pkg['w'], pkg['h']

        # Package tab
        tab = FancyBboxPatch((x, y+h-3), 12, 3, boxstyle="round,pad=0.02,rounding_size=0.1",
                              facecolor='#C5CAE9', edgecolor='#3F51B5', linewidth=2)
        ax.add_patch(tab)

        # Package body
        body = FancyBboxPatch((x, y), w, h-3, boxstyle="round,pad=0.02,rounding_size=0.2",
                               facecolor='#E8EAF6', edgecolor='#3F51B5', linewidth=2)
        ax.add_patch(body)

        # Package name - 2x (22 -> 44)
        ax.text(x + w/2, y + h - 5, pkg['name'], fontsize=44, fontweight='bold', ha='center')

        # Sub-items - 2x (16 -> 32)
        for i, sub in enumerate(pkg['sub']):
            ax.text(x + 3, y + h - 9 - i*3, f"  {sub}", fontsize=32, va='top')

    # Dependencies (dashed arrows)
    deps = [
        ((22, 52), (52, 72)),  # frontend -> backend
        ((52, 52), (52, 40)),  # backend -> database
        ((66, 62), (68, 62)),  # backend -> detection
        ((36, 31), (38, 31)),  # shared -> database
        ((22, 40), (22, 52)),  # shared -> frontend
    ]

    for (fx, fy), (tx, ty) in deps:
        ax.annotate('', xy=(tx, ty), xytext=(fx, fy),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2.5, linestyle='--'))

    save_figure(fig, 'Packages')
    save_figure(fig, 'Packages_2')  # Duplicate for compatibility

def main():
    print("Creating professional diagram images...\n")

    # 1. Use Case Diagram
    print("[1/10] Use Case Diagram")
    create_use_case_diagram()

    # 2. Deployment Diagram (split into 2 parts)
    print("[2/10] Deployment Diagram (Part 1 - Client/Server)")
    create_deployment_diagram_part1()
    print("[2/10] Deployment Diagram (Part 2 - Drone)")
    create_deployment_diagram_part2()

    # 3. Class Diagram
    print("[3/10] Class Diagram")
    create_class_diagram()

    # 4. ERD / Data Objects
    print("[4/10] Data Objects Relationships (ERD)")
    create_erd_diagram()

    # 5. Database Schema
    print("[5/10] Database Schema")
    create_database_schema()

    # 6. Sequence Diagrams
    print("[6/10] Sequence Diagrams")

    # Sequence 1: Start Flight
    create_sequence_diagram(
        'Sequence_Diagrams',
        'SD1: Start Detection Flight',
        ['Operator', 'Frontend', 'Backend', 'DroneService', 'Drone'],
        [
            (0, 1, 'Click Start Flight', False),
            (1, 2, 'POST /flights/start', False),
            (2, 3, 'start_flight(drone_id)', False),
            (3, 4, 'arm()', False),
            (4, 3, 'armed=true', True),
            (3, 4, 'takeoff(altitude)', False),
            (4, 3, 'flying=true', True),
            (3, 2, 'flight_started', True),
            (2, 1, 'flight_id, status', True),
            (1, 0, 'Display: Flight Active', True),
        ]
    )

    # Sequence 2: Detect Birds
    create_sequence_diagram(
        'Sequence_Diagrams_2',
        'SD2: Detect Birds',
        ['VideoStream', 'DetectionService', 'YOLOModel', 'Database'],
        [
            (0, 1, 'frame', False),
            (1, 2, 'detect(frame)', False),
            (2, 1, 'detections[]', True),
            (1, 1, 'filter birds', False),
            (1, 3, 'save_detection()', False),
            (3, 1, 'detection_id', True),
            (1, 1, 'save_image()', False),
        ]
    )

    # Sequence 3: Chase Birds
    create_sequence_diagram(
        'Sequence_Diagrams_3',
        'SD3: Chase Birds',
        ['DetectionService', 'ChaseService', 'DroneService', 'Drone'],
        [
            (0, 1, 'bird_detected(location)', False),
            (1, 2, 'navigate_to(location)', False),
            (2, 3, 'goto(lat, lng, alt)', False),
            (3, 2, 'reached', True),
            (2, 1, 'at_location', True),
            (1, 2, 'play_deterrent()', False),
            (2, 3, 'activate_speaker()', False),
            (3, 2, 'playing', True),
            (1, 0, 'chase_complete', True),
        ]
    )

    # More sequence diagrams
    for i in range(4, 9):
        create_sequence_diagram(
            f'Sequence_Diagrams_{i}',
            f'SD{i}: Additional Flow {i-3}',
            ['Client', 'API', 'Service', 'Database'],
            [
                (0, 1, 'request()', False),
                (1, 2, 'process()', False),
                (2, 3, 'query()', False),
                (3, 2, 'data', True),
                (2, 1, 'result', True),
                (1, 0, 'response', True),
            ]
        )

    # 7. State Machines
    print("[7/10] State Machine Diagrams")

    # Drone State Machine - adjusted for larger boxes (30 wide, 12 tall)
    create_state_machine(
        'State_Machines',
        'Drone State Machine',
        [
            ('Disconnected', (20, 50), True, False),
            ('Connected', (50, 50), False, False),
            ('Armed', (80, 50), False, False),
            ('Flying', (80, 22), False, False),
            ('Landing', (50, 22), False, False),
            ('Idle', (20, 22), False, True),
        ],
        [
            ('Disconnected', 'Connected', 'connect()', (35, 50), (35, 50), 0),
            ('Connected', 'Armed', 'arm()', (65, 50), (65, 50), 0),
            ('Armed', 'Flying', 'takeoff()', (80, 44), (80, 28), 0),
            ('Flying', 'Landing', 'land()', (65, 22), (65, 22), 0),
            ('Landing', 'Idle', 'landed', (35, 22), (35, 22), 0),
            ('Connected', 'Disconnected', 'disconnect()', (35, 56), (35, 56), 0.4),
        ]
    )

    # Flight State Machine - adjusted for larger boxes
    create_state_machine(
        'State_Machines_2',
        'Flight State Machine',
        [
            ('Idle', (20, 45), True, False),
            ('Planning', (50, 45), False, False),
            ('Active', (80, 45), False, False),
            ('Completed', (50, 18), False, True),
            ('Aborted', (80, 18), False, True),
        ],
        [
            ('Idle', 'Planning', 'plan_flight()', (35, 45), (35, 45), 0),
            ('Planning', 'Active', 'start()', (65, 45), (65, 45), 0),
            ('Active', 'Completed', 'complete()', (78, 39), (58, 24), 0),
            ('Active', 'Aborted', 'abort()', (80, 39), (80, 24), 0),
        ]
    )

    # Detection State Machine - adjusted for larger boxes
    create_state_machine(
        'State_Machines_3',
        'Detection State Machine',
        [
            ('Waiting', (20, 45), True, False),
            ('Processing', (50, 45), False, False),
            ('Detected', (80, 45), False, False),
            ('Saved', (50, 18), False, True),
        ],
        [
            ('Waiting', 'Processing', 'frame_received', (35, 45), (35, 45), 0),
            ('Processing', 'Detected', 'bird_found', (65, 45), (65, 45), 0),
            ('Processing', 'Waiting', 'no_bird', (35, 51), (35, 51), 0.4),
            ('Detected', 'Saved', 'save()', (78, 39), (58, 24), 0),
        ]
    )

    # Chase State Machine - adjusted for larger boxes
    create_state_machine(
        'State_Machines_4',
        'Chase Event State Machine',
        [
            ('Idle', (20, 45), True, False),
            ('Navigating', (50, 45), False, False),
            ('Deterring', (80, 45), False, False),
            ('Completed', (50, 18), False, True),
        ],
        [
            ('Idle', 'Navigating', 'start_chase()', (35, 45), (35, 45), 0),
            ('Navigating', 'Deterring', 'arrived', (65, 45), (65, 45), 0),
            ('Deterring', 'Completed', 'bird_fled', (78, 39), (58, 24), 0),
            ('Deterring', 'Navigating', 'bird_moved', (65, 51), (65, 51), 0.4),
        ]
    )

    # 8. Package Diagram
    print("[8/10] Package Diagram")
    create_package_diagram()

    # 9-10. Class Description diagrams (simplified)
    print("[9/10] Class Description Diagrams")
    for i in range(1, 12):
        fig, ax = plt.subplots(1, 1, figsize=(20, 14))
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 60)
        ax.axis('off')

        class_name = ['Drone', 'Flight', 'Detection', 'ChaseEvent', 'Waypoint',
                      'DroneService', 'FlightService', 'DetectionService',
                      'DroneController', 'FlightController', 'DetectionController'][i-1] if i <= 11 else f'Class{i}'

        draw_box(ax, 20, 20, 60, 30, '', COLORS['white'], COLORS['blue_dark'])
        draw_box(ax, 20, 45, 60, 5, class_name, '#BBDEFB', COLORS['blue_dark'], fontsize=14, bold=True)

        ax.text(50, 38, 'Attributes:\n+ id: int\n+ name: str\n+ status: str',
                fontsize=12, ha='center', va='top', family='monospace')
        ax.text(50, 28, 'Methods:\n+ create()\n+ update()\n+ delete()',
                fontsize=12, ha='center', va='top', family='monospace')

        suffix = '' if i == 1 else f'_{i}'
        save_figure(fig, f'Class_Description{suffix}')

    # 11. Area Mapping Capture Flow Diagram
    print("[11/11] Area Mapping Capture Flow Diagram")
    create_mapping_capture_diagram()

    print("\n" + "="*50)
    print(f"All diagrams saved to: {OUTPUT_DIR}/")
    print("="*50)

def create_mapping_capture_diagram():
    """Create Area Mapping Data Capture Flow Diagram - Professional flowchart style."""
    fig, ax = plt.subplots(1, 1, figsize=(48, 40))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title
    ax.text(50, 77, 'Area Mapping Data Capture Flow', fontsize=42, fontweight='bold', ha='center')

    # Left column - Operator and UI
    draw_box(ax, 5, 62, 18, 10, 'Operator', '#E8F5E9', '#388E3C', fontsize=28, bold=True)
    draw_box(ax, 5, 45, 18, 10, 'Dashboard UI\n(Map View)', '#E3F2FD', COLORS['blue_dark'], fontsize=22, bold=True)
    draw_box(ax, 5, 28, 18, 10, 'DroneService', '#FFF3E0', '#F57C00', fontsize=24, bold=True)
    draw_box(ax, 5, 11, 18, 10, 'AreaMap\nModel', '#F3E5F5', '#7B1FA2', fontsize=24, bold=True)

    # Center column - Drone and data capture
    draw_box(ax, 38, 45, 24, 12, 'Drone\n(Physical)', '#DCEDC8', '#7CB342', fontsize=26, bold=True)

    # Boundary points box - larger
    draw_box(ax, 35, 24, 30, 16, 'Boundary Points\n(GPS Coordinates)\n\nNW Corner\nNE Corner\nSE Corner\nSW Corner',
             '#FFF9C4', '#FBC02D', fontsize=20, bold=False)

    # Right column - Database
    draw_box(ax, 75, 55, 20, 14, 'Database', '#BBDEFB', COLORS['blue_dark'], fontsize=28, bold=True)
    draw_box(ax, 75, 28, 20, 16, 'area_maps\ntable\n\nboundaries\narea_size\nstatus',
             '#C5CAE9', '#3F51B5', fontsize=20, bold=True)

    # Arrows with numbered steps - thicker lines
    # 1. Operator -> Dashboard
    ax.annotate('', xy=(14, 55), xytext=(14, 62),
                arrowprops=dict(arrowstyle='->', color='#333', lw=3))
    ax.text(16, 58, '1. Initiate\nMapping', fontsize=18, va='center')

    # 2. Dashboard -> DroneService
    ax.annotate('', xy=(14, 38), xytext=(14, 45),
                arrowprops=dict(arrowstyle='->', color='#333', lw=3))
    ax.text(16, 41, '2. Start\nRequest', fontsize=18, va='center')

    # 3. DroneService -> Drone
    ax.annotate('', xy=(38, 50), xytext=(23, 33),
                arrowprops=dict(arrowstyle='->', color='#333', lw=3))
    ax.text(28, 44, '3. Scan\nArea', fontsize=18, ha='center')

    # 4. Drone -> Boundary Points
    ax.annotate('', xy=(50, 40), xytext=(50, 45),
                arrowprops=dict(arrowstyle='->', color='#333', lw=3))
    ax.text(53, 42, '4. Capture\nGPS', fontsize=18, va='center')

    # 5. Boundary Points -> DroneService
    ax.annotate('', xy=(23, 30), xytext=(35, 30),
                arrowprops=dict(arrowstyle='->', color='#333', lw=3))
    ax.text(28, 32, '5. Return\nData', fontsize=18, ha='center')

    # 6. DroneService -> AreaMap
    ax.annotate('', xy=(14, 21), xytext=(14, 28),
                arrowprops=dict(arrowstyle='->', color='#333', lw=3))
    ax.text(16, 24, '6. Calculate\nArea', fontsize=18, va='center')

    # 7. AreaMap -> Database
    ax.annotate('', xy=(75, 36), xytext=(23, 16),
                arrowprops=dict(arrowstyle='->', color='#333', lw=3))
    ax.text(48, 22, '7. Store Mapping Data', fontsize=18, ha='center')

    # 8. Database insert notation
    ax.annotate('', xy=(85, 44), xytext=(85, 55),
                arrowprops=dict(arrowstyle='->', color='#333', lw=3))
    ax.text(87, 50, '8. INSERT', fontsize=18, va='center')

    # Legend box
    draw_box(ax, 70, 5, 28, 14, '', '#F5F5F5', '#757575', fontsize=16)
    ax.text(84, 17, 'Legend', fontsize=20, fontweight='bold', ha='center')
    ax.text(72, 14, 'UI Components', fontsize=16, color=COLORS['blue_dark'])
    ax.text(72, 11, 'Services', fontsize=16, color='#F57C00')
    ax.text(72, 8, 'Data Storage', fontsize=16, color='#3F51B5')

    save_figure(fig, 'Mapping_Capture_Flow')

if __name__ == '__main__':
    main()

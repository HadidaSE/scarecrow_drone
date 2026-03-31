"""
Convert ASCII architecture diagram to a professional PNG image.
Uses matplotlib and patches to create clean diagram boxes.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

def create_architecture_diagram():
    # Create figure with white background
    fig, ax = plt.subplots(1, 1, figsize=(16, 22))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 140)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor('white')

    # Colors
    client_color = '#E3F2FD'  # Light blue
    server_color = '#E8F5E9'  # Light green
    drone_color = '#FFF3E0'   # Light orange
    component_color = '#FFFFFF'  # White
    header_color = '#90CAF9'  # Blue header
    header_green = '#A5D6A7'  # Green header
    header_orange = '#FFCC80' # Orange header

    # ==================== CLIENT MACHINE ====================
    # Main client box
    client_box = FancyBboxPatch((2, 122), 96, 16, boxstyle="round,pad=0.02,rounding_size=0.5",
                                 facecolor=client_color, edgecolor='#1976D2', linewidth=2)
    ax.add_patch(client_box)
    ax.text(50, 136.5, 'Client Machine', fontsize=12, fontweight='bold', ha='center', va='center')

    # Web Browser box
    browser_box = FancyBboxPatch((4, 123.5), 92, 12, boxstyle="round,pad=0.02,rounding_size=0.3",
                                  facecolor=component_color, edgecolor='#42A5F5', linewidth=1.5)
    ax.add_patch(browser_box)
    ax.text(50, 134, 'Web Browser', fontsize=10, fontweight='bold', ha='center', va='center')

    # React Frontend box
    react_box = FancyBboxPatch((6, 124.5), 88, 8, boxstyle="round,pad=0.02,rounding_size=0.3",
                                facecolor='#BBDEFB', edgecolor='#1E88E5', linewidth=1)
    ax.add_patch(react_box)
    ax.text(50, 131.5, 'React Frontend (Port 5173)', fontsize=9, fontweight='bold', ha='center', va='center')

    # Frontend components
    components = [('Dashboard\nPage', 20), ('Flight\nHistory', 50), ('Detection\nGallery', 80)]
    for name, x in components:
        comp_box = FancyBboxPatch((x-12, 125.5), 24, 5, boxstyle="round,pad=0.02,rounding_size=0.2",
                                   facecolor=component_color, edgecolor='#64B5F6', linewidth=1)
        ax.add_patch(comp_box)
        ax.text(x, 128, name, fontsize=8, ha='center', va='center')

    # Arrow from Client to Server
    ax.annotate('', xy=(50, 82), xytext=(50, 122),
                arrowprops=dict(arrowstyle='->', color='#555555', lw=2))
    ax.text(56, 102, 'HTTP/REST', fontsize=9, ha='left', va='center', style='italic')

    # ==================== GROUND STATION ====================
    # Main server box
    server_box = FancyBboxPatch((2, 30), 96, 52, boxstyle="round,pad=0.02,rounding_size=0.5",
                                 facecolor=server_color, edgecolor='#388E3C', linewidth=2)
    ax.add_patch(server_box)
    ax.text(50, 80.5, 'Ground Station (Server Machine)', fontsize=12, fontweight='bold', ha='center', va='center')

    # FastAPI Backend box
    fastapi_box = FancyBboxPatch((4, 55), 92, 24, boxstyle="round,pad=0.02,rounding_size=0.3",
                                  facecolor=component_color, edgecolor='#66BB6A', linewidth=1.5)
    ax.add_patch(fastapi_box)
    ax.text(50, 77.5, 'FastAPI Backend (Port 5000)', fontsize=10, fontweight='bold', ha='center', va='center')

    # Controllers section
    ctrl_box = FancyBboxPatch((6, 70), 88, 7, boxstyle="round,pad=0.02,rounding_size=0.2",
                               facecolor='#C8E6C9', edgecolor='#4CAF50', linewidth=1)
    ax.add_patch(ctrl_box)
    ax.text(50, 75.5, 'Controllers', fontsize=9, fontweight='bold', ha='center', va='center')

    controllers = [('Drone\nController', 20), ('Flight\nController', 50), ('Connection\nController', 80)]
    for name, x in controllers:
        comp_box = FancyBboxPatch((x-12, 70.5), 24, 5, boxstyle="round,pad=0.02,rounding_size=0.2",
                                   facecolor=component_color, edgecolor='#81C784', linewidth=1)
        ax.add_patch(comp_box)
        ax.text(x, 73, name, fontsize=7, ha='center', va='center')

    # Services section
    svc_box = FancyBboxPatch((6, 62), 88, 7, boxstyle="round,pad=0.02,rounding_size=0.2",
                              facecolor='#C8E6C9', edgecolor='#4CAF50', linewidth=1)
    ax.add_patch(svc_box)
    ax.text(50, 67.5, 'Services', fontsize=9, fontweight='bold', ha='center', va='center')

    services = [('Drone\nService', 20), ('Flight\nService', 50), ('Detection\nService', 80)]
    for name, x in services:
        comp_box = FancyBboxPatch((x-12, 62.5), 24, 5, boxstyle="round,pad=0.02,rounding_size=0.2",
                                   facecolor=component_color, edgecolor='#81C784', linewidth=1)
        ax.add_patch(comp_box)
        ax.text(x, 65, name, fontsize=7, ha='center', va='center')

    # Repositories section
    repo_box = FancyBboxPatch((6, 55.5), 88, 6, boxstyle="round,pad=0.02,rounding_size=0.2",
                               facecolor='#C8E6C9', edgecolor='#4CAF50', linewidth=1)
    ax.add_patch(repo_box)
    ax.text(50, 60, 'Repositories', fontsize=9, fontweight='bold', ha='center', va='center')

    repos = [('Drone\nRepository', 30), ('Flight\nRepository', 70)]
    for name, x in repos:
        comp_box = FancyBboxPatch((x-12, 56), 24, 4, boxstyle="round,pad=0.02,rounding_size=0.2",
                                   facecolor=component_color, edgecolor='#81C784', linewidth=1)
        ax.add_patch(comp_box)
        ax.text(x, 58, name, fontsize=7, ha='center', va='center')

    # SQLite Database
    db_box = FancyBboxPatch((30, 49), 40, 5, boxstyle="round,pad=0.02,rounding_size=0.2",
                             facecolor='#DCEDC8', edgecolor='#7CB342', linewidth=1.5)
    ax.add_patch(db_box)
    ax.text(50, 51.5, 'SQLite Database', fontsize=9, fontweight='bold', ha='center', va='center')

    # Detection Module
    detect_box = FancyBboxPatch((4, 39), 45, 9, boxstyle="round,pad=0.02,rounding_size=0.3",
                                 facecolor=component_color, edgecolor='#66BB6A', linewidth=1.5)
    ax.add_patch(detect_box)
    ax.text(26.5, 46.5, 'Detection Module (detect.py)', fontsize=9, fontweight='bold', ha='center', va='center')

    detect_comps = [('FFmpeg\nDecoder', 12), ('YOLO\nModel', 26.5), ('OpenCV\nProcessing', 41)]
    for name, x in detect_comps:
        comp_box = FancyBboxPatch((x-6, 40), 12, 5, boxstyle="round,pad=0.02,rounding_size=0.2",
                                   facecolor='#E8F5E9', edgecolor='#81C784', linewidth=1)
        ax.add_patch(comp_box)
        ax.text(x, 42.5, name, fontsize=6, ha='center', va='center')

    # File Storage
    storage_box = FancyBboxPatch((51, 39), 45, 9, boxstyle="round,pad=0.02,rounding_size=0.3",
                                  facecolor=component_color, edgecolor='#66BB6A', linewidth=1.5)
    ax.add_patch(storage_box)
    ax.text(73.5, 46.5, 'File Storage', fontsize=9, fontweight='bold', ha='center', va='center')

    storage_comps = [('recordings/\n(Video files)', 62), ('detection_images/\n(Annotated frames)', 84)]
    for name, x in storage_comps:
        comp_box = FancyBboxPatch((x-9, 40), 18, 5, boxstyle="round,pad=0.02,rounding_size=0.2",
                                   facecolor='#E8F5E9', edgecolor='#81C784', linewidth=1)
        ax.add_patch(comp_box)
        ax.text(x, 42.5, name, fontsize=6, ha='center', va='center')

    # Arrows from Server to Drone
    # Left arrow (MAVLink)
    ax.annotate('', xy=(25, 2), xytext=(25, 30),
                arrowprops=dict(arrowstyle='->', color='#555555', lw=2))
    ax.text(5, 16, 'MAVLink Commands\n(Flight control, waypoints,\narm/disarm, mode changes)',
            fontsize=7, ha='left', va='center', style='italic')

    # Right arrow (Video Stream)
    ax.annotate('', xy=(75, 30), xytext=(75, 2),
                arrowprops=dict(arrowstyle='->', color='#555555', lw=2))
    ax.text(77, 16, 'RTP/UDP Video Stream\n(GStreamer JPEG @ 5000)',
            fontsize=7, ha='left', va='center', style='italic')

    # ==================== DRONE ====================
    # Main drone box - positioned at bottom, y from -38 to 0
    drone_box = FancyBboxPatch((2, -38), 96, 38, boxstyle="round,pad=0.02,rounding_size=0.5",
                                facecolor=drone_color, edgecolor='#F57C00', linewidth=2)
    ax.add_patch(drone_box)
    ax.text(50, -1.5, 'Drone (Airborne Unit)', fontsize=12, fontweight='bold', ha='center', va='center')

    # Flight Controller box
    fc_box = FancyBboxPatch((4, -13), 92, 10, boxstyle="round,pad=0.02,rounding_size=0.3",
                             facecolor=component_color, edgecolor='#FFA726', linewidth=1.5)
    ax.add_patch(fc_box)
    ax.text(50, -4.5, 'Flight Controller (Pixhawk)', fontsize=10, fontweight='bold', ha='center', va='center')

    # ArduPilot box
    ardu_box = FancyBboxPatch((6, -12), 88, 7, boxstyle="round,pad=0.02,rounding_size=0.2",
                               facecolor='#FFE0B2', edgecolor='#FF9800', linewidth=1)
    ax.add_patch(ardu_box)
    ax.text(50, -6.5, 'ArduPilot Firmware', fontsize=9, fontweight='bold', ha='center', va='center')

    ardu_comps = [('MAVLink\nProtocol', 30), ('IMU / Sensors\n(Altitude, Attitude)', 70)]
    for name, x in ardu_comps:
        comp_box = FancyBboxPatch((x-15, -11.5), 30, 4, boxstyle="round,pad=0.02,rounding_size=0.2",
                                   facecolor=component_color, edgecolor='#FFCC80', linewidth=1)
        ax.add_patch(comp_box)
        ax.text(x, -9.5, name, fontsize=7, ha='center', va='center')

    # Companion Computer box
    comp_box_main = FancyBboxPatch((4, -24), 92, 10, boxstyle="round,pad=0.02,rounding_size=0.3",
                                    facecolor=component_color, edgecolor='#FFA726', linewidth=1.5)
    ax.add_patch(comp_box_main)
    ax.text(50, -15.5, 'Companion Computer', fontsize=10, fontweight='bold', ha='center', va='center')

    companion_comps = [('GStreamer\nEncoder', 20), ('Camera\nInterface', 50), ('WiFi / Telemetry\nRadio Link', 80)]
    for name, x in companion_comps:
        comp_box = FancyBboxPatch((x-12, -23), 24, 6, boxstyle="round,pad=0.02,rounding_size=0.2",
                                   facecolor='#FFE0B2', edgecolor='#FFCC80', linewidth=1)
        ax.add_patch(comp_box)
        ax.text(x, -20, name, fontsize=7, ha='center', va='center')

    # Hardware Components box
    hw_box = FancyBboxPatch((4, -37), 92, 12, boxstyle="round,pad=0.02,rounding_size=0.3",
                             facecolor=component_color, edgecolor='#FFA726', linewidth=1.5)
    ax.add_patch(hw_box)
    ax.text(50, -26.5, 'Hardware Components', fontsize=10, fontweight='bold', ha='center', va='center')

    hw_comps = [('Camera\n(640x480)', 15), ('Motors\n(x4/x6)', 38), ('Battery\n(LiPo 4S)', 62), ('Speaker\n(Deterrent)', 85)]
    for name, x in hw_comps:
        comp_box = FancyBboxPatch((x-10, -36), 20, 7, boxstyle="round,pad=0.02,rounding_size=0.2",
                                   facecolor='#FFE0B2', edgecolor='#FFCC80', linewidth=1)
        ax.add_patch(comp_box)
        ax.text(x, -32.5, name, fontsize=7, ha='center', va='center')

    # Adjust y limits to show drone section
    ax.set_ylim(-42, 142)

    # Save the figure
    plt.tight_layout()
    plt.savefig('architecture_diagram.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print("Saved: architecture_diagram.png")

    # Also save as high-res for printing
    plt.savefig('architecture_diagram_hires.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print("Saved: architecture_diagram_hires.png (high resolution)")

    plt.close()

if __name__ == '__main__':
    create_architecture_diagram()

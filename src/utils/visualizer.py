"""
Mesh Visualizer
3D visualization of blockMeshDict using matplotlib
"""

# Set matplotlib backend before importing pyplot
import matplotlib
matplotlib.use('QtAgg')  # Use Qt backend for PyQt6

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from typing import List, Tuple, Dict

from ..core.mesh_data import MeshConfig, BoundaryType, Segment
from ..core.generator import BlockMeshDictGenerator


class MeshVisualizerWidget(FigureCanvas):
    """
    Matplotlib figure embedded in Qt widget for 3D mesh visualization
    Shows the overall mesh outline with segment markers and cell counts
    """
    
    # Boundary face colors
    BOUNDARY_COLORS = {
        'xMin': '#FF6B6B',   # Red
        'xMax': '#4ECDC4',   # Teal
        'yMin': '#FFE66D',   # Yellow
        'yMax': '#95E1D3',   # Light green
        'zMin': '#DDA0DD',   # Plum
        'zMax': '#87CEEB',   # Sky blue
    }
    
    def __init__(self, config: MeshConfig, parent=None):
        # Create figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        super().__init__(self.fig)
        self.setParent(parent)
        
        self.config = config
        
        # Draw the mesh outline
        self._draw_mesh_outline()
        
        # Set initial view (show front-bottom-left corner)
        self.ax.view_init(elev=25, azim=45)
        
        self.fig.tight_layout()
    
    def _draw_mesh_outline(self):
        """Draw the overall mesh outline - domain boundary only"""
        # Draw the outer boundary box edges
        self._draw_domain_edges()
        
        # Draw boundary faces (semi-transparent colored surfaces)
        self._draw_boundary_faces()
        
        # Draw segment markers on visible edges
        self._draw_segment_markers()
        
        # Set axis labels and limits
        self._setup_axes()
    
    def _draw_domain_edges(self):
        """Draw the 12 edges of the domain box"""
        x_min, x_max = self.config.x_min, self.config.x_max
        y_min, y_max = self.config.y_min, self.config.y_max
        z_min, z_max = self.config.z_min, self.config.z_max
        
        vertices = [
            (x_min, y_min, z_min),  # 0 - origin corner
            (x_max, y_min, z_min),  # 1
            (x_max, y_max, z_min),  # 2
            (x_min, y_max, z_min),  # 3
            (x_min, y_min, z_max),  # 4
            (x_max, y_min, z_max),  # 5
            (x_max, y_max, z_max),  # 6
            (x_min, y_max, z_max),  # 7
        ]
        
        # 12 edges
        edge_pairs = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom
            (4, 5), (5, 6), (6, 7), (7, 4),  # Top
            (0, 4), (1, 5), (2, 6), (3, 7),  # Vertical
        ]
        
        for i, j in edge_pairs:
            v1 = vertices[i]
            v2 = vertices[j]
            self.ax.plot3D(
                [v1[0], v2[0]],
                [v1[1], v2[1]],
                [v1[2], v2[2]],
                'k-', linewidth=2, alpha=0.8
            )
    
    def _draw_boundary_faces(self):
        """Draw boundary faces as semi-transparent colored surfaces"""
        x_min, x_max = self.config.x_min, self.config.x_max
        y_min, y_max = self.config.y_min, self.config.y_max
        z_min, z_max = self.config.z_min, self.config.z_max
        
        faces = {
            'xMin': [(x_min, y_min, z_min), (x_min, y_max, z_min), 
                     (x_min, y_max, z_max), (x_min, y_min, z_max)],
            'xMax': [(x_max, y_min, z_min), (x_max, y_min, z_max),
                     (x_max, y_max, z_max), (x_max, y_max, z_min)],
            'yMin': [(x_min, y_min, z_min), (x_max, y_min, z_min),
                     (x_max, y_min, z_max), (x_min, y_min, z_max)],
            'yMax': [(x_min, y_max, z_min), (x_min, y_max, z_max),
                     (x_max, y_max, z_max), (x_max, y_max, z_min)],
            'zMin': [(x_min, y_min, z_min), (x_min, y_max, z_min),
                     (x_max, y_max, z_min), (x_max, y_min, z_min)],
            'zMax': [(x_min, y_min, z_max), (x_max, y_min, z_max),
                     (x_max, y_max, z_max), (x_min, y_max, z_max)],
        }
        
        for boundary_name, verts in faces.items():
            color = self.BOUNDARY_COLORS.get(boundary_name, '#CCCCCC')
            
            poly = Poly3DCollection([verts], alpha=0.2)
            poly.set_facecolor(color)
            poly.set_edgecolor('k')
            poly.set_linewidth(1.5)
            self.ax.add_collection3d(poly)
    
    def _draw_segment_markers(self):
        """
        Draw segment markers on visible edges (3 edges from origin corner)
        Show segment boundaries and cell counts
        """
        x_min, x_max = self.config.x_min, self.config.x_max
        y_min, y_max = self.config.y_min, self.config.y_max
        z_min, z_max = self.config.z_min, self.config.z_max
        
        # Visible edges from origin corner (xMin, yMin, zMin)
        # Edge 0->1: X direction along yMin, zMin
        # Edge 0->3: Y direction along xMin, zMin  
        # Edge 0->4: Z direction along xMin, yMin
        
        # X direction edge
        if self.config.use_x_segments and self.config.x_segments:
            self._draw_edge_segments(
                x_min, x_max, y_min, z_min,
                self.config.x_segments,
                'x', axis_direction='x'
            )
        
        # Y direction edge
        if self.config.use_y_segments and self.config.y_segments:
            self._draw_edge_segments(
                y_min, y_max, x_min, z_min,
                self.config.y_segments,
                'y', axis_direction='y'
            )
        
        # Z direction edge
        if self.config.use_z_segments and self.config.z_segments:
            self._draw_edge_segments(
                z_min, z_max, x_min, y_min,
                self.config.z_segments,
                'z', axis_direction='z'
            )
    
    def _draw_edge_segments(self, start_val: float, end_val: float,
                            fixed1: float, fixed2: float,
                            segments: List[Segment],
                            label_axis: str, axis_direction: str):
        """
        Draw segment markers and cell count labels on one edge
        
        Args:
            start_val: Starting coordinate value for the varying axis
            end_val: Ending coordinate value
            fixed1, fixed2: Fixed coordinate values for other two axes
            segments: List of Segment objects
            label_axis: Which axis this edge represents ('x', 'y', or 'z')
            axis_direction: Direction of the edge in 3D space
        """
        # Calculate segment positions
        positions = [start_val]
        for seg in segments:
            positions.append(positions[-1] + seg.length)
        
        # Draw segment boundary markers (small dots at segment boundaries)
        for pos in positions:
            if axis_direction == 'x':
                self.ax.scatter([pos], [fixed1], [fixed2], 
                               c='red', s=50, marker='o', alpha=0.8)
            elif axis_direction == 'y':
                self.ax.scatter([fixed1], [pos], [fixed2],
                               c='green', s=50, marker='o', alpha=0.8)
            elif axis_direction == 'z':
                self.ax.scatter([fixed1], [fixed2], [pos],
                               c='blue', s=50, marker='o', alpha=0.8)
        
        # Draw cell count labels between segment boundaries
        for i, seg in enumerate(segments):
            # Calculate midpoint of this segment
            mid = (positions[i] + positions[i + 1]) / 2
            
            # Create label text
            label_text = f"{seg.n_cells}"
            
            # Position the label
            if axis_direction == 'x':
                self.ax.text(mid, fixed1, fixed2, label_text,
                            fontsize=9, ha='center', va='bottom',
                            color='red', weight='bold')
            elif axis_direction == 'y':
                self.ax.text(fixed1, mid, fixed2, label_text,
                            fontsize=9, ha='center', va='bottom',
                            color='green', weight='bold')
            elif axis_direction == 'z':
                self.ax.text(fixed1, fixed2, mid, label_text,
                            fontsize=9, ha='center', va='bottom',
                            color='blue', weight='bold')
    
    def _setup_axes(self):
        """Setup axis labels and limits"""
        self.ax.set_xlabel('X', fontsize=10)
        self.ax.set_ylabel('Y', fontsize=10)
        self.ax.set_zlabel('Z', fontsize=10)
        
        x_min, x_max = self.config.x_min, self.config.x_max
        y_min, y_max = self.config.y_min, self.config.y_max
        z_min, z_max = self.config.z_min, self.config.z_max
        
        x_range = x_max - x_min
        y_range = y_max - y_min
        z_range = z_max - z_min
        
        max_range = max(x_range, y_range, z_range) / 2
        
        x_mid = (x_max + x_min) / 2
        y_mid = (y_max + y_min) / 2
        z_mid = (z_max + z_min) / 2
        
        self.ax.set_xlim(x_mid - max_range, x_mid + max_range)
        self.ax.set_ylim(y_mid - max_range, y_mid + max_range)
        self.ax.set_zlim(z_mid - max_range, z_mid + max_range)
        
        domain_text = f"Domain: X[{x_min:.1f}, {x_max:.1f}]  Y[{y_min:.1f}, {y_max:.1f}]  Z[{z_min:.1f}, {z_max:.1f}]"
        self.ax.set_title(domain_text, fontsize=10, pad=10)
        
        self.fig.tight_layout()


class MeshPreviewDialog:
    """Factory to create preview widget"""
    
    @staticmethod
    def create_preview_widget(config: MeshConfig, parent=None):
        try:
            return MeshVisualizerWidget(config, parent)
        except Exception as e:
            print(f"Visualization failed: {e}")
            return None
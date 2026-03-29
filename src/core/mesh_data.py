"""
Mesh Data Model
Defines data structures for blockMeshDict generation
Supports single block and multi-segment mesh configurations
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum


class BoundaryType(Enum):
    """OpenFOAM boundary types
    
    Common types:
    - wall: No-slip wall boundary
    - patch: Generic boundary for fixed value or zero gradient
    - symmetryPlane: Symmetry plane
    - empty: For 2D cases (front/back faces)
    - wedge: Axisymmetric boundary
    
    Special types:
    - cyclic: Periodic boundary
    - cyclicAMI: Cyclic with arbitrary mesh interface
    - symmetry: Symmetry plane (alternative)
    - processor: Processor boundary for parallel runs
    """
    # Common types
    WALL = "wall"
    PATCH = "patch"
    SYMMETRY_PLANE = "symmetryPlane"
    EMPTY = "empty"
    WEDGE = "wedge"
    
    # Alternative symmetry
    SYMMETRY = "symmetry"
    
    # Periodic / Cyclic
    CYCLIC = "cyclic"
    CYCLIC_AMI = "cyclicAMI"
    
    # Parallel
    PROCESSOR = "processor"
    PROCESSOR_CYCLIC = "processorCyclic"
    
    # Others
    CALCULATED = "calculated"
    EXTERNAL_WALL = "externalWall"
    MIXED = "mixed"


@dataclass
class Boundary:
    """Represents a single boundary face"""
    name: str
    boundary_type: BoundaryType
    faces: List[Tuple[int, int, int, int]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Boundary name cannot be empty")


@dataclass
class Segment:
    """
    Represents a mesh segment in one direction
    
    Used for multi-block mesh with varying density
    """
    name: str  # Segment name (e.g., "inlet", "simulation", "outlet")
    length: float  # Length of this segment
    n_cells: int  # Number of cells in this segment
    grading: float = 1.0  # Cell size grading within segment
    
    def __post_init__(self):
        if self.n_cells < 1:
            raise ValueError(f"Segment {self.name}: n_cells must be >= 1")
        if self.length <= 0:
            raise ValueError(f"Segment {self.name}: length must be > 0")


@dataclass 
class MeshConfig:
    """
    Complete configuration for a hexahedral mesh
    
    Supports:
    1. Single block (default): Simple uniform mesh
    2. Multi-direction segmented: Multi-block mesh with segments in X/Y/Z
    
    When multiple directions have segments, blocks are generated as
    the Cartesian product of all segment combinations.
    Example: X:2 * Y:2 * Z:2 = 8 blocks
    """
    # Domain bounds
    x_min: float = 0.0
    x_max: float = 1.0
    y_min: float = 0.0
    y_max: float = 1.0
    z_min: float = 0.0
    z_max: float = 1.0
    
    # Cell counts (for single block mode)
    n_x: int = 20
    n_y: int = 20
    n_z: int = 20
    
    # Grading (simpleGrading for single block)
    grading_x: float = 1.0
    grading_y: float = 1.0
    grading_z: float = 1.0
    
    # Scale factor
    scale: float = 1.0
    
    # Boundaries
    boundaries: List[Boundary] = field(default_factory=list)
    
    # Segmented mode - support for all three directions
    use_x_segments: bool = False
    use_y_segments: bool = False
    use_z_segments: bool = False
    
    x_segments: List[Segment] = field(default_factory=list)
    y_segments: List[Segment] = field(default_factory=list)
    z_segments: List[Segment] = field(default_factory=list)
    
    # Custom boundary names (for segmented mesh)
    # Maps default name -> custom name
    # Example: {"xMin": "inlet", "xMax": "outlet"}
    boundary_names: dict = field(default_factory=dict)
    
    # Custom boundary types (for segmented mesh)
    # Maps default name -> boundary type
    boundary_types: dict = field(default_factory=dict)
    
    def __post_init__(self):
        # Check if any direction has segments
        has_any_segments = self.use_x_segments or self.use_y_segments or self.use_z_segments
        
        if has_any_segments and not self.x_segments and not self.y_segments and not self.z_segments:
            # Try to infer from legacy format
            if self.x_segments and not self.use_x_segments:
                self.use_x_segments = True
        
        if self.use_x_segments or self.use_y_segments or self.use_z_segments:
            self._validate_segments()
        else:
            self.validate()
        
        if not self.boundaries:
            self._create_default_boundaries()
    
    @property
    def use_segments(self) -> bool:
        """Check if any direction uses segments"""
        return self.use_x_segments or self.use_y_segments or self.use_z_segments
    
    def validate(self):
        """Validate mesh configuration for single block mode"""
        if self.x_min >= self.x_max:
            raise ValueError(f"x_min ({self.x_min}) must be less than x_max ({self.x_max})")
        if self.y_min >= self.y_max:
            raise ValueError(f"y_min ({self.y_min}) must be less than y_max ({self.y_max})")
        if self.z_min >= self.z_max:
            raise ValueError(f"z_min ({self.z_min}) must be less than z_max ({self.z_max})")
        
        if self.n_x < 1 or self.n_y < 1 or self.n_z < 1:
            raise ValueError("Cell counts must be positive integers")
        
        if self.scale <= 0:
            raise ValueError("Scale must be positive")
    
    def _validate_segments(self):
        """Validate segment configuration for all directions"""
        # Validate X segments if enabled
        if self.use_x_segments:
            if not self.x_segments:
                raise ValueError("use_x_segments=True requires x_segments to be defined")
            if len(self.x_segments) < 1:
                raise ValueError("At least one X segment required")
            for seg in self.x_segments:
                if seg.n_cells < 1:
                    raise ValueError(f"X Segment '{seg.name}' needs at least 1 cell")
                if seg.length <= 0:
                    raise ValueError(f"X Segment '{seg.name}' length must be positive")
        
        # Validate Y segments if enabled
        if self.use_y_segments:
            if not self.y_segments:
                raise ValueError("use_y_segments=True requires y_segments to be defined")
            if len(self.y_segments) < 1:
                raise ValueError("At least one Y segment required")
            for seg in self.y_segments:
                if seg.n_cells < 1:
                    raise ValueError(f"Y Segment '{seg.name}' needs at least 1 cell")
                if seg.length <= 0:
                    raise ValueError(f"Y Segment '{seg.name}' length must be positive")
        
        # Validate Z segments if enabled
        if self.use_z_segments:
            if not self.z_segments:
                raise ValueError("use_z_segments=True requires z_segments to be defined")
            if len(self.z_segments) < 1:
                raise ValueError("At least one Z segment required")
            for seg in self.z_segments:
                if seg.n_cells < 1:
                    raise ValueError(f"Z Segment '{seg.name}' needs at least 1 cell")
                if seg.length <= 0:
                    raise ValueError(f"Z Segment '{seg.name}' length must be positive")
    
    def _compute_bounds_from_segments(self):
        """Compute bounds and cell counts from segments"""
        # X direction
        if self.use_x_segments and self.x_segments:
            self.x_min = 0.0
            self.x_max = sum(seg.length for seg in self.x_segments)
            self.n_x = sum(seg.n_cells for seg in self.x_segments)
        
        # Y direction
        if self.use_y_segments and self.y_segments:
            self.y_min = 0.0
            self.y_max = sum(seg.length for seg in self.y_segments)
            self.n_y = sum(seg.n_cells for seg in self.y_segments)
        
        # Z direction
        if self.use_z_segments and self.z_segments:
            self.z_min = 0.0
            self.z_max = sum(seg.length for seg in self.z_segments)
            self.n_z = sum(seg.n_cells for seg in self.z_segments)
    
    def _create_default_boundaries(self):
        """Create default boundary definitions"""
        if self.use_segments:
            # For segmented mesh, create boundaries for each segment
            self._create_segmented_boundaries()
        else:
            # Standard 6 boundaries for single block
            self.boundaries = [
                Boundary("xMin", BoundaryType.WALL, [(0, 4, 7, 3)]),
                Boundary("xMax", BoundaryType.WALL, [(2, 6, 5, 1)]),
                Boundary("yMin", BoundaryType.WALL, [(1, 5, 4, 0)]),
                Boundary("yMax", BoundaryType.WALL, [(3, 7, 6, 2)]),
                Boundary("zMin", BoundaryType.WALL, [(0, 3, 2, 1)]),
                Boundary("zMax", BoundaryType.WALL, [(4, 5, 6, 7)]),
            ]
    
    def _create_segmented_boundaries(self):
        """Create boundaries for segmented mesh"""
        # Will be computed based on actual vertices
        # For now, placeholder - generator will handle this
        self.boundaries = []
    
    @property
    def total_x_length(self) -> float:
        """Total length in X direction"""
        if self.use_segments:
            return sum(seg.length for seg in self.x_segments)
        return self.x_max - self.x_min
    
    @property
    def total_x_cells(self) -> int:
        """Total cells in X direction"""
        if self.use_segments:
            return sum(seg.n_cells for seg in self.x_segments)
        return self.n_x
    
    @property
    def is_single_block(self) -> bool:
        """Check if using single block mode"""
        return not self.use_segments
    
    def update_boundary_type(self, boundary_name: str, new_type: BoundaryType):
        """Update boundary type by name"""
        for boundary in self.boundaries:
            if boundary.name == boundary_name:
                boundary.boundary_type = new_type
                return
        raise ValueError(f"Boundary '{boundary_name}' not found")
    
    def update_boundary_name(self, old_name: str, new_name: str):
        """Rename a boundary"""
        for boundary in self.boundaries:
            if boundary.name == old_name:
                boundary.name = new_name
                return
        raise ValueError(f"Boundary '{old_name}' not found")


def create_segmented_mesh(
    segments: List[Tuple[str, float, int]],  # (name, length, n_cells)
    y_min: float = 0.0, y_max: float = 1.0,
    z_min: float = 0.0, z_max: float = 1.0,
    n_y: int = 20, n_z: int = 20,
    scale: float = 1.0
) -> MeshConfig:
    """
    Convenience function to create a segmented mesh
    
    Args:
        segments: List of (name, length, n_cells) tuples
        y_min, y_max: Y direction bounds
        z_min, z_max: Z direction bounds
        n_y, n_z: Cell counts in Y and Z directions
        scale: Scale factor
    
    Returns:
        MeshConfig with segmented mesh
    
    Example:
        config = create_segmented_mesh([
            ("inlet", 2.0, 30),      # Inlet section: 2m, 30 cells (dense)
            ("simulation", 5.0, 50), # Simulation section: 5m, 50 cells
            ("outlet", 3.0, 20),     # Outlet section: 3m, 20 cells (coarse)
        ])
    """
    x_segments = [
        Segment(name=name, length=length, n_cells=n_cells)
        for name, length, n_cells in segments
    ]
    
    config = MeshConfig(
        y_min=y_min, y_max=y_max,
        z_min=z_min, z_max=z_max,
        n_y=n_y, n_z=n_z,
        scale=scale,
        use_segments=True,
        x_segments=x_segments,
    )
    
    return config


def create_cavity_mesh(x_max: float = 0.1, y_max: float = 0.1, z_max: float = 0.01,
                       n_x: int = 20, n_y: int = 20, n_z: int = 1) -> MeshConfig:
    """Create a cavity-like mesh (lid-driven cavity)"""
    config = MeshConfig(
        x_min=0, x_max=x_max,
        y_min=0, y_max=y_max,
        z_min=0, z_max=z_max,
        n_x=n_x, n_y=n_y, n_z=n_z
    )
    config.boundaries = [
        Boundary("fixedWalls", BoundaryType.WALL, [
            (0, 4, 7, 3),  # xMin
            (2, 6, 5, 1),  # xMax
            (1, 5, 4, 0),  # yMin
            (0, 3, 2, 1),  # zMin
            (4, 5, 6, 7),  # zMax
        ]),
        Boundary("movingWall", BoundaryType.WALL, [
            (3, 7, 6, 2),  # yMax (lid)
        ]),
    ]
    return config


def create_channel_mesh(length: float = 5.0, height: float = 1.0, width: float = 0.5,
                        n_x: int = 50, n_y: int = 20, n_z: int = 1) -> MeshConfig:
    """Create a channel flow mesh"""
    config = MeshConfig(
        x_min=0, x_max=length,
        y_min=0, y_max=height,
        z_min=0, z_max=width,
        n_x=n_x, n_y=n_y, n_z=n_z
    )
    config.boundaries = [
        Boundary("inlet", BoundaryType.PATCH, [(0, 4, 7, 3)]),
        Boundary("outlet", BoundaryType.PATCH, [(2, 6, 5, 1)]),
        Boundary("bottom", BoundaryType.WALL, [(1, 5, 4, 0)]),
        Boundary("top", BoundaryType.WALL, [(3, 7, 6, 2)]),
        Boundary("front", BoundaryType.EMPTY, [(0, 3, 2, 1)]),
        Boundary("back", BoundaryType.EMPTY, [(4, 5, 6, 7)]),
    ]
    return config
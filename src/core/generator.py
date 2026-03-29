"""
blockMeshDict Generator
Generates OpenFOAM blockMeshDict files from MeshConfig
Supports single block and multi-segment mesh configurations
"""

from pathlib import Path
from typing import Union, List, Tuple, Optional
from .mesh_data import MeshConfig, Boundary, BoundaryType, Segment


class BlockMeshDictGenerator:
    """Generates blockMeshDict files"""
    
    HEADER = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  auto-generated                       |
|   \\  /    A nd           |                                                 |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

scale   {scale};

"""
    
    FOOTER = """
// ************************************************************************* //
"""
    
    def __init__(self, config: MeshConfig):
        self.config = config
    
    def generate(self) -> str:
        """Generate complete blockMeshDict content"""
        lines = []
        
        # Header with scale
        lines.append(self.HEADER.format(scale=self.config.scale))
        
        if self.config.use_segments:
            # Multi-block generation
            lines.append(self._generate_segmented_mesh())
        else:
            # Single block generation
            lines.append(self._generate_single_block())
        
        # Footer
        lines.append(self.FOOTER)
        
        return "\n".join(lines)
    
    def _generate_single_block(self) -> str:
        """Generate single block mesh"""
        parts = []
        
        # Vertices section
        parts.append(self._generate_vertices())
        parts.append("")
        
        # Blocks section
        parts.append(self._generate_blocks())
        parts.append("")
        
        # Edges section
        parts.append(self._generate_edges())
        parts.append("")
        
        # Boundary section
        parts.append(self._generate_boundary())
        
        return "\n".join(parts)
    
    def _generate_segmented_mesh(self) -> str:
        """Generate multi-block segmented mesh"""
        parts = []
        
        # Compute all vertices for all blocks
        vertices, block_defs = self._compute_segmented_geometry()
        
        # Vertices section
        parts.append(self._generate_vertices_list(vertices))
        parts.append("")
        
        # Blocks section
        parts.append(self._generate_segmented_blocks(block_defs))
        parts.append("")
        
        # Edges section
        parts.append(self._generate_edges())
        parts.append("")
        
        # Boundary section
        parts.append(self._generate_segmented_boundary(vertices, block_defs))
        
        return "\n".join(parts)
    
    def _compute_segmented_geometry(self) -> Tuple[List[Tuple[float, float, float]], List[dict]]:
        """
        Compute vertices and block definitions for multi-direction segmented mesh
        
        Supports segments in X, Y, and Z directions simultaneously.
        Blocks are generated as the Cartesian product of all segment combinations.
        
        Returns:
            (vertices, block_definitions)
        """
        vertices = []
        block_defs = []
        
        # Get segments for each direction (or create single segment)
        x_segs = self.config.x_segments if self.config.use_x_segments else [
            Segment("full", self.config.x_max - self.config.x_min, self.config.n_x, 1.0)
        ]
        y_segs = self.config.y_segments if self.config.use_y_segments else [
            Segment("full", self.config.y_max - self.config.y_min, self.config.n_y, 1.0)
        ]
        z_segs = self.config.z_segments if self.config.use_z_segments else [
            Segment("full", self.config.z_max - self.config.z_min, self.config.n_z, 1.0)
        ]
        
        # Compute cumulative positions for each direction
        x_positions = [0.0]
        for seg in x_segs:
            x_positions.append(x_positions[-1] + seg.length)
        
        y_positions = [0.0]
        for seg in y_segs:
            y_positions.append(y_positions[-1] + seg.length)
        
        z_positions = [0.0]
        for seg in z_segs:
            z_positions.append(z_positions[-1] + seg.length)
        
        # First, generate all unique vertices in a grid (shared between blocks)
        nx = len(x_segs)
        ny = len(y_segs)
        nz = len(z_segs)

        # Get domain minimums for offset
        # When using segments, vertices are computed relative to 0, so we need to add the domain min offset
        x_min_offset = self.config.x_min
        y_min_offset = self.config.y_min
        z_min_offset = self.config.z_min

        # Create a mapping from grid position to vertex index
        vertex_map = {}
        vertex_idx = 0
        for zi in range(nz + 1):
            for yi in range(ny + 1):
                for xi in range(nx + 1):
                    x = x_positions[xi] + x_min_offset
                    y = y_positions[yi] + y_min_offset
                    z = z_positions[zi] + z_min_offset
                    vertices.append((x, y, z))
                    vertex_map[(xi, yi, zi)] = vertex_idx
                    vertex_idx += 1
        
        # Generate blocks for all combinations
        block_idx = 0
        for xi, x_seg in enumerate(x_segs):
            for yi, y_seg in enumerate(y_segs):
                for zi, z_seg in enumerate(z_segs):
                    # Compute block bounds (with domain min offset)
                    x_start = x_positions[xi] + x_min_offset
                    x_end = x_positions[xi + 1] + x_min_offset
                    y_start = y_positions[yi] + y_min_offset
                    y_end = y_positions[yi + 1] + y_min_offset
                    z_start = z_positions[zi] + z_min_offset
                    z_end = z_positions[zi + 1] + z_min_offset
                    
                    # Get vertex indices for this block (using shared vertices)
                    # OpenFOAM hex vertex order:
                    # 0: min-min-min, 1: max-min-min, 2: max-max-min, 3: min-max-min
                    # 4: min-min-max, 5: max-min-max, 6: max-max-max, 7: min-max-max
                    v0 = vertex_map[(xi,   yi,   zi)]
                    v1 = vertex_map[(xi+1, yi,   zi)]
                    v2 = vertex_map[(xi+1, yi+1, zi)]
                    v3 = vertex_map[(xi,   yi+1, zi)]
                    v4 = vertex_map[(xi,   yi,   zi+1)]
                    v5 = vertex_map[(xi+1, yi,   zi+1)]
                    v6 = vertex_map[(xi+1, yi+1, zi+1)]
                    v7 = vertex_map[(xi,   yi+1, zi+1)]
                    
                    # Block definition
                    block_def = {
                        'name': f"{x_seg.name}_{y_seg.name}_{z_seg.name}",
                        'vertex_indices': [v0, v1, v2, v3, v4, v5, v6, v7],
                        'n_cells': (x_seg.n_cells, y_seg.n_cells, z_seg.n_cells),
                        'grading': (x_seg.grading, y_seg.grading, z_seg.grading),
                        'x_range': (x_start, x_end),
                        'y_range': (y_start, y_end),
                        'z_range': (z_start, z_end),
                        'block_index': block_idx,
                    }
                    block_defs.append(block_def)
                    block_idx += 1
        
        return vertices, block_defs
    
    def _generate_vertices_list(self, vertices: List[Tuple[float, float, float]]) -> str:
        """Generate vertices section from vertex list"""
        lines = ["vertices"]
        lines.append("(")
        
        for i, (x, y, z) in enumerate(vertices):
            lines.append(f"    ({x} {y} {z})  // {i}")
        
        lines.append(");")
        return "\n".join(lines)
    
    def _generate_segmented_blocks(self, block_defs: List[dict]) -> str:
        """Generate blocks section for segmented mesh"""
        lines = ["blocks"]
        lines.append("(")
        
        for block in block_defs:
            v = block['vertex_indices']
            nx, ny, nz = block['n_cells']
            gx, gy, gz = block['grading']
            
            # hex definition
            hex_def = f"hex ({v[0]} {v[1]} {v[2]} {v[3]} {v[4]} {v[5]} {v[6]} {v[7]})"
            cells_def = f"({nx} {ny} {nz})"
            grading_def = f"simpleGrading ({gx} {gy} {gz})"
            
            lines.append(f"    {hex_def} {cells_def} {grading_def}  // {block['name']}")
        
        lines.append(");")
        return "\n".join(lines)
    
    def _generate_segmented_boundary(self, vertices: List[Tuple[float, float, float]], 
                                      block_defs: List[dict]) -> str:
        """Generate boundary section for segmented mesh"""
        lines = ["boundary"]
        lines.append("(")
        
        # Collect boundary faces
        boundaries_to_add = []
        
        # If user provided custom boundaries, use them
        # Otherwise generate default boundaries
        
        n_segments = len(self.config.x_segments)
        
        # X-min boundary (only blocks with minimum X)
        x_min_faces = []
        for block in block_defs:
            if block['x_range'][0] == self.config.x_min:
                v = block['vertex_indices']
                # xMin face: vertices 0,4,7,3 (normal points in -X direction)
                x_min_faces.append((v[0], v[4], v[7], v[3]))
        
        x_min_name, x_min_type = self._get_boundary_name_and_type("xMin")
        boundaries_to_add.append({
            'name': x_min_name,
            'type': x_min_type,
            'faces': x_min_faces,
        })
        
        # X-max boundary (only blocks with maximum X)
        x_max_faces = []
        for block in block_defs:
            if block['x_range'][1] == self.config.x_max:
                v = block['vertex_indices']
                # xMax face: vertices 1,2,6,5 (normal points in +X direction)
                x_max_faces.append((v[1], v[2], v[6], v[5]))
        
        x_max_name, x_max_type = self._get_boundary_name_and_type("xMax")
        boundaries_to_add.append({
            'name': x_max_name,
            'type': x_max_type,
            'faces': x_max_faces,
        })
        
        # Y-min boundary (only blocks with minimum Y)
        y_min_faces = []
        for block in block_defs:
            if block['y_range'][0] == self.config.y_min:
                v = block['vertex_indices']
                # yMin face: vertices 0,1,5,4 (normal points in -Y direction)
                y_min_faces.append((v[0], v[1], v[5], v[4]))
        
        y_min_name, y_min_type = self._get_boundary_name_and_type("yMin")
        boundaries_to_add.append({
            'name': y_min_name,
            'type': y_min_type,
            'faces': y_min_faces,
        })
        
        # Y-max boundary (only blocks with maximum Y)
        y_max_faces = []
        for block in block_defs:
            if block['y_range'][1] == self.config.y_max:
                v = block['vertex_indices']
                # yMax face: vertices 2,3,7,6 (normal points in +Y direction)
                y_max_faces.append((v[2], v[3], v[7], v[6]))
        
        y_max_name, y_max_type = self._get_boundary_name_and_type("yMax")
        boundaries_to_add.append({
            'name': y_max_name,
            'type': y_max_type,
            'faces': y_max_faces,
        })
        
        # Z-min boundary (only blocks with minimum Z)
        z_min_faces = []
        for block in block_defs:
            if block['z_range'][0] == self.config.z_min:
                v = block['vertex_indices']
                # zMin face: vertices 0,3,2,1 (normal points in -Z direction)
                z_min_faces.append((v[0], v[3], v[2], v[1]))
        
        z_min_name, z_min_type = self._get_boundary_name_and_type("zMin")
        boundaries_to_add.append({
            'name': z_min_name,
            'type': z_min_type,
            'faces': z_min_faces,
        })
        
        # Z-max boundary (only blocks with maximum Z)
        z_max_faces = []
        for block in block_defs:
            if block['z_range'][1] == self.config.z_max:
                v = block['vertex_indices']
                # zMax face: vertices 4,5,6,7 (normal points in +Z direction)
                z_max_faces.append((v[4], v[5], v[6], v[7]))
        
        z_max_name, z_max_type = self._get_boundary_name_and_type("zMax")
        boundaries_to_add.append({
            'name': z_max_name,
            'type': z_max_type,
            'faces': z_max_faces,
        })
        
        # Ensure all 6 boundaries are present (add empty ones if missing)
        required_boundaries = ["xMin", "xMax", "yMin", "yMax", "zMin", "zMax"]
        for req_name in required_boundaries:
            found = False
            for b in boundaries_to_add:
                if b['name'] == req_name:
                    found = True
                    break
            
            if not found:
                boundaries_to_add.append({
                    'name': req_name,
                    'type': BoundaryType.WALL,
                    'faces': [],
                })
        
        # Format all boundaries
        for b in boundaries_to_add:
            lines.append(self._format_boundary_dict(b['name'], b['type'], b['faces']))
        
        lines.append(");")
        return "\n".join(lines)
    
    def _find_boundary(self, name: str) -> Optional[Boundary]:
        """Find boundary by name"""
        for b in self.config.boundaries:
            if b.name == name:
                return b
        return None
    
    def _find_boundary_for_range(self, default_name: str, x_range: Tuple[float, float]) -> Optional[Boundary]:
        """Find boundary that matches a given X range"""
        # This is a placeholder for more sophisticated boundary matching
        return self._find_boundary(default_name)
    
    def _get_boundary_name_and_type(self, default_name: str) -> Tuple[str, BoundaryType]:
        """
        Get boundary name and type, supporting custom names for segmented meshes
        
        Args:
            default_name: The default boundary name (e.g., "xMin", "yMax")
            
        Returns:
            Tuple of (name, type)
        """
        # First, check if there's a boundary object in config.boundaries
        boundary = self._find_boundary(default_name)
        if boundary:
            return boundary.name, boundary.boundary_type
        
        # For segmented meshes, check custom boundary names and types
        if hasattr(self.config, 'boundary_names') and self.config.boundary_names:
            custom_name = self.config.boundary_names.get(default_name)
            if custom_name:
                # Get custom boundary type if available
                if hasattr(self.config, 'boundary_types') and self.config.boundary_types:
                    custom_type = self.config.boundary_types.get(default_name, BoundaryType.WALL)
                else:
                    custom_type = BoundaryType.WALL
                return custom_name, custom_type
        
        # Return default name and type
        default_types = {
            "xMin": BoundaryType.PATCH,
            "xMax": BoundaryType.PATCH,
            "yMin": BoundaryType.WALL,
            "yMax": BoundaryType.WALL,
            "zMin": BoundaryType.WALL,
            "zMax": BoundaryType.WALL,
        }
        return default_name, default_types.get(default_name, BoundaryType.WALL)
    
    def _generate_vertices(self) -> str:
        """Generate vertices section for single block"""
        lines = ["vertices"]
        lines.append("(")
        
        vertices = self._get_single_block_vertices()
        for i, (x, y, z) in enumerate(vertices):
            lines.append(f"    ({x} {y} {z})  // {i}")
        
        lines.append(");")
        return "\n".join(lines)
    
    def _get_single_block_vertices(self) -> List[Tuple[float, float, float]]:
        """Get 8 vertices for single block"""
        return [
            (self.config.x_min, self.config.y_min, self.config.z_min),  # 0
            (self.config.x_max, self.config.y_min, self.config.z_min),  # 1
            (self.config.x_max, self.config.y_max, self.config.z_min),  # 2
            (self.config.x_min, self.config.y_max, self.config.z_min),  # 3
            (self.config.x_min, self.config.y_min, self.config.z_max),  # 4
            (self.config.x_max, self.config.y_min, self.config.z_max),  # 5
            (self.config.x_max, self.config.y_max, self.config.z_max),  # 6
            (self.config.x_min, self.config.y_max, self.config.z_max),  # 7
        ]
    
    def _generate_blocks(self) -> str:
        """Generate blocks section for single block"""
        lines = ["blocks"]
        lines.append("(")
        lines.append(f"    {self._get_single_block_definition()}")
        lines.append(");")
        return "\n".join(lines)
    
    def _get_single_block_definition(self) -> str:
        """Get hex block definition for single block"""
        return f"hex (0 1 2 3 4 5 6 7) ({self.config.n_x} {self.config.n_y} {self.config.n_z}) " \
               f"simpleGrading ({self.config.grading_x} {self.config.grading_y} {self.config.grading_z})"
    
    def _generate_edges(self) -> str:
        """Generate edges section"""
        lines = ["edges"]
        lines.append("(")
        lines.append("    // All edges are straight lines")
        lines.append(");")
        return "\n".join(lines)
    
    def _generate_boundary(self) -> str:
        """Generate boundary section for single block"""
        lines = ["boundary"]
        lines.append("(")
        
        for boundary in self.config.boundaries:
            lines.append(self._format_boundary(boundary))
        
        lines.append(");")
        return "\n".join(lines)
    
    def _format_boundary(self, boundary: Boundary) -> str:
        """Format a single boundary definition"""
        lines = []
        lines.append(f"    {boundary.name}")
        lines.append("    {")
        lines.append(f"        type {boundary.boundary_type.value};")
        lines.append("        faces")
        lines.append("        (")
        
        for face in boundary.faces:
            lines.append(f"            {self._format_face(face)}")
        
        lines.append("        );")
        lines.append("    }")
        
        return "\n".join(lines)
    
    def _format_boundary_dict(self, name: str, btype: BoundaryType, 
                               faces: List[Tuple[int, int, int, int]]) -> str:
        """Format boundary from dictionary data"""
        lines = []
        lines.append(f"    {name}")
        lines.append("    {")
        lines.append(f"        type {btype.value};")
        lines.append("        faces")
        lines.append("        (")
        
        for face in faces:
            lines.append(f"            {self._format_face(face)}")
        
        lines.append("        );")
        lines.append("    }")
        
        return "\n".join(lines)
    
    def _format_face(self, face: tuple) -> str:
        """Format face vertex indices"""
        return f"({face[0]} {face[1]} {face[2]} {face[3]})"
    
    def write(self, filepath: Union[str, Path]) -> Path:
        """Write blockMeshDict to file"""
        filepath = Path(filepath)
        content = self.generate()
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        return filepath
    
    def write_to_case(self, case_dir: Union[str, Path], 
                      subdir: str = "system") -> Path:
        """Write blockMeshDict to an OpenFOAM case directory"""
        case_dir = Path(case_dir)
        filepath = case_dir / subdir / "blockMeshDict"
        return self.write(filepath)


def generate_blockmesh_dict(config: MeshConfig, 
                            output_path: Union[str, Path] = None) -> str:
    """Convenience function to generate blockMeshDict"""
    generator = BlockMeshDictGenerator(config)
    content = generator.generate()
    
    if output_path:
        generator.write(output_path)
    
    return content
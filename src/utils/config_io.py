"""
Configuration Import/Export Utilities
Supports YAML format for mesh configurations
"""

import yaml
from pathlib import Path
from typing import Union, List
from ..core.mesh_data import MeshConfig, Boundary, BoundaryType, Segment


def export_config(config: MeshConfig, filepath: Union[str, Path]) -> Path:
    """
    Export MeshConfig to YAML file
    
    Args:
        config: MeshConfig to export
        filepath: Output file path
    
    Returns:
        Path to saved file
    """
    filepath = Path(filepath)
    
    # Build dictionary representation
    data = {
        'name': getattr(config, 'name', 'mesh'),
        'description': getattr(config, 'description', ''),
        'domain': {
            'x': {
                'min': config.x_min,
                'max': config.x_max,
            },
            'y': {
                'min': config.y_min,
                'max': config.y_max,
            },
            'z': {
                'min': config.z_min,
                'max': config.z_max,
            },
        },
        'scale': config.scale,
    }
    
    # Segments or single block cells
    if config.use_x_segments:
        data['x_segments'] = [
            {'name': seg.name, 'length': seg.length, 'n_cells': seg.n_cells, 'grading': seg.grading}
            for seg in config.x_segments
        ]
    else:
        data['n_x'] = config.n_x
        data['grading_x'] = config.grading_x
    
    if config.use_y_segments:
        data['y_segments'] = [
            {'name': seg.name, 'length': seg.length, 'n_cells': seg.n_cells, 'grading': seg.grading}
            for seg in config.y_segments
        ]
    else:
        data['n_y'] = config.n_y
        data['grading_y'] = config.grading_y
    
    if config.use_z_segments:
        data['z_segments'] = [
            {'name': seg.name, 'length': seg.length, 'n_cells': seg.n_cells, 'grading': seg.grading}
            for seg in config.z_segments
        ]
    else:
        data['n_z'] = config.n_z
        data['grading_z'] = config.grading_z
    
    # Boundaries for single block mode
    if not config.use_segments and config.boundaries:
        data['boundaries'] = [
            {
                'name': b.name,
                'type': b.boundary_type.value,
                'faces': [list(f) for f in b.faces]
            }
            for b in config.boundaries
        ]
    
    # Boundary custom names and types for segmented mode
    if config.use_segments:
        if config.boundary_names:
            data['boundary_names'] = config.boundary_names
        if config.boundary_types:
            data['boundary_types'] = {
                k: v.value if isinstance(v, BoundaryType) else v
                for k, v in config.boundary_types.items()
            }
    
    # Write YAML file
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    return filepath


def import_config(filepath: Union[str, Path]) -> MeshConfig:
    """
    Import MeshConfig from YAML file
    
    Args:
        filepath: Input YAML file path
    
    Returns:
        MeshConfig object
    """
    filepath = Path(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Extract domain bounds
    domain = data.get('domain', {})
    x_cfg = domain.get('x', {})
    y_cfg = domain.get('y', {})
    z_cfg = domain.get('z', {})
    
    # Check for segments
    x_segments_data = data.get('x_segments', [])
    y_segments_data = data.get('y_segments', [])
    z_segments_data = data.get('z_segments', [])
    
    use_x_segments = bool(x_segments_data)
    use_y_segments = bool(y_segments_data)
    use_z_segments = bool(z_segments_data)
    
    # Build segment objects
    x_segments = [Segment(**seg) for seg in x_segments_data] if use_x_segments else []
    y_segments = [Segment(**seg) for seg in y_segments_data] if use_y_segments else []
    z_segments = [Segment(**seg) for seg in z_segments_data] if use_z_segments else []
    
    # Create config
    config = MeshConfig(
        x_min=x_cfg.get('min', 0.0),
        x_max=x_cfg.get('max', 1.0),
        y_min=y_cfg.get('min', 0.0),
        y_max=y_cfg.get('max', 1.0),
        z_min=z_cfg.get('min', 0.0),
        z_max=z_cfg.get('max', 1.0),
        n_x=data.get('n_x', 20),
        n_y=data.get('n_y', 20),
        n_z=data.get('n_z', 20),
        grading_x=data.get('grading_x', 1.0),
        grading_y=data.get('grading_y', 1.0),
        grading_z=data.get('grading_z', 1.0),
        scale=data.get('scale', 1.0),
        use_x_segments=use_x_segments,
        use_y_segments=use_y_segments,
        use_z_segments=use_z_segments,
        x_segments=x_segments,
        y_segments=y_segments,
        z_segments=z_segments,
    )
    
    # Store name and description as attributes
    config.name = data.get('name', 'mesh')
    config.description = data.get('description', '')
    
    # Load boundaries if present (single block only)
    boundaries_data = data.get('boundaries', [])
    if boundaries_data and not config.use_segments:
        config.boundaries = [
            Boundary(
                name=b['name'],
                boundary_type=BoundaryType(b['type']),
                faces=[tuple(f) for f in b['faces']]
            )
            for b in boundaries_data
        ]
    
    # Load boundary custom names and types for segmented mode
    if config.use_segments:
        config.boundary_names = data.get('boundary_names', {})
        boundary_types_data = data.get('boundary_types', {})
        if boundary_types_data:
            config.boundary_types = {
                k: BoundaryType(v) if isinstance(v, str) else v
                for k, v in boundary_types_data.items()
            }
    
    return config


def list_templates(template_dir: Union[str, Path] = None) -> List[dict]:
    """
    List available template files
    
    Args:
        template_dir: Directory containing templates (default: project templates/)
    
    Returns:
        List of template info dicts: [{'name': ..., 'file': ..., 'description': ...}]
    """
    if template_dir is None:
        # Default template directory
        template_dir = Path(__file__).parent.parent.parent / 'templates'
    
    template_dir = Path(template_dir)
    
    if not template_dir.exists():
        return []
    
    templates = []
    for yaml_file in template_dir.glob('*.yaml'):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            templates.append({
                'name': data.get('name', yaml_file.stem),
                'file': yaml_file,
                'description': data.get('description', ''),
            })
        except Exception:
            # Skip invalid files
            continue
    
    # Sort by name
    templates.sort(key=lambda t: t['name'])
    
    return templates


def load_template(template_name: str, template_dir: Union[str, Path] = None) -> MeshConfig:
    """
    Load a template by name
    
    Args:
        template_name: Name of template to load
        template_dir: Template directory
    
    Returns:
        MeshConfig from template
    """
    templates = list_templates(template_dir)
    
    for t in templates:
        if t['name'] == template_name:
            return import_config(t['file'])
    
    raise ValueError(f"Template '{template_name}' not found")
"""
Main Window for blockMesh-gui - V2 with improved segment support
PyQt6 GUI interface with table-based segment configuration
"""

import sys
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QPushButton, QGroupBox, QGridLayout, QFileDialog, QMessageBox,
    QStatusBar, QFrame, QSizePolicy, QScrollArea, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QTextEdit, QTabWidget
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QColor, QFont

from ..core.mesh_data import MeshConfig, Boundary, BoundaryType, Segment
from ..core.generator import BlockMeshDictGenerator
from ..utils.config_io import export_config, import_config, list_templates, load_template
from ..utils.visualizer import MeshVisualizerWidget


class PreviewDialog(QDialog):
    """Custom dialog for previewing blockMeshDict with visualization and text tabs"""
    
    def __init__(self, content: str, config: MeshConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("blockMeshDict Preview")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        self.config = config
        self._setup_ui(content)
    
    def _setup_ui(self, content: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title label
        title = QLabel("Mesh Preview")
        title.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(title)
        
        # Tab widget for visualization and text
        self.tab_widget = QTabWidget()
        
        # Visualization tab
        viz_tab = QWidget()
        viz_layout = QVBoxLayout(viz_tab)
        viz_layout.setContentsMargins(5, 5, 5, 5)
        
        # Try to create visualization
        try:
            self.viz_widget = MeshVisualizerWidget(self.config, self)
            viz_layout.addWidget(self.viz_widget)
            
            # Legend for boundary colors
            legend_label = QLabel(
                "Boundary colors: "
                "<span style='color:#FF6B6B'>■</span> xMin  "
                "<span style='color:#4ECDC4'>■</span> xMax  "
                "<span style='color:#FFE66D'>■</span> yMin  "
                "<span style='color:#95E1D3'>■</span> yMax  "
                "<span style='color:#DDA0DD'>■</span> zMin  "
                "<span style='color:#87CEEB'>■</span> zMax"
            )
            legend_label.setStyleSheet("font-size: 9pt;")
            viz_layout.addWidget(legend_label)
        except Exception as e:
            error_label = QLabel(f"Visualization unavailable: {e}\n\nInstall matplotlib for 3D preview.")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            viz_layout.addWidget(error_label)
            self.viz_widget = None
        
        self.tab_widget.addTab(viz_tab, "3D Visualization")
        
        # Text tab
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        text_layout.setContentsMargins(5, 5, 5, 5)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Monospace", 10))
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        text_layout.addWidget(self.text_edit)
        
        self.tab_widget.addTab(text_tab, "blockMeshDict Text")
        
        layout.addWidget(self.tab_widget)
        
        # Mesh info
        info_row = QHBoxLayout()
        if self.config.use_segments:
            n_blocks = len(self.block_defs) if hasattr(self, 'block_defs') else \
                      (len(self.config.x_segments) if self.config.use_x_segments else 1) * \
                      (len(self.config.y_segments) if self.config.use_y_segments else 1) * \
                      (len(self.config.z_segments) if self.config.use_z_segments else 1)
            info_text = f"Blocks: {n_blocks} | Domain: ({self.config.x_min}, {self.config.y_min}, {self.config.z_min}) → ({self.config.x_max}, {self.config.y_max}, {self.config.z_max})"
        else:
            info_text = f"Blocks: 1 | Domain: ({self.config.x_min}, {self.config.y_min}, {self.config.z_min}) → ({self.config.x_max}, {self.config.y_max}, {self.config.z_max})"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #666;")
        info_row.addWidget(info_label)
        info_row.addStretch()
        layout.addLayout(info_row)
        
        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _copy_to_clipboard(self):
        """Copy content to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "Copied", "Content copied to clipboard!")


class SuccessDialog(QDialog):
    """Custom dialog for showing successful generation with resizable window"""
    
    def __init__(self, file_path: str, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Success")
        self.setMinimumSize(350, 200)  # Minimum size
        self.resize(450, 250)  # Default size - smaller than preview
        self._setup_ui(file_path, config)
    
    def _setup_ui(self, file_path: str, config):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Success icon and title
        title = QLabel("✓ Successfully saved!")
        title.setStyleSheet("font-weight: bold; font-size: 14pt; color: #4CAF50;")
        layout.addWidget(title)
        
        # File path
        path_label = QLabel(f"<b>Path:</b><br><code>{file_path}</code>")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        
        # Mesh details
        if config.use_segments:
            total_blocks = (len(config.x_segments) if config.use_x_segments else 1) * \
                          (len(config.y_segments) if config.use_y_segments else 1) * \
                          (len(config.z_segments) if config.use_z_segments else 1)
            details = QLabel(f"<b>Mesh:</b> Segmented ({total_blocks} blocks)")
        else:
            details = QLabel(f"<b>Mesh:</b> Single block")
        layout.addWidget(details)
        
        # Domain range
        domain = QLabel(f"<b>Domain:</b> ({config.x_min}, {config.y_min}, {config.z_min}) → ({config.x_max}, {config.y_max}, {config.z_max})")
        domain.setWordWrap(True)
        layout.addWidget(domain)
        
        layout.addStretch()
        
        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


class BoundaryConfigWidget(QGroupBox):
    """Widget for configuring a single boundary"""
    
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.name = name
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        
        # Face name label
        face_label = QLabel(self.name)
        face_label.setMinimumWidth(60)
        layout.addWidget(face_label)
        
        # Type label
        type_label = QLabel("Type:")
        layout.addWidget(type_label)
        
        # Boundary type combo box
        self.type_combo = QComboBox()
        for bt in BoundaryType:
            self.type_combo.addItem(bt.value)
        self.type_combo.setMinimumWidth(120)
        layout.addWidget(self.type_combo)
        
        # Custom name
        name_label = QLabel("Name:")
        layout.addWidget(name_label)
        self.name_edit = QLineEdit(self.name)
        self.name_edit.setMinimumWidth(100)
        layout.addWidget(self.name_edit)
        
        layout.addStretch()
    
    @property
    def boundary_type(self) -> BoundaryType:
        return BoundaryType(self.type_combo.currentText())
    
    @property
    def custom_name(self) -> str:
        return self.name_edit.text() or self.name


class DirectionConfigWidget(QWidget):
    """
    Widget for one direction configuration
    
    Features:
    - Min/Max range inputs
    - Cells input (for non-segmented)
    - Segmented checkbox
    - Table with Name/Length/Cells/Grading columns
    - Last row auto-calculated (gray background)
    """
    
    def __init__(self, direction: str, default_min=0.0, default_max=1.0, 
                 default_cells=20, parent=None):
        super().__init__(parent)
        self.direction = direction
        self._setup_ui(default_min, default_max, default_cells)
    
    def _setup_ui(self, default_min, default_max, default_cells):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Row 1: Range inputs
        range_row = QHBoxLayout()
        
        range_row.addWidget(QLabel(f"{self.direction} Min:"))
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(-1e6, 1e6)
        self.min_spin.setDecimals(3)
        self.min_spin.setValue(default_min)
        self.min_spin.setMinimumWidth(80)
        range_row.addWidget(self.min_spin)
        
        range_row.addWidget(QLabel("Max:"))
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(-1e6, 1e6)
        self.max_spin.setDecimals(3)
        self.max_spin.setValue(default_max)
        self.max_spin.setMinimumWidth(80)
        range_row.addWidget(self.max_spin)
        
        range_row.addWidget(QLabel("Cells:"))
        self.cells_spin = QSpinBox()
        self.cells_spin.setRange(1, 10000)
        self.cells_spin.setValue(default_cells)
        self.cells_spin.setMinimumWidth(80)
        range_row.addWidget(self.cells_spin)
        
        range_row.addStretch()
        layout.addLayout(range_row)
        
        # Row 2: Segment checkbox
        self.use_segments_cb = QCheckBox(f"Use Segments in {self.direction}")
        layout.addWidget(self.use_segments_cb)
        
        # Row 3: Segment table
        self.segment_table = QTableWidget()
        self.segment_table.setColumnCount(4)
        self.segment_table.setHorizontalHeaderLabels(["Name", "Length", "Cells", "Grading"])
        
        header = self.segment_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.segment_table.setColumnWidth(1, 100)
        self.segment_table.setColumnWidth(2, 70)
        self.segment_table.setColumnWidth(3, 70)
        self.segment_table.setMinimumHeight(100)
        self.segment_table.hide()
        
        layout.addWidget(self.segment_table)
        
        # Row 4: Buttons and total
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("+ Add")
        self.add_btn.setMaximumWidth(80)
        self.add_btn.hide()
        btn_row.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("- Remove")
        self.remove_btn.setMaximumWidth(80)
        self.remove_btn.hide()
        btn_row.addWidget(self.remove_btn)
        
        btn_row.addStretch()
        layout.addLayout(btn_row)
        
        # Connect signals
        self.use_segments_cb.stateChanged.connect(self._toggle_mode)
        self.add_btn.clicked.connect(self._add_segment)
        self.remove_btn.clicked.connect(self._remove_segment)
        self.min_spin.valueChanged.connect(self._update_last)
        self.max_spin.valueChanged.connect(self._update_last)
        
        # Connect table cell changes - for immediate update of last segment
        self.segment_table.cellChanged.connect(self._on_table_cell_changed)
        
        # Init default segments (block signals during init)
        self._init_segments()
    
    def _on_table_cell_changed(self, row, column):
        """Triggered when any table cell changes"""
        # Skip if we're currently updating the last row
        if hasattr(self, '_updating_last') and self._updating_last:
            return
        
        # Update last segment when length changes
        if column == 1:  # Length column
            self._update_last()
        # Update total display when cells change
        elif column == 2:  # Cells column
            self._update_total_display()
    
    def _toggle_mode(self, state):
        """Toggle between single and segmented mode"""
        if state == Qt.CheckState.Checked.value:
            self.cells_spin.setEnabled(False)
            self.segment_table.show()
            self.add_btn.show()
            self.remove_btn.show()
            
            # Save original cells count and use it to initialize
            self._original_cells = self.cells_spin.value()
            
            # Initialize segments with equal distribution
            self._init_segments_with_equal_cells()
            # Update total to show sum of all segments
            self._update_total_display()
        else:
            self.cells_spin.setEnabled(True)
            self.segment_table.hide()
            self.add_btn.hide()
            self.remove_btn.hide()
    
    def _init_segments(self):
        """Initialize with 2 segments (editable + last auto)"""
        self.segment_table.setRowCount(2)
        
        # Row 0: editable segment
        self._set_table_row(0, "segment1", 0.5, 10, 1.0, editable=True)
        
        # Row 1: last segment (auto)
        self._set_table_row(1, "last", 0.5, 10, 1.0, editable=False)
    
    def _init_segments_with_equal_cells(self):
        """Initialize segments with equal cell distribution"""
        if not hasattr(self, '_original_cells'):
            return
            
        rows = self.segment_table.rowCount()
        
        if rows > 0:
            # Distribute cells equally to ALL rows (including last)
            equal_cells = self._original_cells // rows
            remainder = self._original_cells % rows
            
            for row in range(rows):
                cells = equal_cells + (1 if row < remainder else 0)
                self._set_table_row(row, f"segment{row + 1}", 0.5, cells, 1.0, editable=(row < rows - 1))
    
    def _set_table_row(self, row, name, length, cells, grading, editable):
        """Set a row in table"""
        # Name
        name_item = QTableWidgetItem(name)
        if not editable:
            name_item.setBackground(QColor(220, 220, 220))
        self.segment_table.setItem(row, 0, name_item)
        
        # Length
        length_item = QTableWidgetItem(f"{length:.3f}")
        if not editable:
            length_item.setBackground(QColor(220, 220, 220))
            length_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.segment_table.setItem(row, 1, length_item)
        
        # Cells
        cells_item = QTableWidgetItem(str(cells))
        self.segment_table.setItem(row, 2, cells_item)
        
        # Grading
        grading_item = QTableWidgetItem(f"{grading:.3f}")
        self.segment_table.setItem(row, 3, grading_item)
    
    def _add_segment(self):
        """Add new segment row before last"""
        rows = self.segment_table.rowCount()
        self.segment_table.insertRow(rows - 1)
        
        n = rows
        self._set_table_row(rows - 1, f"segment{n}", 0.2, 5, 1.0, editable=True)
        self._update_last()
    
    def _remove_segment(self):
        """Remove the selected segment (keep at least one editable segment)"""
        rows = self.segment_table.rowCount()
        # Need at least 2 rows: 1 editable + 1 auto (last)
        if rows <= 2:
            return
        
        # Get selected row
        selected_rows = self.segment_table.selectedItems()
        if not selected_rows:
            # No selection, remove the last editable row
            self.segment_table.removeRow(rows - 2)
        else:
            # Get the row index of the selected item
            selected_row = selected_rows[0].row()
            # Cannot remove the last row (auto-calculated)
            if selected_row == rows - 1:
                return
            self.segment_table.removeRow(selected_row)
        
        self._update_last()
    
    def _update_last(self):
        """Update last row (auto calculated length only, cells are free)"""
        if not self.use_segments_cb.isChecked():
            return
        
        total_length = self.max_spin.value() - self.min_spin.value()
        
        # Sum editable segments for length calculation
        used_length = 0.0
        total_cells = 0
        
        for row in range(self.segment_table.rowCount() - 1):
            length_item = self.segment_table.item(row, 1)
            cells_item = self.segment_table.item(row, 2)
            if length_item:
                used_length += float(length_item.text())
            if cells_item:
                total_cells += int(cells_item.text())
        
        # Update last row length - cells are free to modify
        last_row = self.segment_table.rowCount() - 1
        remaining = total_length - used_length
        
        if remaining > 0:
            # Block signals to prevent infinite recursion
            self._updating_last = True
            self._set_table_row(last_row, "last", remaining, 
                              int(self.segment_table.item(last_row, 2).text()) if self.segment_table.item(last_row, 2) else 10, 
                              1.0, editable=False)
            self._updating_last = False
        
        # Update total display
        self._update_total_display()
    
    def _update_total_display(self):
        """Update the total label to show sum of all segments"""
        if not self.use_segments_cb.isChecked():
            return
        
        total_length = self.max_spin.value() - self.min_spin.value()
        total_cells = 0
        
        for row in range(self.segment_table.rowCount()):
            cells_item = self.segment_table.item(row, 2)
            if cells_item:
                total_cells += int(cells_item.text())
        
        # Update the main cells spin to show the total
        self.cells_spin.setValue(total_cells)
    
    def get_config(self) -> dict:
        """Get config for this direction"""
        if self.use_segments_cb.isChecked():
            segments = []
            for row in range(self.segment_table.rowCount()):
                name = self.segment_table.item(row, 0).text()
                length = float(self.segment_table.item(row, 1).text())
                cells = int(self.segment_table.item(row, 2).text())
                grading = float(self.segment_table.item(row, 3).text())
                segments.append(Segment(name, length, cells, grading))
            
            return {
                'use_segments': True,
                'min': self.min_spin.value(),
                'max': self.max_spin.value(),
                'segments': segments,
            }
        else:
            return {
                'use_segments': False,
                'min': self.min_spin.value(),
                'max': self.max_spin.value(),
                'cells': self.cells_spin.value(),
            }


class MeshConfigWidget(QGroupBox):
    """Main mesh configuration widget with 3 directions"""
    
    def __init__(self, parent=None):
        super().__init__("Mesh Configuration", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Scale factor
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Scale:"))
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(1e-10, 1e10)
        self.scale_spin.setDecimals(3)
        self.scale_spin.setValue(1.0)
        scale_row.addWidget(self.scale_spin)
        scale_row.addStretch()
        layout.addLayout(scale_row)
        
        # Three direction widgets
        self.x_config = DirectionConfigWidget("X", 0.0, 10.0, 100)
        self.y_config = DirectionConfigWidget("Y", 0.0, 1.0, 20)
        self.z_config = DirectionConfigWidget("Z", 0.0, 0.5, 1)
        
        layout.addWidget(self.x_config)
        layout.addWidget(self.y_config)
        layout.addWidget(self.z_config)
    
    def get_config(self) -> dict:
        """Get full mesh config"""
        return {
            'scale': self.scale_spin.value(),
            'x': self.x_config.get_config(),
            'y': self.y_config.get_config(),
            'z': self.z_config.get_config(),
        }


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("blockMesh-gui - OpenFOAM Grid Generator")
        self.setMinimumSize(700, 800)
        
        # Remember last save directory
        self.last_save_dir = Path.cwd()
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        content = QWidget()
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(content)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.addWidget(scroll)
        
        # Title
        title = QLabel("blockMesh-gui")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        subtitle = QLabel("OpenFOAM blockMeshDict Generator")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(line)
        
        # Template and Import/Export row
        template_row = QHBoxLayout()
        
        template_label = QLabel("Template:")
        template_label.setStyleSheet("font-weight: bold;")
        template_row.addWidget(template_label)
        
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(200)
        self._load_templates()
        template_row.addWidget(self.template_combo)
        
        self.load_template_btn = QPushButton("Load")
        self.load_template_btn.setToolTip("Load selected template")
        template_row.addWidget(self.load_template_btn)
        
        template_row.addSpacing(20)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.setToolTip("Import configuration from YAML file")
        template_row.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setToolTip("Export current configuration to YAML file")
        template_row.addWidget(self.export_btn)
        
        template_row.addStretch()
        
        main_layout.addLayout(template_row)
        
        # Separator after template row
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(line2)
        
        # Mesh config
        self.mesh_config = MeshConfigWidget()
        main_layout.addWidget(self.mesh_config)
        
        # Total cells display
        total_row = QHBoxLayout()
        self.total_cells_label = QLabel("Total cells: 0")
        self.total_cells_label.setStyleSheet(
            "font-weight: bold; font-size: 15pt; color: #D32F2F; padding: 4px 0;"
        )
        total_row.addWidget(self.total_cells_label)
        total_row.addStretch()
        main_layout.addLayout(total_row)
        
        # Boundaries
        boundary_group = QGroupBox("Boundary Conditions")
        boundary_layout = QVBoxLayout(boundary_group)
        
        self.boundary_widgets = {}
        for name in ["xMin", "xMax", "yMin", "yMax", "zMin", "zMax"]:
            widget = BoundaryConfigWidget(name)
            self.boundary_widgets[name] = widget
            boundary_layout.addWidget(widget)
        
        # Overset separator and checkbox
        overset_sep = QFrame()
        overset_sep.setFrameShape(QFrame.Shape.HLine)
        boundary_layout.addWidget(overset_sep)
        
        overset_row = QHBoxLayout()
        self.use_overset_cb = QCheckBox("Use single overset boundary (hide individual boundaries)")
        overset_row.addWidget(self.use_overset_cb)
        overset_row.addStretch()
        boundary_layout.addLayout(overset_row)
        
        overset_name_row = QHBoxLayout()
        overset_name_row.addWidget(QLabel("Overset patch name:"))
        self.overset_name_edit = QLineEdit("oversetPatch")
        self.overset_name_edit.setMinimumWidth(150)
        self.overset_name_edit.hide()
        overset_name_row.addWidget(self.overset_name_edit)
        overset_name_row.addStretch()
        boundary_layout.addLayout(overset_name_row)
        
        main_layout.addWidget(boundary_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset")
        self.preview_btn = QPushButton("Preview")
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
        )
        
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.preview_btn)
        btn_layout.addWidget(self.generate_btn)
        
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _connect_signals(self):
        self.reset_btn.clicked.connect(self._on_reset)
        self.preview_btn.clicked.connect(self._on_preview)
        self.generate_btn.clicked.connect(self._on_generate)
        self.load_template_btn.clicked.connect(self._on_load_template)
        self.import_btn.clicked.connect(self._on_import)
        self.export_btn.clicked.connect(self._on_export)
        self.use_overset_cb.stateChanged.connect(self._toggle_overset_mode)
        
        # Auto-update total cells on any cell count change
        for cfg in [self.mesh_config.x_config, self.mesh_config.y_config, self.mesh_config.z_config]:
            cfg.cells_spin.valueChanged.connect(self._update_total_cells_display)
            cfg.use_segments_cb.stateChanged.connect(self._update_total_cells_display)
            cfg.segment_table.cellChanged.connect(self._update_total_cells_display)
    
    def _load_templates(self):
        """Load available templates into combo box with tooltips"""
        self.templates = list_templates()
        self.template_combo.clear()
        
        # Add default item
        self.template_combo.addItem("-- Select Template --")
        
        # Add templates
        for t in self.templates:
            self.template_combo.addItem(t['name'])
        
        # Set tooltip for dropdown items (works when dropdown is open)
        self.template_combo.setItemData(0, "Select a template to load", Qt.ItemDataRole.ToolTipRole)
        for i, t in enumerate(self.templates):
            tooltip = t.get('description', 'No description')
            self.template_combo.setItemData(i + 1, tooltip, Qt.ItemDataRole.ToolTipRole)
        
        # Set tooltip on the combo box itself (works when dropdown is closed)
        self._update_combo_tooltip()
        
        # Connect to update tooltip when selection changes
        self.template_combo.currentIndexChanged.connect(self._update_combo_tooltip)
        
        # Install event filter to refresh tooltip on mouse enter
        self.template_combo.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Event filter to refresh tooltip on mouse enter"""
        if obj == self.template_combo:
            if event.type() == QEvent.Type.Enter:
                self._update_combo_tooltip()
        return super().eventFilter(obj, event)
    
    def _update_combo_tooltip(self):
        """Update the combo box tooltip based on current selection"""
        index = self.template_combo.currentIndex()
        if index == 0:
            self.template_combo.setToolTip("Select a template to load")
        elif index <= len(self.templates):
            tooltip = self.templates[index - 1].get('description', 'No description')
            self.template_combo.setToolTip(tooltip)
    
    def _toggle_overset_mode(self, state):
        """Toggle between individual boundaries and single overset boundary"""
        is_overset = state == Qt.CheckState.Checked.value
        for widget in self.boundary_widgets.values():
            widget.setVisible(not is_overset)
        self.overset_name_edit.setVisible(is_overset)

    def _update_total_cells_display(self):
        """Calculate and display total grid cells from current UI state"""
        try:
            x_cfg = self.mesh_config.x_config
            y_cfg = self.mesh_config.y_config
            z_cfg = self.mesh_config.z_config
            
            if x_cfg.use_segments_cb.isChecked():
                n_x = sum(int(x_cfg.segment_table.item(r, 2).text()) for r in range(x_cfg.segment_table.rowCount()) if x_cfg.segment_table.item(r, 2) and x_cfg.segment_table.item(r, 2).text())
            else:
                n_x = x_cfg.cells_spin.value()
            
            if y_cfg.use_segments_cb.isChecked():
                n_y = sum(int(y_cfg.segment_table.item(r, 2).text()) for r in range(y_cfg.segment_table.rowCount()) if y_cfg.segment_table.item(r, 2) and y_cfg.segment_table.item(r, 2).text())
            else:
                n_y = y_cfg.cells_spin.value()
            
            if z_cfg.use_segments_cb.isChecked():
                n_z = sum(int(z_cfg.segment_table.item(r, 2).text()) for r in range(z_cfg.segment_table.rowCount()) if z_cfg.segment_table.item(r, 2) and z_cfg.segment_table.item(r, 2).text())
            else:
                n_z = z_cfg.cells_spin.value()
            
            total = n_x * n_y * n_z
            self.total_cells_label.setText(f"Total cells: {total}")
        except Exception:
            self.total_cells_label.setText("Total cells: ?")

    def _get_mesh_config(self) -> MeshConfig:
        """Create MeshConfig from UI - supporting 3D segments"""
        config_data = self.mesh_config.get_config()
        
        x_cfg = config_data['x']
        y_cfg = config_data['y']
        z_cfg = config_data['z']
        
        # Check if each direction uses segments
        use_x_segments = x_cfg.get('use_segments', False)
        use_y_segments = y_cfg.get('use_segments', False)
        use_z_segments = z_cfg.get('use_segments', False)
        
        # Check if any direction has segments
        has_any_segments = use_x_segments or use_y_segments or use_z_segments
        
        if has_any_segments:
            # Multi-direction segmented mesh
            config = MeshConfig(
                x_min=x_cfg['min'],
                x_max=x_cfg['max'],
                y_min=y_cfg['min'],
                y_max=y_cfg['max'],
                z_min=z_cfg['min'],
                z_max=z_cfg['max'],
                scale=config_data['scale'],
                use_x_segments=use_x_segments,
                use_y_segments=use_y_segments,
                use_z_segments=use_z_segments,
                x_segments=x_cfg.get('segments', []) if use_x_segments else [],
                y_segments=y_cfg.get('segments', []) if use_y_segments else [],
                z_segments=z_cfg.get('segments', []) if use_z_segments else [],
            )
        else:
            # Simple single block
            config = MeshConfig(
                x_min=x_cfg['min'],
                x_max=x_cfg['max'],
                y_min=y_cfg['min'],
                y_max=y_cfg['max'],
                z_min=z_cfg['min'],
                z_max=z_cfg['max'],
                n_x=x_cfg.get('cells', 100),
                n_y=y_cfg.get('cells', 20),
                n_z=z_cfg.get('cells', 1),
                scale=config_data['scale'],
            )
        
        # Boundaries
        if self.use_overset_cb.isChecked():
            overset_name = self.overset_name_edit.text().strip() or "oversetPatch"
            all_faces = [(0, 4, 7, 3), (2, 6, 5, 1), (1, 5, 4, 0),
                         (3, 7, 6, 2), (0, 3, 2, 1), (4, 5, 6, 7)]
            config.boundaries = [Boundary(overset_name, BoundaryType.OVERSET, all_faces)]
        elif not has_any_segments:
            boundaries = []
            face_indices = {
                "xMin": [(0, 4, 7, 3)],
                "xMax": [(2, 6, 5, 1)],
                "yMin": [(1, 5, 4, 0)],
                "yMax": [(3, 7, 6, 2)],
                "zMin": [(0, 3, 2, 1)],
                "zMax": [(4, 5, 6, 7)],
            }
            
            for name, widget in self.boundary_widgets.items():
                boundaries.append(Boundary(
                    name=widget.custom_name,
                    boundary_type=widget.boundary_type,
                    faces=face_indices[name]
                ))
            
            config.boundaries = boundaries
        else:
            # For segmented mesh, store custom boundary names and types
            config.boundary_names = {
                name: widget.custom_name
                for name, widget in self.boundary_widgets.items()
            }
            # Also store boundary types for segmented mesh
            config.boundary_types = {
                name: widget.boundary_type
                for name, widget in self.boundary_widgets.items()
            }
        
        return config
    
    def _on_reset(self):
        """Reset to defaults"""
        self.mesh_config.scale_spin.setValue(1.0)
        self.mesh_config.x_config.min_spin.setValue(0.0)
        self.mesh_config.x_config.max_spin.setValue(10.0)
        self.mesh_config.x_config.cells_spin.setValue(100)
        self.mesh_config.x_config.use_segments_cb.setChecked(False)
        
        self.mesh_config.y_config.min_spin.setValue(0.0)
        self.mesh_config.y_config.max_spin.setValue(1.0)
        self.mesh_config.y_config.cells_spin.setValue(20)
        self.mesh_config.y_config.use_segments_cb.setChecked(False)
        
        self.mesh_config.z_config.min_spin.setValue(0.0)
        self.mesh_config.z_config.max_spin.setValue(0.5)
        self.mesh_config.z_config.cells_spin.setValue(1)
        self.mesh_config.z_config.use_segments_cb.setChecked(False)
        
        self.use_overset_cb.setChecked(False)
        self.overset_name_edit.setText("oversetPatch")
        for name, widget in self.boundary_widgets.items():
            widget.type_combo.setCurrentText("wall")
            widget.name_edit.setText(name)
        
        self._update_total_cells_display()
        self.status_bar.showMessage("Reset to defaults", 3000)
    
    def _on_preview(self):
        """Preview blockMeshDict"""
        try:
            config = self._get_mesh_config()
            config.validate()
            
            generator = BlockMeshDictGenerator(config)
            content = generator.generate()
            
            # Use custom resizable dialog with visualization
            dialog = PreviewDialog(content, config, self)
            dialog.exec()
            
            self.status_bar.showMessage("Preview generated", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{e}")
    
    def _on_generate(self):
        """Generate and save"""
        try:
            config = self._get_mesh_config()
            config.validate()
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save blockMeshDict", 
                str(self.last_save_dir / "blockMeshDict"),
                "OpenFOAM Dictionary (blockMeshDict);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Remember the directory for next time
            self.last_save_dir = Path(file_path).parent
            
            generator = BlockMeshDictGenerator(config)
            generator.write(file_path)
            
            self.status_bar.showMessage(f"Saved: {file_path}", 5000)
            
            # Use custom resizable success dialog
            dialog = SuccessDialog(file_path, config, self)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{e}")
    
    def _on_load_template(self):
        """Load selected template"""
        template_name = self.template_combo.currentText()
        if template_name == "-- Select Template --":
            QMessageBox.warning(self, "Warning", "Please select a template first.")
            return
        
        try:
            config = load_template(template_name)
            self._apply_config_to_ui(config)
            self.status_bar.showMessage(f"Template '{template_name}' loaded", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load template:\n{e}")
    
    def _on_import(self):
        """Import configuration from YAML file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", str(self.last_save_dir),
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            config = import_config(file_path)
            self._apply_config_to_ui(config)
            # Remember the directory for next time
            self.last_save_dir = Path(file_path).parent
            self.status_bar.showMessage(f"Imported: {file_path}", 5000)
            QMessageBox.information(self, "Success", f"Configuration imported:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import:\n{e}")
    
    def _on_export(self):
        """Export current configuration to YAML file"""
        try:
            config = self._get_mesh_config()
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Configuration", 
                str(self.last_save_dir / "mesh_config.yaml"),
                "YAML Files (*.yaml *.yml);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Remember the directory for next time
            self.last_save_dir = Path(file_path).parent
            
            # Add name and description from user input
            config.name = Path(file_path).stem
            config.description = "User exported configuration"
            
            export_config(config, file_path)
            self.status_bar.showMessage(f"Exported: {file_path}", 5000)
            QMessageBox.information(self, "Success", f"Configuration exported:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export:\n{e}")
    
    def _apply_config_to_ui(self, config: MeshConfig):
        """Apply loaded config to UI widgets"""
        # Scale
        self.mesh_config.scale_spin.setValue(config.scale)
        
        # X direction
        self.mesh_config.x_config.min_spin.setValue(config.x_min)
        self.mesh_config.x_config.max_spin.setValue(config.x_max)
        self.mesh_config.x_config.cells_spin.setValue(config.n_x)
        
        if config.use_x_segments and config.x_segments:
            self.mesh_config.x_config.use_segments_cb.setChecked(True)
            # Clear existing rows and add segments
            n_segs = len(config.x_segments)
            self.mesh_config.x_config.segment_table.setRowCount(n_segs)
            for i, seg in enumerate(config.x_segments):
                editable = (i < n_segs - 1)  # Last row not editable
                self.mesh_config.x_config._set_table_row(i, seg.name, seg.length, seg.n_cells, seg.grading, editable=editable)
            self.mesh_config.x_config._update_last()
        else:
            self.mesh_config.x_config.use_segments_cb.setChecked(False)
        
        # Y direction
        self.mesh_config.y_config.min_spin.setValue(config.y_min)
        self.mesh_config.y_config.max_spin.setValue(config.y_max)
        self.mesh_config.y_config.cells_spin.setValue(config.n_y)
        
        if config.use_y_segments and config.y_segments:
            self.mesh_config.y_config.use_segments_cb.setChecked(True)
            n_segs = len(config.y_segments)
            self.mesh_config.y_config.segment_table.setRowCount(n_segs)
            for i, seg in enumerate(config.y_segments):
                editable = (i < n_segs - 1)
                self.mesh_config.y_config._set_table_row(i, seg.name, seg.length, seg.n_cells, seg.grading, editable=editable)
            self.mesh_config.y_config._update_last()
        else:
            self.mesh_config.y_config.use_segments_cb.setChecked(False)
        
        # Z direction
        self.mesh_config.z_config.min_spin.setValue(config.z_min)
        self.mesh_config.z_config.max_spin.setValue(config.z_max)
        self.mesh_config.z_config.cells_spin.setValue(config.n_z)
        
        if config.use_z_segments and config.z_segments:
            self.mesh_config.z_config.use_segments_cb.setChecked(True)
            n_segs = len(config.z_segments)
            self.mesh_config.z_config.segment_table.setRowCount(n_segs)
            for i, seg in enumerate(config.z_segments):
                editable = (i < n_segs - 1)
                self.mesh_config.z_config._set_table_row(i, seg.name, seg.length, seg.n_cells, seg.grading, editable=editable)
            self.mesh_config.z_config._update_last()
        else:
            self.mesh_config.z_config.use_segments_cb.setChecked(False)
        
        # Detect overset mode (single boundary with type OVERSET)
        is_overset = False
        if len(config.boundaries) == 1 and config.boundaries[0].boundary_type == BoundaryType.OVERSET:
            is_overset = True
            self.use_overset_cb.setChecked(True)
            self.overset_name_edit.setText(config.boundaries[0].name)

        # Boundaries for single block mode
        if not config.use_segments and config.boundaries:
            for boundary in config.boundaries:
                # Map boundary name to face
                face_map = {
                    (0, 4, 7, 3): "xMin",
                    (2, 6, 5, 1): "xMax",
                    (1, 5, 4, 0): "yMin",
                    (3, 7, 6, 2): "yMax",
                    (0, 3, 2, 1): "zMin",
                    (4, 5, 6, 7): "zMax",
                }
                for face_tuple, face_name in face_map.items():
                    if boundary.faces and tuple(boundary.faces[0]) == face_tuple:
                        widget = self.boundary_widgets.get(face_name)
                        if widget:
                            widget.type_combo.setCurrentText(boundary.boundary_type.value)
                            widget.name_edit.setText(boundary.name)

        # Boundaries for segmented mode (restore custom names/types)
        if config.use_segments and not is_overset:
            for face_name, widget in self.boundary_widgets.items():
                if face_name in config.boundary_names:
                    widget.name_edit.setText(config.boundary_names[face_name])
                if face_name in config.boundary_types:
                    bt = config.boundary_types[face_name]
                    widget.type_combo.setCurrentText(bt.value if isinstance(bt, BoundaryType) else bt)
        
        self._update_total_cells_display()


def main():
    """Entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
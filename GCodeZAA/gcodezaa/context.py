from gcodezaa.slicer_syntax import SlicerSyntax, Slicer
from gcodezaa.extrusion import Extrusion
import logging

try:
    import open3d
except ModuleNotFoundError:
    open3d = None

logger = logging.getLogger(__name__)


class ProcessorContext:
    """Context for GCodeZAA processing with enhanced surface tracking."""
    
    syntax: SlicerSyntax
    config_block: dict[str, str] = {}
    model_dir: str
    position_hint: tuple[float, float] | None = None
    gcode: list[str]
    gcode_line = 0

    line_type: str = ""

    last_p: tuple[float, float, float] = (0, 0, 0)
    last_e: float = 0
    last_contoured_z: float | None = None

    exclude_object: dict[str, object] = {}
    active_object: object | None = None

    extrusion: list[Extrusion] = []

    layer = 0
    z: float = 0
    height: float = 0.2  # Layer height in mm
    width: float = 0.4   # Line width in mm (nozzle diameter)
    wipe: bool = False
    
    # Enhanced ZAA tracking
    normal_history: list = []  # For normal smoothing
    z_offset_history: list = []  # For Z offset tracking
    
    # Surface state
    current_surface_normal: tuple = (0, 0, 1)
    confidence_score: float = 0.0

    relative_extrusion: bool = False
    relative_positioning: bool = False

    progress_percent: float = 0
    progress_remaining_minutes: float = 0

    def __init__(self, gcode: list[str], model_dir: str):
        self.gcode = gcode
        self.model_dir = model_dir
        self.syntax = SlicerSyntax(Slicer.detect(self.gcode))
        
        # Initialize lists as copies (avoid class variable sharing)
        self.extrusion = []
        self.normal_history = []
        self.z_offset_history = []
        self.exclude_object = {}

        is_in_config = False
        for l in gcode:
            if not is_in_config and l.startswith(self.syntax.config_block_start):
                is_in_config = True
            elif is_in_config and l.startswith(self.syntax.config_block_end):
                break
            elif is_in_config:
                try:
                    key, value = l.removeprefix(";").split("=", maxsplit=1)
                    self.config_block[key.strip()] = value.strip()
                    
                    # Extract layer height and width from config
                    if "layer_height" in key.lower():
                        try:
                            self.height = float(value)
                            logger.info(f"[GCodeZAA] Config: Layer height = {self.height}mm")
                        except ValueError:
                            pass
                    
                    if "nozzle_diameter" in key.lower() or "line_width" in key.lower():
                        try:
                            self.width = float(value)
                            logger.info(f"[GCodeZAA] Config: Line width = {self.width}mm")
                        except ValueError:
                            pass
                
                except ValueError:
                    pass

    @property
    def line(self):
        if self.gcode_line < len(self.gcode):
            return self.gcode[self.gcode_line]
        return ""
    
    def record_surface_normal(self, normal: tuple, confidence: float = 1.0):
        """Record a surface normal measurement for tracking."""
        self.current_surface_normal = normal
        self.confidence_score = confidence
        self.normal_history.append((normal, confidence))
        
        # Keep history limited
        if len(self.normal_history) > 10:
            self.normal_history.pop(0)
    
    def record_z_offset(self, z_offset: float, confidence: float):
        """Record a Z contour offset for analysis."""
        self.z_offset_history.append((self.z, z_offset, confidence))
        
        # Keep history limited
        if len(self.z_offset_history) > 100:
            self.z_offset_history.pop(0)
    
    def get_average_confidence(self, window: int = 5) -> float:
        """Get average confidence score over recent measurements."""
        if not self.normal_history:
            return 0.0
        
        recent = self.normal_history[-window:]
        return sum(c for _, c in recent) / len(recent)

import sys
import os
import math
import time
import traceback
import shutil
import tempfile
import re
import subprocess
import logging
import json
import hashlib

# --- LOGGING KONFIGURATION (MUST BE FIRST!) ---
script_dir = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(script_dir, "kinematic_engine.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logging.info("[SYSTEM] Logging system initialized. Log file: " + LOG_FILE)

# Z-Anti-Aliasing Enhancement Module (from GCodeZAA)
gcodezaa_path = os.path.join(script_dir, "GCodeZAA")
try:
    if os.path.exists(gcodezaa_path):
        sys.path.insert(0, gcodezaa_path)
        from gcodezaa.surface_analysis import SurfaceAnalyzer, EdgeDetector
        from gcodezaa.config import DEFAULT_MAX_SMOOTHING_ANGLE, MIN_BUILDPLATE_Z
        ZAA_ENABLED = True
        logging.info("[ZAA] Z-Anti-Aliasing module loaded successfully")
    else:
        ZAA_ENABLED = False
        DEFAULT_MAX_SMOOTHING_ANGLE = 40.0
        MIN_BUILDPLATE_Z = 0.0
        logging.warning("[ZAA] GCodeZAA directory not found - Z-Anti-Aliasing disabled")
except (ImportError, ModuleNotFoundError) as e:
    ZAA_ENABLED = False
    DEFAULT_MAX_SMOOTHING_ANGLE = 40.0
    MIN_BUILDPLATE_Z = 0.0
    logging.warning(f"[ZAA] Import failed ({e}) - Z-Anti-Aliasing disabled")

# GCodeZAA Integration (Optional Auto-Enhancement)
try:
    if os.path.exists(gcodezaa_path):
        if gcodezaa_path not in sys.path:
            sys.path.insert(0, gcodezaa_path)
        from gcodezaa.process import process_gcode as gcodezaa_process
        GCODEZAA_AVAILABLE = True
    else:
        GCODEZAA_AVAILABLE = False
except (ImportError, ModuleNotFoundError) as e:
    logging.warning(f"[GCodeZAA] Import failed: {e} - raycasting skipped")
    GCODEZAA_AVAILABLE = False

# --- 27K KINEMATIC ENGINE CONFIGURATION ---
MAX_ACCEL_XY = 24000        # Absolutes Hardware-Limit
MAX_ACCEL_Z = 9000         # Z-Hop Beschleunigung
MIN_ACCEL = 6000            # Unterstes Limit für extrem scharfe Ecken
ANGLE_THRESHOLD = 2.0       # Ignoriere Winkel unter 2 Grad 
ACCEL_HYSTERESIS = 500      # Ändere Beschleunigung nur in signifikanten Schritten
MIN_SEGMENT_LEN = 0.2       # Ignoriere Vektoren unter 0.15mm für reine Winkelkalkulation

# --- ARC-WELDER KINEMATIK INTEGRATION ---
ARC_WELDER_EXE = "ArcWelder.exe"
AW_DYNAMIC_RES = True       # Aktiviere Dynamic Resolution (-d)
AW_MAX_ERROR = 0.06          # Resolution (-r): Max. erlaubte Abweichung in mm (tighter for fine details like 3DBenchy)
AW_TOLERANCE = 0.12         # Tolerance (-t): Arc Fitting Toleranz in % (Decimal → 0.1=10%)

# --- ARTIFACT PREVENTION FOR ARC FITTING ---
ARC_MIN_LENGTH = 1.0        # Minimum arc length in mm (prevent arcing tiny segments)
ARC_MIN_CURVE_RADIUS = 2.0  # Minimum curve radius in mm (don't arc very tight curves)

# --- Z-ANTI-ALIASING CONFIGURATION ---
ENABLE_ZAA = ZAA_ENABLED and True       # Enable enhanced surface contouring
ZAA_LAYER_HEIGHT = 0.2                  # Expected layer height in mm
ZAA_RESOLUTION = 0.05                   # Ray casting resolution in mm
ZAA_SMOOTH_NORMALS = 3                  # Normal smoothing window (0=disabled)
ZAA_MIN_ANGLE_FOR_ZAA = 5.0            # Only apply ZAA if surface angle > this (degrees)
HARD_MAX_SMOOTHING_ANGLE = 45.0
ZAA_MAX_SMOOTHING_ANGLE = min(DEFAULT_MAX_SMOOTHING_ANGLE, HARD_MAX_SMOOTHING_ANGLE)  # Hard-capped for print-head safety
ZAA_Z_OFFSET_PER_ANGLE = 0.01           # Z offset in mm per degree of surface angle (for heuristic ZAA)
ZAA_VERBOSE_LOGGING = False             # Disable verbose tensor batch logging for performance
G1_PATTERN = re.compile(r'([XYZ])([-+]?\d*\.\d+|[-+]?\d+)')
ARC_PATTERN = re.compile(r'([XYZIJKF])([-+]?\d*\.\d+|[-+]?\d+)')  # G2/G3 arc parameters
Z_PARAM_PATTERN = re.compile(r'(^|[ \t])Z([-+]?(?:\d+(?:\.\d*)?|\.\d+))')

# --- G2/G3 ARC COMMAND SUPPORT ---
ENABLE_ARC_ANALYSIS = True              # Analyze G2/G3 commands
ARC_MIN_ACCEL = 6000                     # Minimum accel for arc moves
ARC_MAX_DEVIATION = 0.1                  # Max deviation for arc fitting (mm)

def safe_parse_g1(cmd_strip):
    x = y = z = None
    has_xy = False
    for match in G1_PATTERN.finditer(cmd_strip):
        axis = match.group(1)
        val = float(match.group(2))
        if axis == 'X':
            x, has_xy = val, True
        elif axis == 'Y':
            y, has_xy = val, True
        elif axis == 'Z':
            z = val
    return has_xy, x, y, z

def safe_parse_arc(cmd_strip, is_cw):
    """Parse G2 (CW) or G3 (CCW) arc command.
    
    Args:
        cmd_strip: Command string without G2/G3 prefix
        is_cw: True for G2 (clockwise), False for G3 (counter-clockwise)
    
    Returns:
        Tuple: (has_xy, x_end, y_end, z_end, i_offset, j_offset, f_speed)
    """
    params = {}
    has_xy = False
    
    for match in ARC_PATTERN.finditer(cmd_strip):
        axis = match.group(1)
        val = float(match.group(2))
        
        if axis == 'X':
            has_xy = True
        elif axis == 'Y':
            has_xy = True
        
        params[axis] = val
    
    x_end = params.get('X')
    y_end = params.get('Y')
    z_end = params.get('Z')
    i_offset = params.get('I', 0.0)
    j_offset = params.get('J', 0.0)
    f_speed = params.get('F')
    
    return has_xy, x_end, y_end, z_end, i_offset, j_offset, f_speed

def calculate_arc_length(x1, y1, z1, x2, y2, z2, i, j, is_cw):
    """Calculate TRUE 3D arc length handling helical ZAA moves."""
    cx = x1 + i
    cy = y1 + j
    r1 = math.sqrt(i*i + j*j)
    
    dx_end = x2 - cx
    dy_end = y2 - cy
    
    if r1 < 0.001:
        return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1 if z2 and z1 else 0.0)**2)
    
    angle_start = math.atan2(j, i)
    angle_end = math.atan2(dy_end, dx_end)
    
    if is_cw:
        if angle_end > angle_start: angle_end -= 2 * math.pi
        delta_angle = angle_start - angle_end
    else:
        if angle_end < angle_start: angle_end += 2 * math.pi
        delta_angle = angle_end - angle_start
    
    # 2D Bogenlänge auf der XY-Ebene
    arc_length_2d = r1 * abs(delta_angle)
    
    # 3D Helix-Kompensation (Pythagoras aus 2D-Arc und Z-Delta)
    dz = z2 - z1 if (z1 is not None and z2 is not None) else 0.0
    return math.sqrt(arc_length_2d**2 + dz**2)

def run_arcwelder(gcode_file, start_time):
    """Run ArcWelder for Stage 3 arc compression and 3D arc generation.
    
    Args:
        gcode_file: Path to G-code file to process (already kinematically optimized + ZAA'd)
        start_time: Start time for logging duration
    """
    script_dir = os.path.dirname(os.path.abspath(gcode_file))
    arc_p = os.path.join(script_dir, ARC_WELDER_EXE)
    
    if not os.path.exists(arc_p):
        logging.warning(f"[ArcWelder] {ARC_WELDER_EXE} not found - skipping arc compression")
        return
    
    logging.info(f"[ArcWelder] Starting Stage 3: Arc Compression + 3D Arc Generation")
    
    fd_aw, temp_aw_path = tempfile.mkstemp(suffix=".gcode", text=True)
    os.close(fd_aw)
    
    aw_cmd = [arc_p]
    if AW_DYNAMIC_RES:
        aw_cmd.append("-d")
    aw_cmd.extend(["-y", "-z"])
    aw_cmd.append(f'-t={AW_TOLERANCE}')
    aw_cmd.append(f'-r={AW_MAX_ERROR}')
    aw_cmd.extend(["--", gcode_file, temp_aw_path])
    
    logging.info(f"[ArcWelder] Führe aus: {' '.join(aw_cmd)}")
    
    try:
        result = subprocess.run(aw_cmd, check=True, capture_output=True, text=True)
        
        if os.path.getsize(temp_aw_path) == 0:
            logging.error(f"[ArcWelder] Output file empty (0 bytes)")
            raise Exception("Empty ArcWelder output")
        
        shutil.move(temp_aw_path, gcode_file)
        logging.info(f"[ArcWelder] Stage 3 Complete - 3D arcs generated successfully in {time.time() - start_time:.2f}s")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"[ArcWelder] Process failed (Code {e.returncode})")
        logging.error(f"[ArcWelder] STDERR: {e.stderr.strip()}")
        logging.warning("[ArcWelder] Stage 3 Failed - Continuing with ZAA output (no arc compression)")
        if os.path.exists(temp_aw_path): 
            os.remove(temp_aw_path)
        
    except Exception as ex:
        logging.error(f"[ArcWelder] Unexpected I/O error: {ex}")
        logging.warning("[ArcWelder] Stage 3 Failed - Continuing with ZAA output (no arc compression)")
        if os.path.exists(temp_aw_path): 
            os.remove(temp_aw_path)

# === NEW UTILITY FUNCTIONS ===

def estimate_print_time(gcode_file):
    """Estimate total print duration and collect movement statistics."""
    total_time = 0.0
    total_distance = 0.0
    total_extrusion = 0.0
    arc_segments = 0
    line_segments = 0
    current_speed = 0.0
    current_pos = [0.0, 0.0, 0.0]
    
    try:
        with open(gcode_file, 'r', encoding='utf-8') as f:
            for line in f:
                cmd = line.split(';')[0].strip()
                if not cmd:
                    continue
                
                # Extract feedrate
                f_match = re.search(r'F(\d+)', cmd)
                if f_match:
                    current_speed = float(f_match.group(1))
                
                # Process G1 moves
                if cmd.startswith('G1 '):
                    coords = safe_parse_g1(cmd[3:])
                    has_xy, x, y, z = coords
                    
                    if has_xy or z is not None:
                        new_x = x if x is not None else current_pos[0]
                        new_y = y if y is not None else current_pos[1]
                        new_z = z if z is not None else current_pos[2]
                        
                        distance = math.sqrt(
                            (new_x - current_pos[0])**2 +
                            (new_y - current_pos[1])**2 +
                            (new_z - current_pos[2])**2
                        )
                        
                        if current_speed > 0 and distance > 0:
                            total_time += (distance / current_speed) * 60  # Convert to seconds
                            total_distance += distance
                            line_segments += 1
                        
                        current_pos = [new_x, new_y, new_z]
                
                # Process G2/G3 arcs
                elif cmd.startswith('G2 ') or cmd.startswith('G3 '):
                    is_cw = cmd.startswith('G2 ')
                    arc_coords = safe_parse_arc(cmd[3:].strip(), is_cw)
                    has_xy, x, y, z, i, j, f = arc_coords
                    
                    if has_xy:
                        arc_dist = calculate_arc_length(
                            current_pos[0], current_pos[1], current_pos[2],
                            x if x is not None else current_pos[0],
                            y if y is not None else current_pos[1],
                            z if z is not None else current_pos[2],
                            i, j, is_cw
                        )
                        
                        if current_speed > 0 and arc_dist > 0:
                            total_time += (arc_dist / current_speed) * 60
                            total_distance += arc_dist
                            arc_segments += 1
                        
                        current_pos[0] = x if x is not None else current_pos[0]
                        current_pos[1] = y if y is not None else current_pos[1]
                        current_pos[2] = z if z is not None else current_pos[2]
        
        return {
            'total_time_seconds': total_time,
            'total_time_hours': total_time / 3600.0,
            'total_distance_mm': total_distance,
            'line_segments': line_segments,
            'arc_segments': arc_segments,
            'arc_ratio': (arc_segments / (arc_segments + line_segments) * 100) if (arc_segments + line_segments) > 0 else 0
        }
    
    except Exception as e:
        logging.warning(f"[ESTIMATOR] Print time estimation failed: {e}")
        return None

def generate_quality_report(gcode_file, original_size):
    """Generate comprehensive quality metrics about the optimized GCode."""
    try:
        optimized_size = os.path.getsize(gcode_file)
        compression_ratio = ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
        
        with open(gcode_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        g0_count = sum(1 for l in lines if l.strip().startswith('G0 '))
        g1_count = sum(1 for l in lines if l.strip().startswith('G1 '))
        g2_count = sum(1 for l in lines if l.strip().startswith('G2 '))
        g3_count = sum(1 for l in lines if l.strip().startswith('G3 '))
        m204_count = sum(1 for l in lines if l.strip().startswith('M204 '))
        
        arc_total = g2_count + g3_count
        total_moves = g0_count + g1_count + arc_total
        arc_percentage = (arc_total / total_moves * 100) if total_moves > 0 else 0
        
        # Estimate quality score
        quality_score = min(100, 60 + arc_percentage * 0.3 + (compression_ratio / 2))
        
        report = {
            'original_size_kb': original_size / 1024,
            'optimized_size_kb': optimized_size / 1024,
            'compression_percent': compression_ratio,
            'total_lines': len(lines),
            'g0_moves': g0_count,
            'g1_moves': g1_count,
            'g2_arcs_cw': g2_count,
            'g3_arcs_ccw': g3_count,
            'total_arc_segments': arc_total,
            'arc_conversion_percent': arc_percentage,
            'accel_commands': m204_count,
            'estimated_quality_score': round(quality_score, 1)
        }
        
        return report
    
    except Exception as e:
        logging.warning(f"[REPORT] Quality report generation failed: {e}")
        return None

def backup_gcode(gcode_file):
    """Create backup of original G-code before processing."""
    try:
        backup_file = gcode_file + '.backup'
        if not os.path.exists(backup_file):
            shutil.copy2(gcode_file, backup_file)
            logging.info(f"[BACKUP] Created backup: {os.path.basename(backup_file)}")
            return backup_file
        return backup_file
    except Exception as e:
        logging.warning(f"[BACKUP] Failed to create backup: {e}")
        return None

def select_primary_stl_model(model_dir):
    """Return the first STL filename in sorted order from model_dir, or None."""
    if not os.path.isdir(model_dir):
        return None
    stl_files = sorted(
        f for f in os.listdir(model_dir) if f.lower().endswith('.stl')
    )
    if not stl_files:
        return None
    return stl_files[0]

def detect_ironing_sections(gcode_lines):
    """
    Detect ironing sections in G-code based on slicer TYPE comments.
    
    Returns: List of (start_idx, end_idx) tuples for each ironing section
    
    Supported markers:
    - OrcaSlicer: ;TYPE:Ironing
    - PrusaSlicer: ;TYPE:Ironing
    - Cura: ;TYPE:Ironing (basic support)
    """
    ironing_sections = []
    in_ironing = False
    ironing_start = None
    
    for i, line in enumerate(gcode_lines):
        # Check for TYPE comments
        if ';TYPE:' in line:
            line_type = line.split(';TYPE:')[1].split('\n')[0].strip()
            
            if line_type.lower() == 'ironing':
                if not in_ironing:
                    # Start of ironing section
                    in_ironing = True
                    ironing_start = i
            else:
                if in_ironing:
                    # End of ironing section (new type encountered)
                    in_ironing = False
                    if ironing_start is not None:
                        ironing_sections.append((ironing_start, i))
                        logging.debug(f"[IRONING] Detected section: lines {ironing_start}-{i}")
    
    # Handle case where ironing extends to end of file
    if in_ironing and ironing_start is not None:
        ironing_sections.append((ironing_start, len(gcode_lines)))
        logging.debug(f"[IRONING] Detected section at end: lines {ironing_start}-{len(gcode_lines)}")
    
    return ironing_sections

def restore_from_backup(gcode_file, backup_file):
    """Restore G-code from backup if processing failed."""
    try:
        if backup_file and os.path.exists(backup_file):
            shutil.copy2(backup_file, gcode_file)
            logging.info(f"[RECOVERY] Restored from backup")
            return True
    except Exception as e:
        logging.error(f"[RECOVERY] Failed to restore backup: {e}")
    return False


def sidecar_path_for_gcode(gcode_file):
    return f"{gcode_file}.meta"


def _hash_text_lines(lines):
    h = hashlib.sha256()
    for line in lines:
        h.update(line.encode("utf-8"))
    return h.hexdigest()


def _hash_file(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_stage2_metadata(gcode_lines, selected_model, stage2_input_sha256, stage2_output_sha256):
    ironing_ranges = detect_ironing_sections(gcode_lines)
    contour_markers = []
    for idx, line in enumerate(gcode_lines):
        if line.startswith(";RESET_Z") or "_CONTOUR" in line:
            contour_markers.append(idx)

    return {
        "schema_version": 1,
        "stage": "stage_2",
        "generated_unix": time.time(),
        "selected_model": selected_model,
        "stage2_input_sha256": stage2_input_sha256,
        "stage2_output_sha256": stage2_output_sha256,
        "line_count": len(gcode_lines),
        "ironing_ranges": ironing_ranges,
        "contour_marker_lines": contour_markers,
    }


def write_sidecar_metadata(gcode_file, metadata):
    sidecar = sidecar_path_for_gcode(gcode_file)
    with open(sidecar, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)
    return sidecar


def load_sidecar_metadata(gcode_file):
    sidecar = sidecar_path_for_gcode(gcode_file)
    if not os.path.exists(sidecar):
        return None
    with open(sidecar, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None


def remove_sidecar_metadata(gcode_file):
    sidecar = sidecar_path_for_gcode(gcode_file)
    if os.path.exists(sidecar):
        os.remove(sidecar)
        return True
    return False


def sidecar_hash_matches_file(gcode_file, metadata, hash_key):
    expected = metadata.get(hash_key)
    if not expected:
        return False
    return expected == _hash_file(gcode_file)


def invalidate_stale_sidecar(gcode_file, current_stage2_input_sha256):
    """Remove existing sidecar when it does not match current Stage 2 input hash."""
    sidecar = sidecar_path_for_gcode(gcode_file)
    if not os.path.exists(sidecar):
        return False

    metadata = load_sidecar_metadata(gcode_file)
    if metadata is None:
        os.remove(sidecar)
        logging.warning("[GCodeZAA] Removed unreadable metadata sidecar")
        return True

    previous_input_sha = metadata.get("stage2_input_sha256")
    if previous_input_sha != current_stage2_input_sha256:
        os.remove(sidecar)
        logging.info("[GCodeZAA] Removed stale metadata sidecar due to input hash mismatch")
        return True

    return False


def update_sidecar_stage3_status(gcode_file, status, include_output_hash=False):
    metadata = load_sidecar_metadata(gcode_file)
    if metadata is None:
        return False

    metadata["stage_3"] = status
    if include_output_hash:
        metadata["stage3_output_sha256"] = _hash_file(gcode_file)

    write_sidecar_metadata(gcode_file, metadata)
    return True


def enforce_stage1_success_or_raise(stage_status):
    if stage_status.get("stage_1") == "COMPLETE":
        return

    stage_status["stage_2"] = "SKIPPED (stage 1 failed)"
    stage_status["stage_3"] = "SKIPPED (stage 1 failed)"
    raise RuntimeError("Stage 1 failed validation")


def _format_gcode_decimal(value):
    text = f"{value:.5f}".rstrip("0").rstrip(".")
    if text in ("", "-0", "+0"):
        return "0"
    return text


def _replace_z_in_command(command, new_z):
    formatted = _format_gcode_decimal(new_z)
    return Z_PARAM_PATTERN.sub(
        lambda m: f"{m.group(1)}Z{formatted}",
        command,
        count=1,
    )


def enforce_non_negative_z_in_gcode(gcode_file, min_z=MIN_BUILDPLATE_Z):
    """Clamp motion and coordinate-set commands so no Z value goes below build plate."""
    with open(gcode_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    absolute_positioning = True
    current_z = float(min_z)
    changes = 0
    out = []

    for raw_line in lines:
        stripped = raw_line.rstrip("\r\n")
        newline = raw_line[len(stripped):] or "\n"

        if ";" in stripped:
            command, comment = stripped.split(";", 1)
            comment = ";" + comment
        else:
            command = stripped
            comment = ""

        cmd = command.strip()
        if not cmd:
            out.append(stripped + newline)
            continue

        token = cmd.split()[0].upper()
        if token == "G90":
            absolute_positioning = True
        elif token == "G91":
            absolute_positioning = False

        z_match = Z_PARAM_PATTERN.search(command)
        if z_match and token in ("G0", "G1", "G2", "G3", "G92"):
            z_value = float(z_match.group(2))

            if token == "G92":
                safe_z = max(min_z, z_value)
                if safe_z != z_value:
                    command = _replace_z_in_command(command, safe_z)
                    changes += 1
                current_z = safe_z

            elif absolute_positioning:
                safe_target = max(min_z, z_value)
                if safe_target != z_value:
                    command = _replace_z_in_command(command, safe_target)
                    changes += 1
                current_z = safe_target

            else:
                target_z = current_z + z_value
                if target_z < min_z:
                    safe_delta = min_z - current_z
                    command = _replace_z_in_command(command, safe_delta)
                    current_z = min_z
                    changes += 1
                else:
                    current_z = target_z

        out.append(command + comment + newline)

    if changes > 0:
        with open(gcode_file, "w", encoding="utf-8") as f:
            f.writelines(out)

    return changes


def count_negative_z_commands(gcode_file, min_z=MIN_BUILDPLATE_Z):
    """Return count of commands that still request Z below the build plate."""
    with open(gcode_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    absolute_positioning = True
    current_z = float(min_z)
    negatives = 0

    for raw_line in lines:
        command = raw_line.split(";", 1)[0].strip()
        if not command:
            continue

        token = command.split()[0].upper()
        if token == "G90":
            absolute_positioning = True
        elif token == "G91":
            absolute_positioning = False

        z_match = Z_PARAM_PATTERN.search(command)
        if not z_match or token not in ("G0", "G1", "G2", "G3", "G92"):
            continue

        z_value = float(z_match.group(2))
        if token == "G92":
            if z_value < min_z:
                negatives += 1
            current_z = max(min_z, z_value)
            continue

        if absolute_positioning:
            if z_value < min_z:
                negatives += 1
            current_z = max(min_z, z_value)
        else:
            target_z = current_z + z_value
            if target_z < min_z:
                negatives += 1
            current_z = max(min_z, target_z)

    return negatives

def validate_gcode(file_path):
    """Quick validation of G-code file integrity."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return False, "File is empty"
        
        # Count command types
        g0_count = sum(1 for l in lines if l.strip().startswith('G0 '))
        g1_count = sum(1 for l in lines if l.strip().startswith('G1 '))
        g2_count = sum(1 for l in lines if l.strip().startswith('G2 '))
        g3_count = sum(1 for l in lines if l.strip().startswith('G3 '))
        m204_count = sum(1 for l in lines if l.strip().startswith('M204 '))
        
        logging.info(f"[VALIDATION] G0={g0_count}, G1={g1_count}, G2={g2_count}, G3={g3_count}, M204={m204_count}")
        
        return True, f"Valid: {len(lines)} lines"
    except Exception as e:
        return False, str(e)

def process_gcode(file_path):
    abs_path = os.path.abspath(file_path)
    logging.info(f"--- NEUER PROZESS START ---")
    logging.info(f"Lade G-Code: {abs_path}")
    start_time = time.time()
    
    if not os.path.exists(abs_path):
        logging.error(f"G-Code Datei nicht gefunden: {abs_path}")
        return

    with open(abs_path, 'r', encoding='utf-8', newline='') as f:
        lines = f.readlines()
        
    total_lines = len(lines)
    logging.info(f"G-Code in RAM geladen. Zeilen: {total_lines}")

    # === DETECT IRONING SECTIONS EARLY ===
    ironing_sections = detect_ironing_sections(lines)
    ironing_ranges = [(start, end) for start, end in ironing_sections]
    if ironing_ranges:
        logging.info(f"[IRONING] Detected {len(ironing_ranges)} ironing sections for non-planar ZAA enhancement")
        for idx, (s, e) in enumerate(ironing_ranges):
            logging.debug(f"  [IRONING] Section {idx+1}: lines {s}-{e} - ZAA will apply surface-following moves")
    else:
        logging.debug(f"[IRONING] No ironing sections detected")
    
    # Stage 1 is kinematic-only. Surface analysis is delegated to Stage 2 (GCodeZAA).
    logging.info(f"[PIPELINE] Stage 1: Kinematic-only mode (Z-compensation delegated to Stage 2 GCodeZAA)")

    optimized = []
    c_pos = [0.0, 0.0, 0.0]
    prev_vec = None
    local_max_accel = MAX_ACCEL_XY 
    c_acc = MAX_ACCEL_XY

    for i, line in enumerate(lines):
        raw = line.rstrip('\r\n')
        nl = line[len(raw):]
        if not nl: nl = '\n'
        
        if not raw:
            optimized.append(nl)
            continue
        
        cmd_strip = raw.split(';', 1)[0].strip()

        # 1. Feature Tracking
        if cmd_strip.startswith('M204 '):
            for p in cmd_strip.split()[1:]:
                if p.startswith('S') or p.startswith('P'):
                    val = float(p[1:])
                    local_max_accel = min(val, MAX_ACCEL_XY)
                    c_acc = local_max_accel
                    break
            optimized.append(raw + nl)
            continue

        # 2. Kinematische Bewegungsanalyse
        if cmd_strip.startswith('G1 '):
            has_xy, nx, ny, nz = safe_parse_g1(cmd_strip)

            if has_xy or nz is not None:
                tx = nx if nx is not None else c_pos[0]
                ty = ny if ny is not None else c_pos[1]
                tz = nz if nz is not None else c_pos[2]
                
                new_pos = [tx, ty, tz]
                vec = [tx - c_pos[0], ty - c_pos[1], tz - c_pos[2]]
                
                z_moved = abs(tz - c_pos[2]) > 0.001
                target_accel = local_max_accel
                
                # Cache distance calculation (used for acceleration profiling)
                dist = math.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)
                
                # === ACCELERATION CONTROL ONLY (Z-compensation now in Stage 2) ===
                if z_moved:
                    target_accel = MAX_ACCEL_Z
                elif prev_vec is not None and has_xy:
                    if dist > MIN_SEGMENT_LEN:
                        # Simple velocity-based acceleration (no edge detection in Stage 1)
                        # Edge detection and physics now handled by GCodeZAA
                        target_accel = local_max_accel
                    else:
                        target_accel = local_max_accel
                else:
                    target_accel = local_max_accel

                # Hysterese & M204 Injection
                target_accel = int(target_accel / 100) * 100
                if abs(target_accel - c_acc) >= ACCEL_HYSTERESIS:
                    optimized.append(f"M204 S{target_accel}{nl}")
                    c_acc = target_accel

                # Pass through move as-is (Z-compensation happens in Stage 2)
                optimized.append(raw + nl)

                # Vektor-Tracking
                if has_xy and not z_moved:
                    prev_vec = vec
                else:
                    prev_vec = None
                    
                c_pos = new_pos
                continue
        
        # 2b. Arc Command Analysis (G2/G3)
        if ENABLE_ARC_ANALYSIS and (cmd_strip.startswith('G2 ') or cmd_strip.startswith('G3 ')):
            is_cw = cmd_strip.startswith('G2 ')
            arc_cmd = cmd_strip[3:].strip()  # Remove "G2 " or "G3 "
            has_xy, nx, ny, nz, i_off, j_off, f_speed = safe_parse_arc(arc_cmd, is_cw)
            
            if has_xy:
                tx = nx if nx is not None else c_pos[0]
                ty = ny if ny is not None else c_pos[1]
                tz = nz if nz is not None else c_pos[2]
                
                # Calculate arc length for acceleration profiling
                arc_len = calculate_arc_length(c_pos[0], c_pos[1], c_pos[2], tx, ty, tz, i_off, j_off, is_cw)
                
                # Determine target acceleration (arcs typically need lower accel)
                target_accel = int(ARC_MIN_ACCEL / 100) * 100
                
                # Inject M204 if accel changed significantly
                if abs(target_accel - c_acc) >= ACCEL_HYSTERESIS:
                    optimized.append(f"M204 S{target_accel}{nl}")
                    c_acc = target_accel
                
                # Pass through arc with optimized accel
                optimized.append(raw + nl)
                logging.debug(f"Arc (G{'2' if is_cw else '3'}) at line {i}: length={arc_len:.2f}mm, accel={target_accel}mm/s²")
                
                # Update position
                new_pos = [tx, ty, tz]
                c_pos = new_pos
                
                # Arcs reset kinematic vector tracking (can't predict next segment angle)
                prev_vec = None
                continue

        # Passthrough für alle anderen Befehle
        optimized.append(raw + nl)
        
        # Sicherheits-Break der Kinematik-Kette
        if cmd_strip.startswith(("G0 ", "G2 ", "G3 ", "G28", "G92", "M82", "M83", "T")):
            prev_vec = None

    # No batch flush needed (Z-compensation moved to Stage 2)

    calc_time = time.time() - start_time
    logging.info(f"Kinematik iteriert in {calc_time:.2f}s. Schreibe optimiertes Output...")

    # --- OS-LEVEL TEMPFILE ISOLATION ---
    fd_py, temp_py_path = tempfile.mkstemp(suffix=".gcode", text=True)
    with os.fdopen(fd_py, 'w', encoding='utf-8', newline='') as f:
        f.writelines(optimized)

    # Moving optimized file back to original location
    shutil.move(temp_py_path, abs_path)
        
    logging.info(f"Stage 1 Post-Processing: {time.time() - start_time:.2f}s")
    # Z-compensation logging removed - now handled in Stage 2 (GCodeZAA)

if __name__ == "__main__":
    logging.info(f"Script started with arguments: {sys.argv}")
    logging.info(f"[SYSTEM] OrcaSlicer Post-Processing Mode")
    
    gcode_file = None
    
    # OrcaSlicer passes the G-code file as the first argument after script name
    if len(sys.argv) > 1:
        # Try direct file path first
        potential_file = sys.argv[-1]
        if os.path.isfile(potential_file) and potential_file.endswith('.gcode'):
            gcode_file = potential_file
    
    if not gcode_file:
        logging.error("Kein G-Code Pfad als Argument übergeben oder Datei nicht gefunden.")
        sys.exit(1)
    
    try:
        logging.info(f"[SYSTEM] Processing: {os.path.basename(gcode_file)}")
        
        # Store original file size for compression stats
        original_file_size = os.path.getsize(gcode_file)
        
        # Create backup before processing
        backup_file = backup_gcode(gcode_file)
        
        # Validate input first
        valid, msg = validate_gcode(gcode_file)
        if not valid:
            logging.error(f"[VALIDATION FAILED] {msg}")
            sys.exit(1)
        
        start_time = time.time()
        stage_status = {
            "stage_1": "SKIPPED",
            "stage_2": "SKIPPED",
            "stage_3": "SKIPPED",
        }
        
        # Get script directory (where Ultra_Optimizer.py is located)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # === STAGE 1: Kinematic Optimization ===
        logging.info("[PIPELINE] Stage 1: Kinematic Optimization + M204 Acceleration Control")
        process_gcode(gcode_file)
        logging.info("[PIPELINE] Stage 1 Complete ✓")
        stage_status["stage_1"] = "COMPLETE"
        
        # Validate output
        valid, msg = validate_gcode(gcode_file)
        if valid:
            logging.info(f"[VALIDATION] Stage 1 Output: {msg}")
        else:
            logging.warning(f"[VALIDATION] Stage 1 Output check: {msg}")
            stage_status["stage_1"] = "FAILED"

        if stage_status["stage_1"] != "COMPLETE":
            logging.error("[PIPELINE] Stage 1 did not complete successfully; Stage 2 and Stage 3 will be skipped")
        enforce_stage1_success_or_raise(stage_status)
        
        # === STAGE 2: Optional GCodeZAA Full Raycasting with Z-Compensation ===
        if GCODEZAA_AVAILABLE:
            logging.info("[PIPELINE] Stage 2: GCodeZAA Full Surface Raycasting + Z-Compensation")
            try:
                model_dir = os.path.join(script_dir, "stl_models")

                if not os.path.isdir(model_dir):
                    logging.warning(f"[GCodeZAA] Stage 2 skipped: model directory missing: {model_dir}")
                    logging.info("[PIPELINE] Stage 2 Skipped (Optional)")
                    stage_status["stage_2"] = "SKIPPED (model dir missing)"
                    remove_sidecar_metadata(gcode_file)
                else:
                    selected_model = select_primary_stl_model(model_dir)
                    if not selected_model:
                        logging.warning(f"[GCodeZAA] Stage 2 skipped: no STL files found in {model_dir}")
                        logging.info("[PIPELINE] Stage 2 Skipped (Optional)")
                        stage_status["stage_2"] = "SKIPPED (no STL)"
                        remove_sidecar_metadata(gcode_file)
                    else:
                        plate_object = (selected_model, 0.0, 0.0)

                        with open(gcode_file, 'r', encoding='utf-8') as f:
                            gcode_lines = f.readlines()

                        stage2_input_sha = _hash_text_lines(gcode_lines)
                        invalidate_stale_sidecar(gcode_file, stage2_input_sha)

                        logging.info(
                            f"[GCodeZAA] Using STL model '{selected_model}' for surface raycasting"
                        )
                        enhanced_gcode = gcodezaa_process(gcode_lines, model_dir, plate_object)

                        stage2_output_sha = _hash_text_lines(enhanced_gcode)
                        stage2_metadata = build_stage2_metadata(
                            enhanced_gcode,
                            selected_model,
                            stage2_input_sha,
                            stage2_output_sha,
                        )

                        with open(gcode_file, 'w', encoding='utf-8') as f:
                            f.writelines(enhanced_gcode)

                        sidecar_path = write_sidecar_metadata(gcode_file, stage2_metadata)
                        logging.info(f"[GCodeZAA] Stage 2 metadata sidecar written: {os.path.basename(sidecar_path)}")

                        logging.info("[PIPELINE] Stage 2 Complete ✓")
                        stage_status["stage_2"] = "COMPLETE"
            except Exception as e:
                logging.warning(f"[GCodeZAA] Raycasting failed: {e}")
                logging.info("[PIPELINE] Stage 2 Failed - Continuing with Stage 1 results")
                stage_status["stage_2"] = "FAILED"
                remove_sidecar_metadata(gcode_file)
        else:
            logging.warning("[PIPELINE] Stage 2 Skipped: GCodeZAA not available (install optional Open3D deps)")
            stage_status["stage_2"] = "SKIPPED (GCodeZAA unavailable)"
            remove_sidecar_metadata(gcode_file)
        
        # === STAGE 3: ArcWelder ===
        try:
            existing_sidecar = load_sidecar_metadata(gcode_file)
            if existing_sidecar is not None and not sidecar_hash_matches_file(
                gcode_file, existing_sidecar, "stage2_output_sha256"
            ):
                logging.warning("[ArcWelder] Sidecar out of sync with Stage 2 output - removing stale sidecar")
                remove_sidecar_metadata(gcode_file)

            arcwelder_path = os.path.join(script_dir, "ArcWelder.exe")
            if os.path.isfile(arcwelder_path):
                logging.info("[PIPELINE] Initializing Stage 3 - Arc Welding Optimization...")
                
                # Create temporary output file (safer than in-place)
                fd_aw, temp_aw_path = tempfile.mkstemp(suffix=".gcode", text=True)
                os.close(fd_aw)
                
                # Build proper ArcWelder command with all parameters
                aw_cmd = [arcwelder_path]
                
                # Add optional flags
                if AW_DYNAMIC_RES:
                    aw_cmd.append("-d")  # Dynamic resolution
                
                # Add axis support flags
                aw_cmd.extend(["-y", "-z"])  # Support Y and Z axes
                
                # Add tolerance and resolution settings
                aw_cmd.append(f'-t={AW_TOLERANCE}')      # Tolerance
                aw_cmd.append(f'-r={AW_MAX_ERROR}')      # Resolution (max error)
                
                # Add input/output files with separator
                aw_cmd.extend(["--", gcode_file, temp_aw_path])
                
                logging.debug(f"[ArcWelder] Command: {' '.join(aw_cmd)}")
                
                result = subprocess.run(
                    aw_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    # Verify output file is not empty
                    if os.path.getsize(temp_aw_path) == 0:
                        logging.error(f"[ArcWelder] Output file empty (0 bytes)")
                        if os.path.exists(temp_aw_path):
                            os.remove(temp_aw_path)
                        logging.info("[PIPELINE] Stage 3 Failed - Continuing with previous stages")
                    else:
                        # Move temp file to original location
                        shutil.move(temp_aw_path, gcode_file)
                        update_sidecar_stage3_status(gcode_file, "COMPLETE", include_output_hash=True)
                        logging.info("[ArcWelder] Arc welding optimization successful")
                        logging.info("[PIPELINE] Stage 3 Complete ✓")
                        stage_status["stage_3"] = "COMPLETE"
                else:
                    logging.error(f"[ArcWelder] Process failed (Code {result.returncode})")
                    if result.stderr:
                        logging.error(f"[ArcWelder] STDERR: {result.stderr.strip()}")
                    if result.stdout:
                        logging.debug(f"[ArcWelder] STDOUT: {result.stdout.strip()}")
                    if os.path.exists(temp_aw_path):
                        os.remove(temp_aw_path)
                    update_sidecar_stage3_status(gcode_file, "FAILED")
                    logging.info("[PIPELINE] Stage 3 Failed - Continuing with previous stages")
                    stage_status["stage_3"] = "FAILED"
            else:
                logging.info("[PIPELINE] Stage 3 Skipped (ArcWelder not available)")
                update_sidecar_stage3_status(gcode_file, "SKIPPED (ArcWelder unavailable)")
                stage_status["stage_3"] = "SKIPPED (ArcWelder unavailable)"
        except Exception as e:
            logging.error(f"[ArcWelder] Exception occurred: {e}")
            logging.warning(f"[ArcWelder] Arc welding failed")
            logging.info("[PIPELINE] Stage 3 Failed - Continuing with previous stages")
            update_sidecar_stage3_status(gcode_file, "FAILED")
            stage_status["stage_3"] = "FAILED"

        # === SAFETY ENFORCEMENT: NEVER MOVE BELOW BUILD PLATE ===
        clamped = enforce_non_negative_z_in_gcode(gcode_file, MIN_BUILDPLATE_Z)
        if clamped > 0:
            logging.warning(
                "[SAFETY] Clamped %d negative-Z command(s) to Z>=%.3fmm",
                clamped,
                MIN_BUILDPLATE_Z,
            )
        else:
            logging.info("[SAFETY] No negative-Z commands detected")

        remaining_negative = count_negative_z_commands(gcode_file, MIN_BUILDPLATE_Z)
        if remaining_negative > 0:
            raise RuntimeError(
                f"Safety validation failed: {remaining_negative} negative-Z command(s) remain"
            )

        if load_sidecar_metadata(gcode_file) is not None:
            update_sidecar_stage3_status(
                gcode_file,
                stage_status["stage_3"],
                include_output_hash=True,
            )
        
        # === POST-PROCESSING ANALYSIS ===
        logging.info("[PIPELINE] Generating post-processing statistics...")
        
        # Print time estimation
        time_estimate = estimate_print_time(gcode_file)
        if time_estimate:
            hours = int(time_estimate['total_time_hours'])
            minutes = int((time_estimate['total_time_hours'] - hours) * 60)
            logging.info(f"[ESTIMATOR] Print time: ~{hours}h {minutes}m ({time_estimate['total_time_hours']:.2f}h)")
            logging.info(f"[ESTIMATOR] Total distance: {time_estimate['total_distance_mm']:.1f}mm")
            logging.info(f"[ESTIMATOR] Line segments: {time_estimate['line_segments']}, Arc segments: {time_estimate['arc_segments']}")
            logging.info(f"[ESTIMATOR] Arc conversion: {time_estimate['arc_ratio']:.1f}%")
        
        # Quality report
        report = generate_quality_report(gcode_file, original_file_size)
        if report:
            logging.info(f"[REPORT] File compression: {report['compression_percent']:.1f}% reduction")
            logging.info(f"[REPORT] Input: {report['original_size_kb']:.1f} KB → Output: {report['optimized_size_kb']:.1f} KB")
            logging.info(f"[REPORT] Total lines: {report['total_lines']}")
            logging.info(f"[REPORT] Moves - G0: {report['g0_moves']}, G1: {report['g1_moves']}, Arcs(G2/G3): {report['total_arc_segments']}")
            logging.info(f"[REPORT] Arc conversion rate: {report['arc_conversion_percent']:.1f}%")
            logging.info(f"[REPORT] Acceleration commands: {report['accel_commands']}")
            logging.info(f"[REPORT] Estimated quality score: {report['estimated_quality_score']}/100")
        
        # === COMPLETION ===
        total_time = time.time() - start_time
        logging.info("[PIPELINE] Summary: Stage 1=%s | Stage 2=%s | Stage 3=%s",
                 stage_status["stage_1"], stage_status["stage_2"], stage_status["stage_3"])
        logging.info(
            "[SAFETY] Enforced smoothing cap %.1fdeg and build-plate floor Z>=%.3fmm",
            ZAA_MAX_SMOOTHING_ANGLE,
            MIN_BUILDPLATE_Z,
        )
        logging.info("[PIPELINE] ════════════════════════════════════════")
        logging.info("[PIPELINE] All-In-One Post-Processing Complete ✓")
        logging.info(f"[SYSTEM] Output: {os.path.basename(gcode_file)}")
        logging.info(f"[SYSTEM] Total processing time: {total_time:.2f}s")
        logging.info("[PIPELINE] Ready for printing!")
        logging.info("[PIPELINE] ════════════════════════════════════════")
        
    except Exception as e:
        logging.critical("[FATAL ERROR] Engine Crash. Unhandled Exception:", exc_info=True)
        # Attempt recovery
        if backup_file and os.path.exists(backup_file):
            if restore_from_backup(gcode_file, backup_file):
                logging.info("[RECOVERY] Processing failed - restored from backup")
        sys.exit(1)
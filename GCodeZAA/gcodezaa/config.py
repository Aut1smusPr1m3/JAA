"""Shared configuration for GCodeZAA and Ultra_Optimizer integration."""

# Degrees from vertical that may use full Z-offset; steeper surfaces taper offsets
# aggressively to avoid nozzle/cooling-duct collisions.
DEFAULT_MAX_SMOOTHING_ANGLE = 15.0

# Absolute lower Z limit (build-plate plane).
MIN_BUILDPLATE_Z = 0.0

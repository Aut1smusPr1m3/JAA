# Quick Reference: New Ultra Optimizer Features

## 📊 What You'll Now See in Logs

### Before (Old Output)
```
[PIPELINE] All-In-One Post-Processing Complete (4 Stages) ✓
[SYSTEM] Output: model.gcode
```

### After (New Output)
```
[ESTIMATOR] Print time: ~2h 15m (2.25h)
[ESTIMATOR] Total distance: 12543.2mm
[ESTIMATOR] Line segments: 5234, Arc segments: 892
[ESTIMATOR] Arc conversion: 14.6%

[REPORT] File compression: 12.5% reduction
[REPORT] Input: 245.3 KB → Output: 214.6 KB
[REPORT] Total lines: 15432
[REPORT] Moves - G0: 234, G1: 12456, Arcs(G2/G3): 742
[REPORT] Arc conversion rate: 5.6%
[REPORT] Acceleration commands: 823
[REPORT] Estimated quality score: 82.4/100

[PIPELINE] ════════════════════════════════════════
[PIPELINE] All-In-One Post-Processing Complete ✓
[SYSTEM] Output: model.gcode
[SYSTEM] Total processing time: 8.34s
[PIPELINE] Ready for printing!
[PIPELINE] ════════════════════════════════════════
```

---

## 🔧 Key Improvements at a Glance

| Feature | What It Does | Where to Find |
|---------|-------------|----------------|
| **Print Time Estimator** | Shows how long print will take | `[ESTIMATOR]` section |
| **Quality Score** | 0-100 rating of optimization result | `[REPORT]` section |
| **File Compression** | % size reduction from optimization | `[REPORT]` section |
| **Arc Conversion** | % of segments converted to arcs | `[REPORT]` section |
| **Automatic Backup** | `.gcode.backup` file created | In script directory |
| **Auto-Recovery** | Restores backup if processing fails | See error messages |
| **Processing Time** | Total time for all stages | `[PIPELINE]` completion |

---

## 📈 Understanding the Quality Score

The **Estimated Quality Score** (0-100) is calculated based on:
- Arc compression effectiveness (more arcs = better)
- File compression ratio (more compression = better)
- Baseline efficiency metrics

**Interpretation**:
- **90-100**: Excellent optimization (complex curves, good arc fit)
- **70-89**: Good optimization (balanced)
- **50-69**: Modest optimization (mostly straight lines)
- **<50**: Minimal optimization (simple geometry)

---

## 💾 Automatic Backup System

**How it works**:
1. Before processing starts → `.gcode.backup` is created
2. If any stage fails → Original is automatically restored
3. You can manually restore by copying `.backup` back

**Backup location**:
```
c:\ArcWelder\Skript\model.gcode.backup
```

⚠️ **Note**: Only one backup per file. It gets overwritten each run.

---

## 🕐 Print Time Estimation Details

The estimator calculates:
- **Assumes constant speed** throughout (conservative estimate)
- **Includes all G1/G2/G3 movements** (extrusion + travel)
- **Excludes tool changes, retractions** (adds 5-10% in reality)
- **Actual may vary** ±10% depending on printer acceleration

**Example**: If estimator shows 2h 15m, actual might be 2h 00m - 2h 30m

---

## 📊 Arc Conversion Metric Explained

Shows how effectively ArcWelder compressed the G-code:

```
Arc segments: 892
Line segments: 5234
Arc ratio: 14.6%
```

**Means**:
- Out of 6,126 total movement commands
- 892 became arcs (curved moves)
- 5,234 stayed as lines (straight moves)
- ~14.6% of geometry had curves worth converting

**Higher arc ratio** = More curved surfaces in model

---

## 🎯 How to Use These Features

### For 3D Print Jobs
1. Before printing, check `[ESTIMATOR]` for print time
2. Check `[REPORT]` quality score to know optimization quality
3. Look at arc conversion % to see if model has curves

### For Troubleshooting
1. Check compression % - if very low (<5%), unusual geometry
2. Check arc ratio - if very high (>30%), very curvy model
3. If quality score <50, model might be mostly walls/infill

### For Batch Processing
1. Compare quality scores across different models
2. Look at arc conversion to estimate model complexity
3. Use compression % to track optimization consistency

---

## 📝 Log File Location

All detailed logs saved to:
```
c:\ArcWelder\Skript\kinematic_engine.log
```

Open this file to see:
- Full processing details
- Individual stage timings
- Any warnings or errors
- Complete statistics

---

## ⚡ Performance Expectations

**Typical processing times**:
- Simple models (< 100K GCODE lines): 1-3 seconds
- Medium models (100K-500K lines): 3-10 seconds
- Complex models (> 500K lines): 10-30 seconds

**File compression** (depends on geometry):
- Mostly straight lines: 2-5% reduction
- Mixed geometry: 5-15% reduction
- Very curved surfaces: 15-30% reduction

---

## 🔍 What Each Report Metric Means

| Metric | Min/Typical/Max | What It Indicates |
|--------|-----------------|-------------------|
| Compression | 2% / 10% / 30% | Geometry complexity |
| Arc conversion | 0% / 10% / 50% | Curve-to-straight ratio |
| Quality score | 50 / 75 / 95 | Overall optimization success |
| Print time | Minutes / Hours | Model size + complexity |

---

## ✅ Verification Checklist Before Printing

- [ ] Print time estimate is reasonable
- [ ] Quality score > 50
- [ ] Arc conversion > 5% (shows curves detected)
- [ ] Compression > 3% (shows optimization worked)
- [ ] No errors in log file (check for [WARNING] or [ERROR])
- [ ] Backup file exists (safety verification)

---

**Need help?** Check these files:
- Full details: `IMPROVEMENTS_IMPLEMENTED.md`
- Processing logs: `kinematic_engine.log`
- Backup file: `filename.gcode.backup`

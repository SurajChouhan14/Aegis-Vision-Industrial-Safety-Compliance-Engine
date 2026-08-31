# 🏭 Aegis-Vision: Industrial Safety Compliance & Incident Prevention Engine
> **Detector-Agnostic Spatial IoGA Geometry, Ray-Casting Polygon Containment, and 4-State Anti-Alarm-Fatigue State Machine**  
> *Computer Vision Geometry · OpenCV · Ray-Casting Polygon Containment · IoGA Association · Finite State Machine*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/SurajChouhan14/Aegis-Vision-Industrial-Safety-Compliance-Engine/actions/workflows/ci.yml/badge.svg)](https://github.com/SurajChouhan14/Aegis-Vision-Industrial-Safety-Compliance-Engine/actions)
[![Benchmark](https://img.shields.io/badge/benchmark-Synthetic%20CCTV%20Stream%20(50%20Frames)-blue.svg)]()
[![Tests](https://img.shields.io/badge/tests-6%20passed-brightgreen.svg)]()

---

## 🎯 Executive Overview & Geometric Architecture
Aegis-Vision is a high-throughput, detector-agnostic industrial safety compliance engine that evaluates 2D bounding boxes (compatible with YOLO, RT-DETR, or OpenCV detectors) to enforce heavy-machinery danger zone containment and PPE compliance across continuous CCTV surveillance streams.

### 1. Ray-Casting Polygon Danger Zone Containment
* Implements point-in-polygon ray-casting (Jordan Curve Theorem) over worker ground-anchor foot coordinates `((x1+x2)/2, y2)` against arbitrary $N$-vertex polygon danger boundaries.
* Eliminates global-frame false positive breaches caused by worker bounding boxes clipping zone boundaries in 3D perspective.

### 2. Anatomical Intersection-over-Gear-Area (IoGA)
* Replaces naive global-box IoU with anatomical spatial slicing:
  * **Hardhat / Helmet:** Must intersect the upper $40\%$ head region with $\text{IoGA} \ge 0.60$.
  * **High-Vis Safety Vest:** Must intersect the torso region ($10\%$ to $80\%$) with $\text{IoGA} \ge 0.60$.
* Eliminates false associations from helmets dropped on the floor or carried in hands.

### 3. 4-State Anti-Alarm-Fatigue Finite State Machine
```
  Worker Enters Danger Zone (Unprotected)
                    │
                    ▼
        ┌───────────────────────┐
        │ PENDING (Grace Period)│ ──[ Dons PPE / Exits Zone ]──> [ COMPLIANT (0 Alarms) ]
        │ • 30-second window    │
        └───────────┬───────────┘
                    │ (Elapsed >= 30s)
                    ▼
        ┌───────────────────────┐
        │ ALARMING              │ ──[ Active Audible Siren (10s) ]
        └───────────┬───────────┘
                    │ (Elapsed >= 10s)
                    ▼
        ┌───────────────────────┐
        │ REMINDING             │ ──[ Periodic 20s Reminder Warnings ]
        └───────────┬───────────┘
                    │ (Continuous Violation >= 120s)
                    ▼
        ┌───────────────────────┐
        │ TIMED_OUT (Escalated) │ ──[ Logged to Safety Supervisor Incident Ledger ]
        └───────────────────────┘
```

---

## 📊 Empirical Benchmark & Comparative Performance

### Synthetic CCTV Scenario Stream ($N=50$ Scripted Keyframes, $122.5\text{s}$ Horizon)

| Performance / Compliance Metric | Naive Baseline (Zero Grace, 1-Frame Debounce) | Aegis-Vision Engine | Improvement / Status |
|---|:---:|:---:|:---:|
| **Total Audible Alarms Triggered** | $3\text{ Alarms}$ | **$2\text{ Alarms}$** | True Non-Compliant Only |
| **Nuisance False Alarms (Donning/Safe)** | $1\text{ Alarm (Worker 105)}$ | **$0\text{ Alarms}$** | **$100.0\%\text{ Reduction}$** |
| **Anti-Alarm-Fatigue Protection Rate** | $0.0\%$ | **$100.0\%$** | $30\text{s}$ Grace Period Active |
| **Execution Latency per Frame** | $0.05\text{ ms}$ | **$0.05\text{ ms}$** | $> 20,000\text{ FPS Throughput}$ |
| **Debounce Hysteresis** | $1\text{ Frame (Flicker Prone)}$ | **$2\text{ Frames (Stable)}$** | Zero False Dropouts |

---

## 📁 Repository Structure

```text
Aegis-Vision-Industrial-Safety-Compliance-Engine/
├── .github/
│   └── workflows/
│       └── ci.yml                      # Automated CI test & validation workflow
├── .gitignore                          # Git exclusions (pycache, logs)
├── Industrial_Safety_OSHA_Vision.ipynb # Interactive evaluation & visualization notebook
├── README.md                           # Documentation & geometric architecture
├── data/
│   ├── industrial_surveillance_stream.json  # 50-frame synthetic CCTV stream
│   └── safety_compliance_audit_log.json     # Timestamped safety audit log
├── requirements.txt                    # Production dependencies
├── run_pipeline.py                     # 4-phase safety compliance pipeline & benchmark
├── src/
│   ├── __init__.py                     # Package init
│   ├── data_loader.py                  # Synthetic surveillance stream generator & loader
│   ├── spatial_association_engine.py   # Ray-casting & anatomical IoGA association engine
│   └── temporal_state_machine.py       # 4-state anti-alarm-fatigue FSM with debouncing
└── test_spatial_and_temporal_engine.py # 6 automated unit & state lifecycle tests
```

---

## 🚀 Quickstart

### 1. Installation
```bash
git clone https://github.com/SurajChouhan14/Aegis-Vision-Industrial-Safety-Compliance-Engine.git
cd Aegis-Vision-Industrial-Safety-Compliance-Engine
pip install -r requirements.txt
```

### 2. Run Pipeline Benchmark
```bash
python run_pipeline.py
```

### 3. Run Test Suite
```bash
python test_spatial_and_temporal_engine.py
```

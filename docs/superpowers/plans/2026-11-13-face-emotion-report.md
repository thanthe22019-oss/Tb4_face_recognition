# Bài thực hành 4 Face Emotion Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a detailed Vietnamese LaTeX report for the completed `tbe4_face_recognition` package while keeping every unverified webcam and TurtleBot result explicitly pending.

**Architecture:** Reuse the read-only UET/TurtleBot 4 LaTeX template as a visual scaffold and split the report into focused chapters for recognition, filtering, behavior, odometry motion, ROS integration, operation, and evidence. Repository source and automated tests provide verified facts; manual webcam/simulator results use named placeholders until real evidence is supplied.

**Tech Stack:** LaTeX/pdfLaTeX, Vietnamese T5 fonts, TikZ, longtable, BibTeX, ROS 2 Humble source/config/test evidence

**Spec:** `docs/superpowers/specs/2026-11-13-face-emotion-report-design.md`

## Global Constraints

- Write in Vietnamese and preserve the established UET/TurtleBot 4 visual style.
- Treat `/home/alex/Interaction/tb4_nav2/report/Bao_cao_TurtleBot4_SLAM_Nav2_23020730/` as read-only.
- Write report deliverables only under `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/`.
- Do not modify ROS/Python application source, YAML, launch files, tests, or runtime scripts while producing the report.
- Use commit `c35bdd5` and fresh verification output as the application evidence baseline; update both if implementation changes before report generation.
- State only verified automated results and mark every unverified webcam/simulator result with `\pending`.
- Do not store raw webcam frames, face crops, private video, virtualenv content, credentials, or unrelated personal data.
- Keep repository/video URLs as placeholders until real public links exist.

## Review Focus

- Branch provenance: do not describe `feature/face-emotion-control` as merged into `main` unless Git proves it at report time.
- AI acceptance: passing fake-detector tests does not prove the installed FER model recognizes six live expressions.
- Motion acceptance: numerical profile tests do not prove the simulator or physical TurtleBot completed the trajectories.
- Safety claims: distinguish tested pure/controller behavior from pending live camera-close, no-face, neutral, and odometry-loss trials.
- Evidence integrity: every missing screenshot must remain a named placeholder and never render as an apparent PASS.

---

### Task 1: Create the UET report scaffold

**Files:**
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/main.tex`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/preamble.tex`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/references.bib`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/Logo_UET.png`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/images/README.md`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/00-frontmatter.tex`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/01-muc-tieu-kien-truc.tex`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/02-nhan-dien-bieu-cam.tex`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/03-loc-va-state-machine.tex`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/04-dieu-khien-chuyen-dong.tex`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/05-cai-dat-van-hanh.tex`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/06-kiem-thu-ket-qua.tex`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/07-ket-luan.tex`

**Interfaces:**
- Consumes: the read-only UET/TurtleBot 4 report template named in the spec.
- Produces: a compilable multi-file report skeleton with `\reportfigure`, `\pending`, code-block, table, and TikZ support.

- [ ] **Step 1: Copy only reusable visual assets**

Copy the logo and adapt `preamble.tex`, title-page layout, typography, colors, code blocks, tables, `\reportfigure`, and Vietnamese metadata. Do not copy technical text from the SLAM/Nav2 report.

- [ ] **Step 2: Define report metadata and chapter order**

Set the author to Thân Thế Trí Dũng, MSSV 23020730, class QH-2023-I/CQ-E-RE, and title the work “Nhận diện biểu cảm khuôn mặt và điều khiển TurtleBot 4”. Wire all eight content files from `main.tex`.

- [ ] **Step 3: Add safe evidence macros**

Define `\pending{...}` with a visible pending style and preserve the figure macro that renders a named placeholder when an image is missing.

- [ ] **Step 4: Compile the empty structure**

Run:

```bash
cd report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Expected: PDF generation succeeds with intentional image placeholders and no undefined content files.

- [ ] **Step 5: Commit**

```bash
git add report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730
git commit -m "docs: scaffold face emotion practice report"
```

### Task 2: Document architecture and facial-emotion recognition

**Files:**
- Modify: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/01-muc-tieu-kien-truc.tex`
- Modify: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/02-nhan-dien-bieu-cam.tex`
- Modify: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/references.bib`

**Interfaces:**
- Consumes: `README.md`, `package.xml`, `setup.py`, `emotion_model.py`, `emotion_recognition_node.py`, `protocol.py`, recognition YAML, launch files, and the approved design spec.
- Produces: accurate chapters for project goals, two-node architecture, JSON contracts, FER/TFLite processing, webcam scheduling, overlay, and dependency isolation.

- [ ] **Step 1: Explain the problem and selected architecture**

Describe the six required emotions, the two-process boundary, standard ROS messages, `/emotion_observation`, `/emotion_behavior_status`, `/odom`, and the controller-only `/cmd_vel` rule. Add a TikZ architecture diagram consistent with the design spec.

- [ ] **Step 2: Document the webcam and FER pipeline**

Trace `VideoCapture` → mirror → 5 Hz FER inference → validated `DetectedFace` → `Observation` → 20 Hz overlay. Explain exact single-face selection, confidence, `disgust`, no-face/multiple-face behavior, and camera-loss unknown publication.

- [ ] **Step 3: Document the isolated AI environment**

List the pinned direct dependencies, `.venv-face --system-site-packages`, FER `--no-deps`, TFLite mode, and why the ROS controller never imports TensorFlow.

- [ ] **Step 4: Add references**

Cite ROS 2 Humble, TurtleBot 4, OpenCV, FER/FER2013, TensorFlow Lite, and the upstream TurtleBot 4 simulator using primary project documentation or papers.

- [ ] **Step 5: Check technical names against source**

Run:

```bash
rg -n "emotion_observation|emotion_behavior_status|cmd_vel|FER\(|inference_rate_hz|camera_index" \
  tbe4_face_recognition config launch README.md
```

Expected: every report name, topic and default matches the current repository.

- [ ] **Step 6: Commit**

```bash
git add report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730
git commit -m "docs: explain face emotion recognition architecture"
```

### Task 3: Document filtering, behavior, motion and safety

**Files:**
- Modify: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/03-loc-va-state-machine.tex`
- Modify: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/04-dieu-khien-chuyen-dong.tex`

**Interfaces:**
- Consumes: `emotion_filter.py`, `behavior.py`, `motion.py`, `emotion_controller_node.py`, `config/controller.yaml`, and their tests.
- Produces: a precise account of temporal stabilization, one-shot behavior, re-arm rules, odometry feedback, five non-neutral trajectories, and every stop path.

- [ ] **Step 1: Explain filtering with exact thresholds**

Document strict confidence above `0.60`, zero temporal delay, immediate neutral re-arm, unknown/no-face re-arm `0.75 s`, observation timeout `0.75 s`, session/sequence handling, and immediate unsafe-observation stop reasons.

- [ ] **Step 2: Draw the behavior state machine**

Show `DISARMED`, `ARMED`, and `EXECUTING`; explain one trigger per cycle, preview trigger consumption, missing-odometry rejection, completion, cancellation, and why actions are never queued.

- [ ] **Step 3: Present the six-emotion mapping table**

Use the exact profiles: happy arc left `R=0.40 m`, `+60°`; sad arc right `R=0.40 m`, `-60°`; neutral zero velocity; angry reverse `0.20 m`; surprise `2π`; fear forward `0.20 m`.

- [ ] **Step 4: Explain odometry feedback and bounds**

Document yaw unwrap, distance/angle tolerance, settle `0.30 s`, segment timeout `30 s`, odometry timeout `0.5 s`, speed caps, reset/jump detection, and zero Twist cleanup.

- [ ] **Step 5: Audit safety claims against tests**

For each stated behavior, point to a relevant test name. Mark camera/simulator observations as `\pending` even when the same logic has an automated unit test.

- [ ] **Step 6: Commit**

```bash
git add report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730
git commit -m "docs: describe emotion behavior and safe motion"
```

### Task 4: Write installation, operation and evidence guidance

**Files:**
- Modify: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/05-cai-dat-van-hanh.tex`
- Modify: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/06-kiem-thu-ket-qua.tex`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/HUONG_DAN.md`
- Create: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/HUONG_DAN_CHUP_ANH.md`

**Interfaces:**
- Consumes: `README.md`, scripts, launch files, `docs/acceptance.md`, current Git state, fresh pytest/colcon output, and manual evidence supplied later.
- Produces: reproducible operator steps, verified automated-results table, pending manual matrix, and an exact screenshot checklist.

- [ ] **Step 1: Re-run and capture the evidence baseline**

Run:

```bash
source /opt/ros/humble/setup.bash
pytest -q
colcon build --base-paths . --packages-select tbe4_face_recognition --symlink-install
source install/setup.bash
colcon test --base-paths . --packages-select tbe4_face_recognition
colcon test-result --verbose
ros2 pkg prefix tbe4_face_recognition
git branch --show-current
git rev-parse --short HEAD
```

Expected baseline after immediate-confidence behavior: 102 pytest passed; colcon 102 tests, 0 errors, 0 failures, 0 skipped; application commit `c35bdd5`.

- [ ] **Step 2: Write exact setup and run commands**

Cover venv setup, build, recognition preview, simulator in a separate terminal, undock, preview interaction, explicit `preview_only:=false`, topic inspection, and orderly `Q`/Ctrl+C shutdown.

- [ ] **Step 3: Create the manual-acceptance table**

Include overlay/webcam, six recognized expressions, five moving profiles, neutral stop, no-face/multiple-face stop, camera-close watchdog, odometry loss, single `/cmd_vel` publisher, public repository, and demo video. Initialize unsupported items as `PENDING`, not PASS.

- [ ] **Step 4: Create the screenshot checklist**

Use exact filenames and capture criteria:

1. `01_kien_truc_he_thong.png` — architecture diagram or node/topic graph.
2. `02_overlay_nhan_dien.png` — one face, FER label, confidence and stable status.
3. `03_sau_bieu_cam.png` — evidence covering all six required expressions.
4. `04_topics_observation_status.png` — valid JSON observation and behavior status.
5. `05_preview_zero_cmd_vel.png` — preview trigger with zero Twist.
6. `06_happy_cong_trai.png` — left-arc execution and completion.
7. `07_sad_cong_phai.png` — right-arc execution and completion.
8. `08_angry_lui.png` — reverse profile evidence.
9. `09_surprise_xoay_360.png` — full-turn progress/completion.
10. `10_fear_tien.png` — forward profile evidence.
11. `11_neutral_no_face_stop.png` — neutral or face-loss stop.
12. `12_odom_watchdog.png` — stale/lost odometry stop.
13. `13_kiem_thu_tu_dong.png` — final pytest/colcon summary.

State that images containing a face must be selected by the user and should not expose bystanders.

- [ ] **Step 5: Commit**

```bash
git add report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730
git commit -m "docs: add report operation and evidence guide"
```

### Task 5: Finish conclusions, compile and audit the deliverable

**Files:**
- Modify: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/content/07-ket-luan.tex`
- Modify: report-local files from Tasks 1–4 only.
- Produce: `report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730/main.pdf`

**Interfaces:**
- Consumes: complete report source and evidence matrix.
- Produces: compiled, internally consistent report plus a precise handoff of remaining manual work.

- [ ] **Step 1: Write conclusion and limitations**

Summarize the implemented architecture and verified automation. Keep live recognition accuracy, CPU performance, lighting sensitivity, simulator trajectories, physical robot compatibility, obstacle avoidance, public URL, and video explicitly pending where evidence is absent.

- [ ] **Step 2: Compile twice**

```bash
cd report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Expected: `main.pdf` exists, table of contents and references resolve, and missing live images render only as intentional placeholders. If TeX is unavailable, record the exact missing command/package instead of claiming success.

- [ ] **Step 3: Audit formatting and unsupported claims**

Check the LaTeX log for undefined controls/references and run:

```bash
git diff --check
rg -n -i "PASS|thành công|hoàn thành|đã nhận diện|đã di chuyển" \
  report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730
```

Review every match and retain it only when backed by automated output or real manual evidence.

- [ ] **Step 4: Audit privacy and generated files**

Confirm the report directory contains no `.venv-face`, raw video, unselected face crops, credential-shaped values, or build cache. Verify every image has a documented source.

- [ ] **Step 5: Record final handoff**

Report the PDF path and page count, list remaining placeholders, name the exact manual tests still required, and provide the next command for rebuilding after the user adds screenshots.

- [ ] **Step 6: Commit**

```bash
git add report/Bao_cao_Bai_Thuc_Hanh_4_TB4_Face_Recognition_23020730
git commit -m "docs: complete face emotion practice report"
```

# TurtleBot 4 Face Emotion Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone ROS 2 Humble package that recognizes six facial expressions from a laptop webcam and safely executes the corresponding TurtleBot 4 `/cmd_vel` motion once per stable expression.

**Architecture:** A FER/TFLite recognition node runs from an isolated Python virtualenv, opens the webcam, and publishes validated JSON observations. A system-ROS controller node filters observations, owns the safety state machine and odometry-feedback motion executor, and is the only process that publishes `/cmd_vel`; both nodes exchange only standard ROS messages.

**Tech Stack:** Ubuntu 22.04, Python 3.10, ROS 2 Humble, TurtleBot 4 Simulator/Ignition Fortress, `rclpy`, OpenCV 4.10, FER 25.10.3, TensorFlow CPU 2.15.1, NumPy 1.26.4, pytest, ament/colcon.

**Spec:** `docs/superpowers/specs/2026-11-13-turtlebot-face-emotion-design.md`

## Global Constraints

- Work only in `/home/alex/Interaction/tbe4_face_recognition`; do not modify `tb4_nav2` or `tb4_hand_gesture`.
- Preserve the requested directory and ROS package name `tbe4_face_recognition` exactly.
- Target Ubuntu 22.04, Python 3.10 and ROS 2 Humble.
- The webcam source is `cv2.VideoCapture`; do not use OAK-D or `cv_bridge` in the recognition path.
- The controller node is the sole `/cmd_vel` publisher and runs a 20 Hz wall-time control loop with `use_sim_time=false`.
- `preview_only=true` is the default; motion requires an explicit `preview_only:=false` launch argument.
- Use `/odom` feedback for every non-neutral action; never defer an action that arrived while odometry was unavailable.
- Install AI dependencies only inside `.venv-face`; never run pip against the system ROS Python.
- Install `fer==25.10.3` with `--no-deps`, then explicitly install `tensorflow-cpu==2.15.1`, `numpy==1.26.4`, `opencv-contrib-python==4.10.0.84`, `Pillow==10.4.0`, `requests==2.32.3`, and `setuptools==70.3.0`. This deliberately avoids FER's unused MTCNN/PyTorch dependency.
- Do not store webcam frames or inferred face crops.
- Do not launch Nav2, SLAM, localization or teleop with the interaction controller.

## Review Focus

- Camera frames continue but inference stops: `test_stale_observation_stops_execution` proves no new sequence for `0.75 s` cancels motion.
- Recognition restarts with sequence zero: `test_new_session_stops_and_requires_rearm` proves a new `session_id` cannot inherit an armed or executing state.
- No face, multiple faces, low confidence or `disgust`: `test_invalid_face_observations_request_immediate_stop` proves each becomes an immediate safety stop.
- Yaw wrap, stale odometry and pose jumps: motion and odometry-guard tests prove commands return to zero without corrupting progress.
- A trigger arrives before odometry: `test_missing_odometry_consumes_trigger_without_delayed_start` proves it is rejected and cannot execute later automatically.

---

### Task 1: Package foundation and observation protocol

**Files:**
- Create: `.gitignore`
- Create: `package.xml`
- Create: `resource/tbe4_face_recognition`
- Create: `setup.cfg`
- Create: `setup.py`
- Create: `tbe4_face_recognition/__init__.py`
- Create: `tbe4_face_recognition/protocol.py`
- Create: `test/test_protocol.py`

**Interfaces:**
- Produces: `Observation(session_id: str, sequence: int, emotion: str, confidence: float, face_count: int)`.
- Produces: `encode_observation(value: Observation) -> str` and `decode_observation(payload: str) -> Observation`.
- Produces: `BehaviorStatus(state: str, stable_emotion: str | None, active_action: str | None, reason: str, preview_only: bool, odometry_ready: bool, motion_progress: float)` plus matching encode/decode functions.

- [ ] **Step 1: Initialize the standalone repository and write failing protocol tests**

Run `git init -b main`, then test valid round trips and reject malformed JSON, unknown emotions, empty sessions, negative/non-integer sequences, non-finite/out-of-range confidence, negative face counts and invalid status progress.

- [ ] **Step 2: Run the protocol test and confirm the package is absent**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_protocol.py`

Expected: FAIL during import because `tbe4_face_recognition.protocol` does not exist.

- [ ] **Step 3: Implement the minimal package and strict JSON protocol**

Use frozen dataclasses. Accept raw emotions `happy`, `sad`, `neutral`, `angry`, `surprise`, `fear`, `disgust`, `unknown`; use compact, sorted JSON; reject booleans where an integer is required and reject extra/missing keys so the wire contract cannot drift silently. Register future console entry points `emotion_recognition_node` and `emotion_controller_node` in `setup.py` and install `launch/*.launch.py` plus `config/*.yaml` by glob.

- [ ] **Step 4: Verify the protocol and package metadata**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_protocol.py && python3 setup.py --name`

Expected: tests PASS and package name prints `tbe4_face_recognition`.

- [ ] **Step 5: Commit**

```bash
git add .gitignore package.xml resource setup.cfg setup.py tbe4_face_recognition test/test_protocol.py
git commit -m "feat: establish face emotion ROS protocol"
```

### Task 2: FER adapter and face-result normalization

**Files:**
- Create: `requirements-face.txt`
- Create: `scripts/setup_face_venv.sh`
- Create: `tbe4_face_recognition/emotion_model.py`
- Create: `test/test_emotion_model.py`

**Interfaces:**
- Consumes: `Observation` from Task 1.
- Produces: `DetectedFace(box: tuple[int, int, int, int], emotion: str, confidence: float)`.
- Produces: `FerEmotionModel(detector: object | None = None)` with `analyze(frame: object) -> list[DetectedFace]`.
- Produces: `make_observation(faces: list[DetectedFace], session_id: str, sequence: int) -> Observation`.

- [ ] **Step 1: Write adapter tests using a fake FER detector**

Assert FER score dictionaries choose the highest emotion, confidence is converted from FER's `[0, 1]` score, boxes remain `(x, y, width, height)`, no face yields `unknown/0.0/face_count=0`, and two faces yield `unknown/0.0/face_count=2`. Assert the adapter rejects malformed boxes, unknown score keys and non-finite scores.

- [ ] **Step 2: Run the focused test and verify failure**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_emotion_model.py`

Expected: FAIL because `emotion_model.py` does not exist.

- [ ] **Step 3: Implement the lazy FER adapter and isolated installer**

Only run `from fer.fer import FER` inside `FerEmotionModel.__init__` when no detector is injected; instantiate it as `FER(use_tflite=True, mtcnn=False)`. In `setup_face_venv.sh`, create `.venv-face` with `--system-site-packages`, bootstrap pip only inside that venv, install pinned direct dependencies from `requirements-face.txt`, install FER with `--no-deps`, and finish with an import/model-load check for `fer.fer.FER`, TensorFlow, OpenCV, NumPy and `rclpy`.

- [ ] **Step 4: Verify the adapter without downloading dependencies**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_emotion_model.py`

Expected: PASS using only the injected fake detector; tests must not import TensorFlow or FER.

- [ ] **Step 5: Commit**

```bash
git add requirements-face.txt scripts/setup_face_venv.sh tbe4_face_recognition/emotion_model.py test/test_emotion_model.py
git commit -m "feat: add isolated FER emotion adapter"
```

### Task 3: Temporal emotion filter and inference freshness

**Files:**
- Create: `tbe4_face_recognition/emotion_filter.py`
- Create: `test/test_emotion_filter.py`

**Interfaces:**
- Consumes: `Observation` from Task 1.
- Produces: `FilterResult(normalized: str, stable_emotion: str | None, changed: bool, stop_reason: str | None)`.
- Produces: `EmotionFilter(confidence_threshold: float = 0.55, stable_seconds: float = 0.5, rearm_seconds: float = 0.75, max_observation_gap: float = 0.75)` with `observe(observation: Observation, now: float) -> FilterResult`, `tick(now: float) -> FilterResult | None`, and `reset() -> None`.

- [ ] **Step 1: Write filter tests for stability and all safety inputs**

Cover stable emotion only after `0.5 s`, candidate reset on label change, neutral/unknown stable after `0.75 s`, non-finite/backward time rejection, stale observation timeout and session/sequence rules. Add `test_invalid_face_observations_request_immediate_stop` for no face, multiple faces, low confidence and `disgust`.

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_emotion_filter.py`

Expected: FAIL because `EmotionFilter` is missing.

- [ ] **Step 3: Implement filtering with separate transport and candidate clocks**

Only a strictly increasing sequence in the current session refreshes observation freshness or candidate duration. On session change, return `stop_reason='recognition_restarted'`, reset candidates and adopt the new session. Normalize every unsafe face observation to `unknown` and return its specific immediate stop reason while still allowing `unknown` to accumulate toward re-arm.

- [ ] **Step 4: Verify all temporal edges**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_emotion_filter.py`

Expected: PASS, including `test_stale_observation_stops_execution` at the filter boundary and the Review Focus session test.

- [ ] **Step 5: Commit**

```bash
git add tbe4_face_recognition/emotion_filter.py test/test_emotion_filter.py
git commit -m "feat: stabilize emotion observations safely"
```

### Task 4: One-shot behavior state machine

**Files:**
- Create: `tbe4_face_recognition/behavior.py`
- Create: `test/test_behavior.py`

**Interfaces:**
- Consumes: `FilterResult` from Task 3.
- Produces: `BehaviorDecision(start_action: str | None, cancel_motion: bool)`.
- Produces: `BehaviorController(preview_only: bool)` with `receive(result: FilterResult, now: float, odometry_ready: bool) -> BehaviorDecision`, `complete(now: float) -> None`, `cancel(reason: str) -> None`, and `snapshot(odometry_ready: bool, motion_progress: float = 0.0) -> BehaviorStatus`.

- [ ] **Step 1: Write state-machine tests for all six mappings**

Assert `happy→arc_left`, `sad→arc_right`, `angry→reverse`, `surprise→rotate_full`, `fear→forward`, and `neutral→stop`. Assert one trigger per armed cycle, no queued replacement during execution, neutral/unsafe input cancels, completion remains disarmed, and neutral/unknown must re-arm before another trigger.

- [ ] **Step 2: Add preview and inhibited-motion regression tests**

`test_preview_consumes_trigger_and_reports_preview_completed` expects zero start action plus reason `preview_completed`. `test_missing_odometry_consumes_trigger_without_delayed_start` expects `odometry_unavailable`, remains disarmed after odometry becomes ready, and starts only after re-arm plus a new stable expression. `test_new_session_stops_and_requires_rearm` passes the filter restart result and verifies cancellation.

- [ ] **Step 3: Run tests and verify failure**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_behavior.py`

Expected: FAIL because `BehaviorController` is missing.

- [ ] **Step 4: Implement the minimal `DISARMED`, `ARMED`, `EXECUTING` machine**

Do not store queued actions. Every rejected, completed or canceled trigger returns to `DISARMED`; only stable `neutral` or `unknown` arms it. Fill `BehaviorStatus` with exact reason strings asserted by tests.

- [ ] **Step 5: Verify behavior and protocol together**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_protocol.py test/test_emotion_filter.py test/test_behavior.py`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tbe4_face_recognition/behavior.py test/test_behavior.py
git commit -m "feat: add one-shot emotion behavior state machine"
```

### Task 5: Odometry-feedback motion profiles

**Files:**
- Create: `tbe4_face_recognition/motion.py`
- Create: `test/test_motion.py`

**Interfaces:**
- Produces: `Pose(x: float, y: float, yaw: float)` and `Velocity(linear_x: float, angular_z: float, done: bool, progress: float)`.
- Produces: `MotionConfig(linear_speed=0.10, reverse_speed=0.08, angular_speed=0.40, arc_radius=0.40, arc_angle=math.pi/3, travel_distance=0.20, distance_tolerance=0.008, angle_tolerance=0.025, settle_seconds=0.30, segment_timeout=30.0)`.
- Produces: `MotionExecutor(action: str, start_pose: Pose, now: float, config: MotionConfig)` with `step(pose: Pose, now: float) -> Velocity`.
- Produces: `OdometryGuard(timeout_seconds: float = 0.5)` with `update(pose: Pose, stamp: float, received_at: float) -> str | None`, `ready(now: float) -> bool`, and `pose: Pose | None`.

- [ ] **Step 1: Write numerical simulation tests for five non-neutral profiles**

Integrate returned velocities at `0.02 s`. Assert left/right arcs reach signed `60°` with radius `0.40 m`, reverse/forward reach signed `0.20 m`, full rotation accumulates `2π` across yaw wrap, all outputs respect `0.10 m/s` and `0.40 rad/s`, progress stays in `[0,1]`, and completed profiles emit zero.

- [ ] **Step 2: Write odometry and timeout safety tests**

Reject non-finite pose/time/config, repeated stamps do not refresh freshness, backward stamps return `odom_reset`, translation jump above `0.5 m` or yaw jump above `1.0 rad` returns `odom_jump`, stale data is not ready, and a stuck motion raises `motion_timeout`.

- [ ] **Step 3: Run tests and verify failure**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_motion.py`

Expected: FAIL because motion interfaces are absent.

- [ ] **Step 4: Implement bounded profiles and unwrap angular progress**

Use Euclidean displacement for line profiles, accumulated wrapped yaw for turns/arcs, heading correction only for line motion, constant signed curvature for arcs, a zero-velocity settle phase and strict configuration validation.

- [ ] **Step 5: Verify motion deterministically**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_motion.py`

Expected: PASS without ROS or Gazebo.

- [ ] **Step 6: Commit**

```bash
git add tbe4_face_recognition/motion.py test/test_motion.py
git commit -m "feat: add bounded TurtleBot motion profiles"
```

### Task 6: ROS controller adapter and safety loop

**Files:**
- Create: `config/controller.yaml`
- Create: `tbe4_face_recognition/emotion_controller_node.py`
- Create: `test/test_controller_helpers.py`

**Interfaces:**
- Consumes: protocol, filter, behavior and motion interfaces from Tasks 1, 3, 4 and 5.
- Produces: ROS node `emotion_controller_node` subscribing `/emotion_observation` and `/odom`, publishing `/cmd_vel` and `/emotion_behavior_status`.
- Produces: `pose_from_odometry(message: nav_msgs.msg.Odometry) -> tuple[Pose, float]` for a focused adapter test.

- [ ] **Step 1: Write controller adapter tests**

Use real ROS message classes to assert quaternion normalization/yaw conversion and timestamp extraction. Reject zero-norm/non-finite quaternions. Add a fake-publisher harness around a factored `compute_control(now)` method to prove stale observations, invalid odometry and controller cleanup each produce zero Twist.

Name the stale-observation integration case `test_stale_observation_stops_execution`; first start a motion, advance wall time beyond `0.75 s` without a new sequence, and assert both the returned velocity and published Twist are zero.

- [ ] **Step 2: Run tests and verify failure**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_controller_helpers.py`

Expected: FAIL because the controller module is missing.

- [ ] **Step 3: Implement the ROS adapter at 20 Hz wall time**

Declare every YAML parameter, reject `use_sim_time=true`, use sensor-data QoS for `/odom`, process observation JSON without throwing out of callbacks, create/cancel a `MotionExecutor` only from behavior decisions, and publish one Twist plus one status every timer tick. On shutdown, publish zero Twist before destroying the node.

- [ ] **Step 4: Verify controller safety and pure modules**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_controller_helpers.py test/test_behavior.py test/test_motion.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add config/controller.yaml tbe4_face_recognition/emotion_controller_node.py test/test_controller_helpers.py
git commit -m "feat: publish safe emotion-driven velocity commands"
```

### Task 7: Webcam recognition node and live overlay

**Files:**
- Create: `config/recognition.yaml`
- Create: `tbe4_face_recognition/emotion_recognition_node.py`
- Create: `test/test_recognition_helpers.py`

**Interfaces:**
- Consumes: `FerEmotionModel`, observation protocol and behavior-status protocol from Tasks 1 and 2.
- Produces: ROS node `emotion_recognition_node` publishing `/emotion_observation`, subscribing `/emotion_behavior_status`, and owning webcam/window cleanup.
- Produces: `draw_overlay(frame: object, faces: list[DetectedFace], observation: Observation, status: BehaviorStatus | None) -> object`.

- [ ] **Step 1: Write recognition helper tests**

With small NumPy frames and injected detected faces, assert overlay preserves dimensions, does not mutate the input, clips boxes to frame bounds and tolerates missing/malformed status. Test inference scheduling so capture/display can run at 20 Hz while observation sequence advances only after a completed 5 Hz inference.

- [ ] **Step 2: Run tests and verify failure**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_recognition_helpers.py`

Expected: FAIL because the recognition module is missing.

- [ ] **Step 3: Implement webcam ownership, inference and cleanup**

Generate an eight-character UUID-derived `session_id` at startup. Open `camera_index` with V4L2, request 640x480 and buffer size 1, mirror before inference/display, publish only when inference completes, and display raw/stable confidence plus controller state. `Q`, frame loss, exception and ROS shutdown must release the camera and destroy the window; no code path writes an image to disk.

- [ ] **Step 4: Verify helpers and import boundaries**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_recognition_helpers.py test/test_emotion_model.py`

Expected: PASS without opening a webcam and without importing FER in fake-model tests.

- [ ] **Step 5: Commit**

```bash
git add config/recognition.yaml tbe4_face_recognition/emotion_recognition_node.py test/test_recognition_helpers.py
git commit -m "feat: recognize facial emotions from webcam"
```

### Task 8: Launch, scripts, installation checks and operator guide

**Files:**
- Create: `launch/recognition.launch.py`
- Create: `launch/interaction.launch.py`
- Create: `launch/simulation.launch.py`
- Create: `scripts/build.sh`
- Create: `scripts/run_recognition.sh`
- Create: `scripts/run_interaction.sh`
- Create: `test/test_package_assets.py`
- Create: `docs/acceptance.md`
- Create: `README.md`
- Modify: `setup.py`
- Modify: `package.xml`

**Interfaces:**
- Consumes: both ROS nodes and YAML files from Tasks 6 and 7.
- Produces: `./scripts/build.sh`, `./scripts/run_recognition.sh`, and `./scripts/run_interaction.sh preview_only:=false` operator entry points.

- [ ] **Step 1: Write failing installation and launch-contract tests**

Assert setup installs both YAML files and all three launch files; scripts are executable and contain no `sudo`; interaction launch exposes `python_executable`, `camera_index`, `show_window`, and `preview_only`; simulation launch includes upstream TurtleBot 4 with `nav2=false`, `slam=false`, `localization=false`; no launch starts two `/cmd_vel` sources.

- [ ] **Step 2: Run the asset test and verify failure**

Run: `source /opt/ros/humble/setup.bash && pytest -q test/test_package_assets.py`

Expected: FAIL because launch files and run scripts do not exist.

- [ ] **Step 3: Implement launch and operator scripts**

Follow `tb4_nav2`'s upstream TurtleBot include pattern but do not copy its maps, Nav2 or YOLO assets. Prefix only the recognition node with `.venv-face/bin/python`; launch the controller normally. Each run script resolves its repository directory, verifies the venv/install prerequisites and sources only ROS Humble plus this project's install.

- [ ] **Step 4: Write the Vietnamese README**

Document setup/build, preview-first workflow, simulator launch in a separate terminal, undock, explicit motion enable, six mappings and exact defaults, topic inspection, single-`/cmd_vel`-publisher rule, `Q`/Ctrl+C shutdown, troubleshooting, automated tests and a manual acceptance checklist that does not claim unperformed hardware tests.

- [ ] **Step 5: Run the full automated proof**

Run:

```bash
source /opt/ros/humble/setup.bash
pytest -q
colcon build --base-paths . --packages-select tbe4_face_recognition --symlink-install
source install/setup.bash
ros2 pkg prefix tbe4_face_recognition
```

Expected: all tests PASS, colcon succeeds, and the prefix resolves inside `/home/alex/Interaction/tbe4_face_recognition/install`.

- [ ] **Step 6: Run static package checks**

Run: `source /opt/ros/humble/setup.bash && colcon test --base-paths . --packages-select tbe4_face_recognition && colcon test-result --verbose`

Expected: zero test failures.

- [ ] **Step 7: Record manual checks without fabricating results**

Run webcam preview and simulator checks only when hardware/display are available. Add a short `docs/acceptance.md` table with `PASS`, `FAIL` or `NOT RUN` for webcam, six expressions, six motions, neutral stop, no-face stop, camera-close stop and odometry-loss stop.

- [ ] **Step 8: Commit**

```bash
git add launch scripts test/test_package_assets.py README.md docs/acceptance.md setup.py package.xml
git commit -m "docs: complete TurtleBot face emotion demo workflow"
```

## Self-Review Result

- Spec coverage: every goal, safety stop, motion mapping, preview rule, environment constraint and acceptance condition maps to a task above.
- Step scan: implementation steps name exact interfaces and decisions; tests contain the required assertions without transcribing full implementations.
- Type consistency: Tasks 2–7 consume the `Observation`, `BehaviorStatus`, `FilterResult`, `BehaviorDecision`, `Pose`, `Velocity` and `MotionExecutor` names exactly as introduced.
- Review Focus: each listed failure mode has a named test in Tasks 3–6.
- Proportion: the plan focuses on decisions, interfaces and proof; internal helper decomposition remains with the implementer.

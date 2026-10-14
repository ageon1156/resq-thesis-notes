# 02b — Features missing from the report: verified fact sheets

This file answers "the report doesn't cover all the features; I need to add some." Each sheet gives only facts checked against the code at `HEAD = 15567ea5f`: what the feature does, how it works, the real constants, where the code is, and its honest limits. It is deliberately **not** finished prose. Write each section in your own words, using these facts as the checklist. Specific numbers and stated limitations also read far better than generic benefit paragraphs.

**Recommended priority** (by strength as a contribution and how easy it is to defend in a viva):
1. Rescuer assignment (Hungarian algorithm): your most substantial algorithm
2. Background silent-node service: you have real measurements for it (03 §2.1)
3. Priority gating under (simulated) congestion: it replaces the incorrect Table 3.3
4. Geofenced hazard zones: logs its own evaluation metrics
5. SOS beacon and quick action: extends the existing SOS chapter
6. Voice messages over Codec2: already mentioned in one line; needs facts and a credit
7. Offline emergency guide: simple, but a visible feature
8. Message Mule: describe carefully (see its limitations)

A note on timing: features 4 and 8 were committed on **2026-09-15**, after the report's May 2026 date. Include them only if the submitted code is the September version. In that case, remove "dynamic geofencing alerts" from Future Enhancements (p. 43), because it's implemented.

---

## 1. Rescuer↔victim assignment (Hungarian algorithm) and incident-commander view

- **What it does:** given the triage pins on the map and the rescuer nodes heard recently, it computes a one-to-one assignment of rescuers to victims. The cost is distance weighted by triage urgency, so RED victims attract the nearest rescuers. The result is broadcast so each rescuer sees their task, and the commander can lock an assignment so later recomputations don't change it.
- **How it works:**
  - *Eligible rescuers*: all nodes except ourselves and ignored nodes, heard within **7,200 s (2 h)** ([AssignmentEngine.kt:29-41](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/AssignmentEngine.kt#L29-L41)).
  - *Urgency weights*: RED 0.25, YELLOW 1.0, GREEN 2.0, BLACK 4.0 ([AssignmentEngine.kt:22-27](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/AssignmentEngine.kt#L22-L27)). A lower weight makes a pin cheaper to reach, so it gets assigned first.
  - *Cost*: `distance(rescuer, pin) in m × weight`. If a rescuer has no GPS, the cost is just `weight` ([:76-90](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/AssignmentEngine.kt#L76-L90)).
  - *More pins than rescuers*: pins are sorted by weight and only the most urgent *k* are offered (k = number of free rescuers) ([:68-74](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/AssignmentEngine.kt#L68-L74)).
  - *Solver*: Hungarian (Kuhn–Munkres) with dual potentials `u`, `v` and augmenting paths, O(n³); a non-square matrix is padded with zeros ([HungarianSolver.kt:5-30+](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/HungarianSolver.kt#L5)).
  - *Locked assignments* are excluded from the optimisation and merged back in ([:56-57, 103](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/AssignmentEngine.kt#L56-L57)). Lock and unlock are in `TriageMapViewModel.lockAssignment`/`unlockAssignment`.
  - *Sharing*: `AssignmentPacket` JSON on port 256 per rescuer, with a `locked` flag ([TriageMapViewModel.kt ~152-163](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/TriageMapViewModel.kt#L152-L163); [AssignmentPacket.kt](../core/model/src/main/kotlin/org/meshtastic/core/model/triage/AssignmentPacket.kt)). Claims use `ClaimPinPacket`; conflicting pins are merged by [TriageMergeEngine.kt:14](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/TriageMergeEngine.kt#L14).
  - *UI*: `IncidentCommanderComponents.kt` (236 lines), `TriageMapUiComponents.kt`.
- **Commits:** `f96b39052` (2026-02-19), `62a5326d2` (2026-03-07).
- **Evidence it runs:** S2 logs show a `MANUAL_TRIAGE_PIN` and a `CLAIM_PIN` for the same pin crossing between the two phones and being decoded (03 §2.4).
- **Limitations to state:** straight-line distance, not route distance. Weights are hand-chosen, not calibrated. No assignment packets appear in the captured logs. **Uncommitted work exists:** `feature/map/src/test/.../triage/AssignmentEngineTest.kt` (164 lines, 9 tests covering nearest-distance assignment, priority over distance, more pins than rescuers, locking, missing GPS and empty input; file dated 2026-09-15 22:20), plus the `testImplementation(libs.junit)` line in `feature/map/build.gradle.kts`. Both are untracked or modified and not committed, and I did not run them. Commit and run them, and you can cite "9 unit tests pass" in the report. If you adapted the solver from a reference implementation, cite it. Its origin is **not verified**.
- **Cite:** H. W. Kuhn, "The Hungarian method for the assignment problem," *Naval Research Logistics Quarterly*, 1955; J. Munkres, *J. SIAM*, 1957.
- **Easy evaluation to add:** on top of the existing scenario tests, add a test with random cost matrices that compares `HungarianSolver` against brute force for n ≤ 8 and times it for n = 10…100. This gives you a correctness and runtime table without any field work.

## 2. Background silent-node detection service (the detector that actually ran)

- **What it does:** a background component in the mesh service that actively pings tracked nodes. It moves a node through ONLINE → SILENT → CONFIRMED_SILENT, broadcasts a silence report and a text alert with the node's last GPS position, auto-places a RED triage pin, and removes the pin when the node returns.
- **Constants** ([SilentNodeDetector.kt:501-515](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L501-L515)): silence timeout 900 s; scan every 15 s; ping every 120 s; **2 missed pings → SILENT, 3 → CONFIRMED**; unconfirmed promote after 600 s; minimum confirm delay 300 s; pings and reports use hop limit 2.
- **Ping packet:** `HEARTBEAT_PING|<ms>`, unicast, `PRIVATE_APP`, want_ack, BACKGROUND priority ([:400-416](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L400-L416)). Any packet *from* the node resets the missed count ([:122-127](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L122-L127)). Incoming `HB|` heartbeats count as proof of life ([:460-464](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L460-L464)).
- **Mesh actions:** `broadcastSilenceReport` ([:419](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L419)), `broadcastAlertToChannel` ([:282](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L282)), `autoPlaceTriagePin` ([:301](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L301)), `broadcastGracefulExit` (`MESH_EXIT|…`).
- **Commits:** `0494376d0` (02-15), `c19ed2a12` (02-18), `43623ee41` (02-20, a fix for false alerts during DeviceSleep/BLE reconnect), plus a 433-line unit test.
- **Measured (03 §2.1, n = 1):** last heard → SILENT 316 s, → CONFIRMED 436 s, node back → "online" 26 s.
- **Design point worth writing up:** ACKs to pings are deliberately *not* treated as proof of life. The logs show `isAck=true` for pings to a node that was off (03 §2.3), so an ACK-based detector would have missed the outage.
- **Limitations:** n = 1. The relation to the simpler `detectSilentNode()` on the map (the one described in the current report) needs explaining. These are two detectors, and you should either justify both or merge them. Where the `HB|` heartbeats come from is **not in this repo** (see open questions).

## 3. Priority gating under congestion (replaces Table 3.3)

- **What it does:** when channel utilisation is high, the app refuses to queue low-priority text messages, so the airtime stays free for urgent ones.
- **Rule** ([MeshCommandSender.kt:116-127](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L116-L127), thresholds at [:429-431](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L429-L431)):

  | Channel utilisation | Normal (DEFAULT) | High | Critical Alert (ALERT) |
  |---|---|---|---|
  | < 70 % | sent | sent | sent |
  | 70–85 % | **rejected** ("only high-priority messages allowed") | sent | sent |
  | ≥ 85 % | rejected | **rejected** | sent |

  Only `TEXT_MESSAGE_APP` packets are gated. Rejected messages are marked ERROR in the UI.
- **Important:** utilisation comes from `simulatedChannelUtil`, a slider in the node-list screen ([NodeRepository.kt:178-181](../core/data/src/main/kotlin/org/meshtastic/core/data/repository/NodeRepository.kt#L178-L181)), not from the radio's measured `channel_utilization`. Present it as a **simulation harness for demonstrating the policy**, and list "use the radio's real channel-utilisation telemetry" as future work.
- **Commit:** `62a5326d2` (2026-03-07). The priority selector itself is from `4d28a45ef` (2026-01-31).
- **Evaluation to add:** test 4 in 03 §4 (accept/reject counts at 0 / 75 / 90 %).

## 4. Geofenced hazard zones (Sep 2026)

- **What it does:** users draw polygon hazard zones (FLOOD, FIRE, CHEMICAL, STRUCTURAL, ROADBLOCK, OTHER, [HazardZone.kt:6](../core/model/src/main/kotlin/org/meshtastic/core/model/hazard/HazardZone.kt#L6)) and share them over the mesh. Each phone watches its own GPS and notifies on **enter and exit**.
- **How it works:**
  - Point-in-polygon uses even-odd ray casting on lat/lon as a plane ([HazardZone.kt:35-55](../core/model/src/main/kotlin/org/meshtastic/core/model/hazard/HazardZone.kt#L35-L55)).
  - Distance to the boundary is computed on a local flat projection ([:57-82](../core/model/src/main/kotlin/org/meshtastic/core/model/hazard/HazardZone.kt#L57-L82)).
  - The enter/exit state machine is in [HazardZoneMonitor.kt:27-32](../app/src/main/java/com/geeksville/mesh/service/HazardZoneMonitor.kt#L27-L32).
  - Detection is **purely local**, so it works with the radio disconnected.
  - Zones are shared as JSON with coordinates rounded to 6 decimals, about 0.1 m ([HazardZonePackets.kt:23-72](../core/model/src/main/kotlin/org/meshtastic/core/model/hazard/HazardZonePackets.kt#L23-L72)).
- **Built-in evaluation data:** every alert stores GPS accuracy, distance to boundary and **detection latency** (`now − location.time`) ([HazardZoneMonitor.kt `evaluate`](../app/src/main/java/com/geeksville/mesh/service/HazardZoneMonitor.kt#L40)), viewable in `HazardZoneLogScreen`. Walk in and out of a test zone 20 times and you have a results table.
- **Commits:** `34b4f9531`, `45ed1f204`, `e59cea170` (all 2026-09-15). Unit tests: `HazardZoneTest.kt` (102 lines), `HazardZoneMonitorTest.kt` (39 lines).
- **Limitations:** planar approximation (fine at city scale, wrong across the antimeridian or near the poles); GPS jitter near the edge can cause repeated enter/exit alerts (no hysteresis is implemented); zones have only an `active` flag and no expiry time ([HazardZone.kt:10-18](../core/model/src/main/kotlin/org/meshtastic/core/model/hazard/HazardZone.kt#L10-L18)).

## 5. SOS: repeating location beacon and quick action

- The existing chapter covers the single broadcast. It doesn't cover these:
  - after sending, a **beacon re-broadcasts an updated location every 2 min** until stopped ([SOSBeaconController.kt:31, 73-81](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSBeaconController.kt#L31-L81)), with messages formatted "SOS UPDATE … (Nm since SOS)" ([SOSMessage.kt:11-17](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSMessage.kt#L11-L17));
  - a visual signal strobe (350 ms on / 350 ms off, [:32-33](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSBeaconController.kt#L32-L33));
  - a **quick-access notification action** that fires SOS without opening the app ([SOSReceiver.kt:20-36](../app/src/main/java/com/geeksville/mesh/service/SOSReceiver.kt#L20-L36)).
- Also correct the current text: the safeguard is a confirmation dialog, not a countdown (02 C1), and the priority is ALERT, not RELIABLE (02 C3).
- **Limitations:** the location goes out as free text at 4-decimal precision (≈ 11 m) on channel 0, which uses the public default key (02 F1). No SOS appears in the captured logs.

## 6. Voice messages over Codec2

- **Pipeline:**
  1. Record up to **5 s** at 8 kHz mono 16-bit ([AudioRecorder.kt:13-16](../core/audio/src/main/kotlin/org/meshtastic/core/audio/AudioRecorder.kt#L13-L16)).
  2. Encode with **Codec2 at 1,200 bit/s** ([Codec2Wrapper.kt:21](../core/audio/src/main/kotlin/org/meshtastic/core/audio/Codec2Wrapper.kt#L21)) through JNI (`app/src/main/cpp/codec2_jni.cpp`).
  3. Split into ≤ 216-byte fragments with a 14-byte binary header (index, total, 8-byte session ID, timestamp) ([VoiceFragment.kt:35-61](../core/model/src/main/kotlin/org/meshtastic/core/model/voice/VoiceFragment.kt#L35-L61)).
  4. Send on `AUDIO_APP`, 500 ms apart ([VoiceMessageViewModel.kt:35-36, 129, 142](../feature/voicemessage/src/main/kotlin/org/meshtastic/feature/voicemessage/VoiceMessageViewModel.kt#L35-L36)).
  5. The receiver reassembles by session ID ([MeshDataHandler.kt:193-202](../app/src/main/java/com/geeksville/mesh/service/MeshDataHandler.kt#L193-L202)).
- **Back-of-envelope (state it as calculation, not measurement):** 5 s × 1,200 bit/s = 6,000 bits = 750 bytes, which is 4 fragments and about 1.5 s of inter-fragment gaps, before LoRa airtime.
- **Must credit:** Codec2 © David Rowe, LGPL-2.1, vendored in `app/src/main/cpp/codec2/` (116 files). Its LGPL notice must accompany the app.
- **Limitations:** no retransmission of lost fragments was found in the voice code, so if one fragment is lost the whole message fails. No voice traffic appears in the captured logs. Commit `62a5326d2`.

## 7. Offline emergency first-aid and survival guide

- **Content** (bundled JSON, `app/src/main/assets/emergency_guide.json`, 787 lines):
  - 12 first-aid topics: severe bleeding, unconscious person, adult CPR, choking, shock, burns, fractures, head injury, snake bite, heat stroke, hypothermia, drowning;
  - 5 disaster topics: earthquake, flood, fire, cyclone/severe storm, landslide;
  - 4 basic-survival topics: shelter, safe water, food safety, hygiene;
  - emergency contacts (3 groups), plus a disclaimer dialog.
- **Code:** `feature/emergency` (13 files), [EmergencyJsonDataSource.kt:11](../feature/emergency/src/main/kotlin/org/meshtastic/feature/emergency/data/EmergencyJsonDataSource.kt#L11). Commit `9c7c71f47` (2026-01-29).
- **Must state:** where the medical text came from. The JSON lists IFRC 2020, WHO, St John Ambulance, Red Cross, FEMA and UK Resuscitation Council as sources; add these to the reference list. Say whether the text was written or paraphrased, and that it was not reviewed by a medical professional (if true).

## 8. Message Mule (delay-tolerant retry), Sep 2026

- **What it actually does** (read the class comment, [MessageMuleRelay.kt:21-27](../app/src/main/java/com/geeksville/mesh/service/MessageMuleRelay.kt#L21-L27)): when a **direct text message this device sent** fails, the device keeps it ("picks it up"). Failure means any NAK for it ([MeshDataHandler.kt:627](../app/src/main/java/com/geeksville/mesh/service/MeshDataHandler.kt#L627)), or the normal retry prompt being declined or exhausted ([:558-561](../app/src/main/java/com/geeksville/mesh/service/MeshDataHandler.kt#L558-L561)). Only own, non-broadcast `TEXT_MESSAGE_APP` packets are eligible ([:500-502](../app/src/main/java/com/geeksville/mesh/service/MeshDataHandler.kt#L500-L502)). It retries every **5 min** and immediately whenever it hears the destination node, then gives up after **48 h** ([:58-89, 111-112](../app/src/main/java/com/geeksville/mesh/service/MessageMuleRelay.kt#L58-L112)). Status goes CARRYING → DELIVERED / ABANDONED, and a log screen shows it.
- **Careful wording:** the sender carries only **its own** undelivered messages, as the phone physically moves. It does **not** pick up and carry other users' messages. In DTN terms this is store-and-retry at the source, not a data mule relaying third-party traffic. Calling it a "relay" in the report would overclaim.
- **Commits:** `34b4f9531`, `45ed1f204` (2026-09-15). No tests, and no traffic in the logs.

---

## Also add (one or two sentences each)
- **BLE reliability work** (Sep 2026): connection and handshake timeouts (`b3936c75f`), auto-reconnect after link errors (`15567ea5f`). The measured median recovery is 17.9 s (03 §2.5).
- **Scope reductions:** the upstream firmware-update module, traceroute map and Google Maps were removed (`1b0e9790c`, `c19ed2a12`).
- **UI redesign** ("Organic/Atlas" theme): mention it briefly; it isn't a research contribution.

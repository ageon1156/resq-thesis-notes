# 02 — Report Claims vs. Code

- **Report:** `C:\Users\searc\Downloads\DOCS\done.pdf`, "Offline Emergency Communication Application Using Hybrid BLE and LoRa Technology", May 2026. Text was extracted with `pdftotext`. Page numbers below are the report's printed page numbers.
- **Code:** `HEAD = 15567ea5f`, 2026-09-15.
- **"Upstream"** means the line was written by Meshtastic-Android contributors before the fork point `9266caae9`; see 01-contribution-map.

**Limitation:** the code snippets in §§4.1–5.2 (pp. 24–36) are embedded images, and the extracted text shows only a blank after "as follows:". Those images were **not compared**. Snippets that appear as text (Appendix A1, pp. 47–54, and inline constants) were compared.

Verdicts: ✅ matches · 🟡 partially matches · ❌ contradicted · ⬜ not found / not verifiable in this repo.

---

## A. Positioning and architecture

| # | Claim (page) | Verdict | Evidence |
|---|---|---|---|
| A1 | The system is "an Android-based disaster communication application" whose "primary contribution … lies in the software architecture" (pp. 2–3). Meshtastic is mentioned only as "firmware" (p. 21, 32) and "documentation [10]" (p. 10) | ❌ **Material omission** | The app *is* Meshtastic-Android: `APPLICATION_ID=com.geeksville.mesh` ([config.properties:9](../config.properties#L9)); 5,637 of 5,681 commits are upstream; the BLE transport, protobuf protocol, Room DB, messaging, paging, reactions, maps and settings are upstream code (01-contribution-map §3). The report never says the app is a fork of an existing open-source app |
| A2 | Title: "Hybrid **BLE** and LoRa" | 🟡 | BLE is used **only** as the phone↔radio link ([NordicBleInterface.kt:215-221](../app/src/main/java/com/geeksville/mesh/repository/radio/NordicBleInterface.kt#L215-L221)). No phone-to-phone BLE exists: a search for `BluetoothLeAdvertiser`, `AdvertiseSettings`, `BluetoothGattServer`, `openGattServer` and `startAdvertising` in `app/ core/ feature/` returns nothing. "Hybrid" overstates this; say "BLE-tethered LoRa" |
| A3 | Modular `app/ core/ feature/` structure; ViewModels, repositories, service layer (pp. 22, 24, 32, 47) | ✅ (upstream design) | [settings.gradle.kts:3-27](../settings.gradle.kts#L3-L27). The structure is upstream's; you added `feature/{emergency,sos,voicemessage}` and `core/audio` |
| A4 | Appendix A1.1 tree: `core/{database,model,proto,strings}`, `feature/{messaging,sos,map}` (p. 47) | 🟡 | Incomplete. Also present: `core/{audio,data,datastore,di,navigation,network,prefs,service,ui,…}` and `feature/{emergency,voicemessage,node,settings,intro}` |
| A5 | "If a node becomes unavailable, the network dynamically adjusts to route messages through alternative paths" (p. 2) | ⬜ | Routing is done by the radio firmware (managed flooding), which is not in this repo. The app only sets `hopLimit` ([MeshCommandSender.kt:155](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L155)) |
| A6 | "When connectivity is restored, synchronization mechanisms ensure consistency **between nodes**" (p. 3) | 🟡 | Only phone→radio resend exists: `offlineSentPackets` is replayed on reconnect ([MeshCommandSender.kt:168-185](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L168-L185), upstream, James Rich 2026-01-02). No node-to-node sync existed at report time. Message Mule (Sept 2026) is the closest feature |
| A7 | Minimum Android 8.0 (p. 21) | ✅ | `MIN_SDK=26` ([config.properties:10](../config.properties#L10)) |
| A8 | Hardware: Heltec LoRa V3.2, ESP32-S3, SX1262, 4000 mAh LiPo (p. 21) | ⬜ | Not determinable from app code; see 03-log-analysis for any hardware model reported in logs |
| A9 | Software: Kotlin, Room, Paging 3, BLE libraries, Protobuf (p. 21) | ✅ | Paging: [MessageViewModel.kt:97](../feature/messaging/src/main/kotlin/org/meshtastic/feature/messaging/MessageViewModel.kt#L97) (upstream). Room: `core/database`. Protobuf: `core/proto` (submodule). BLE: Nordic BLE library in `NordicBleInterface.kt` |

## B. Messaging and priority

| # | Claim (page) | Verdict | Evidence |
|---|---|---|---|
| B1 | User selects priority with a `rememberSaveable` state variable (pp. 24, 34, 51) | ✅ | [Message.kt:162](../feature/messaging/src/main/kotlin/org/meshtastic/feature/messaging/Message.kt#L162), with options at [Message.kt:763-765](../feature/messaging/src/main/kotlin/org/meshtastic/feature/messaging/Message.kt#L763-L765) ("Normal", "High", "Critical Alert"). Your commit `4d28a45ef` |
| B2 | Listing `mutableStateOf(Priority:Int.DEFAULT_VALUE)`; "Priority values are defined within the **Priority:Int** enumeration" (pp. 26, 33, 51) | ❌ | Not valid Kotlin. The code is `MeshPacket.Priority.DEFAULT_VALUE`, and the enum is `MeshPacket.Priority` from the upstream `meshtastic/protobufs` submodule. "Priority:Int" looks like a find-and-replace artefact; an examiner who knows Kotlin will spot it |
| B3 | `fun sendMessage(str, contactKey, replyId, priority: Int = 0)` builds `DataPacket(...).apply { this.priority = priority }` (pp. 34, 51) | ✅ | [MessageViewModel.kt:152-177](../feature/messaging/src/main/kotlin/org/meshtastic/feature/messaging/MessageViewModel.kt#L152-L177) |
| B4 | Priority "mapped directly to protocol-level packet scheduling" in firmware; emergency traffic "bypasses routine traffic" (pp. 3, 17, 26, 40) | 🟡 / ⬜ | The app does copy priority into `MeshPacket.priority` ([MeshCommandSender.kt:149-157](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L149-L157), upstream). Whether the firmware's TX queue honours it is **not verifiable in this repo**; cite the firmware source if you keep the claim |
| B5 | Table 3.3: HIGH = "ACK-based confirmation, preempts lower priority"; ALERT = "immediate broadcast with **elevated hop limit**, ACK-gated" (p. 18) | ❌ | (a) `wantAck` defaults to `true` for **every** packet regardless of priority ([DataPacket.kt:44](../core/model/src/main/kotlin/org/meshtastic/core/model/DataPacket.kt#L44)). (b) Chat messages never set `hopLimit` ([MessageViewModel.kt:173-175](../feature/messaging/src/main/kotlin/org/meshtastic/feature/messaging/MessageViewModel.kt#L173-L175)), so a "Critical Alert" chat message uses the same channel hop limit as a Normal one (default 3, [Channel.kt:50](../core/model/src/main/kotlin/org/meshtastic/core/model/Channel.kt#L50)). Only the SOS packet uses `hopLimit = 7`. (c) No app-side pre-emption: the offline queue is a plain FIFO list ([MeshCommandSender.kt:168-172](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L168-L172)) |
| B6 | (Not in report) **Congestion gating**: with channel utilisation ≥ 70 %, Normal text messages are *rejected*; at ≥ 85 % everything below ALERT is rejected | — omitted | [MeshCommandSender.kt:116-127](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L116-L127), thresholds at [:429-431](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L429-L431) (your commit `62a5326d2`). ⚠ The utilisation value is **`simulatedChannelUtil`**, set from a slider in the node list ([NodeRepository.kt:178-181](../core/data/src/main/kotlin/org/meshtastic/core/data/repository/NodeRepository.kt#L178-L181), [NodeListScreen.kt:109-118](../feature/node/src/main/kotlin/org/meshtastic/feature/node/list/NodeListScreen.kt#L109-L118)), not the radio's real channel utilisation. This is the actual priority mechanism you built, and it differs from what Table 3.3 describes |
| B7 | Message persistence in Room; deduplicated by message ID before insert (pp. 25, 33, 50) | ✅ | Dedup scoped to `(packet_id, contact_key)`: [PacketDao.kt:276](../core/database/src/main/kotlin/org/meshtastic/core/database/dao/PacketDao.kt#L276), used at [MeshDataHandler.kt:714](../app/src/main/java/com/geeksville/mesh/service/MeshDataHandler.kt#L714) (your fix `db69f3192`); Room persistence is upstream |
| B8 | Paging 3 for large histories (pp. 26, 34) | ✅ (upstream) | [MessageViewModel.kt:97](../feature/messaging/src/main/kotlin/org/meshtastic/feature/messaging/MessageViewModel.kt#L97); blame: Mac DeCourcy, 2025-11-24 |
| B9 | Reactions and reply support (p. 17) | ✅ (upstream) | `feature/messaging/.../component/MessageActions.kt`; reactions introduced upstream by Phil Oliver (`886e9cfed`, 2025-10-12) |
| B10 | Voice messages: "Protobuf", "compressed audio segments, fragmentation, reassembly" (pp. 17, Table 3.2) | 🟡 | Codec2 at 1200 bps ([Codec2Wrapper.kt:21](../core/audio/src/main/kotlin/org/meshtastic/core/audio/Codec2Wrapper.kt#L21)); ≤ 216-byte fragments sent 500 ms apart ([VoiceMessageViewModel.kt:35-36](../feature/voicemessage/src/main/kotlin/org/meshtastic/feature/voicemessage/VoiceMessageViewModel.kt#L35-L36)) on `AUDIO_APP` ([:129](../feature/voicemessage/src/main/kotlin/org/meshtastic/feature/voicemessage/VoiceMessageViewModel.kt#L129)). The fragment format is a **custom 14-byte binary header, not Protobuf** ([VoiceFragment.kt:35-61](../core/model/src/main/kotlin/org/meshtastic/core/model/voice/VoiceFragment.kt#L35-L61)). The report never names Codec2 or credits its author (LGPL-2.1) |

## C. SOS

| # | Claim (page) | Verdict | Evidence |
|---|---|---|---|
| C1 | "A visible **countdown timer** allows cancellation" (p. 18) | ❌ | No countdown in `feature/sos`. Accidental activation is guarded by a **confirmation dialog** ([SOSScreen.kt:87-90](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSScreen.kt#L87-L90), [:359-390](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSScreen.kt#L359-L390); [SOSViewModel.kt:54-62](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSViewModel.kt#L54-L62)) |
| C2 | Packet: `to = ID_BROADCAST`, `hopLimit = 7`, `wantAck = true`, `priority = ALERT_VALUE` (p. 52) | ✅ | [SOSMessage.kt:32-40](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSMessage.kt#L32-L40) |
| C3 | §4.1.3: "the packet is assigned an elevated priority (**RELIABLE**)" (p. 27) | ❌ | The code uses `ALERT` ([SOSMessage.kt:39](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSMessage.kt#L39)). The report also contradicts itself, since p. 52 says ALERT |
| C4 | "The `sendSOS()` function" (pp. 27, 35) | ❌ (name) | No `sendSOS` exists. The flow is `SOSViewModel.confirmAndSendSOS()` ([SOSViewModel.kt:61-75](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSViewModel.kt#L61-L75)) → `buildSosPacket()` |
| C5 | "Constructed using **Protobuf builders**" (pp. 27, 35) | 🟡 | Built as a Kotlin `DataPacket` and converted to protobuf later in the upstream `MeshCommandSender.sendNow` ([:149-160](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L149-L160)) |
| C6 | Includes the sender's last known location (pp. 18, 22) | ✅ | Free text, `"Location: %.4f, %.4f"` plus a Google Maps URL ([SOSMessage.kt:11-30](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSMessage.kt#L11-L30)). Note that 4 decimal places ≈ 11 m precision |
| C7 | (Not in report) Repeating SOS location beacon every 2 min until stopped; lock-screen quick action | — omitted | [SOSBeaconController.kt:31](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSBeaconController.kt#L31), [:73-81](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSBeaconController.kt#L73-L81); [SOSReceiver.kt:24](../app/src/main/java/com/geeksville/mesh/service/SOSReceiver.kt#L24) |

## D. Silent-node detection and triage

> The repo contains **two separate silent-node detectors**. The report describes only the simpler one in `feature/map`. The one that runs in the background service, sends pings and raises notifications (`app/.../service/SilentNodeDetector.kt`, 518 lines plus a 433-line test) is never mentioned.

| # | Claim (page) | Verdict | Evidence |
|---|---|---|---|
| D1 | `private const val HEARTBEAT_TIMEOUT_SECS = 900L` (pp. 27, 35) | ✅ | [feature/map/.../SilentNodeDetector.kt:10](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/SilentNodeDetector.kt#L10) |
| D2 | Confidence score: +40 timeout, +25 if ≥ 2 online neighbours within 500 m, +20 no motion, +15 battery not in low range; skip if battery 1–4 % or no GPS (pp. 28, 52–53) | ✅ code / 🟡 semantics | [SilentNodeDetector.kt:5-16, 28-41, 54-63](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/SilentNodeDetector.kt#L5-L63). Two caveats. (1) `motionDetected` is never supplied: the only caller ([TriageMapViewModel.kt:56](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/TriageMapViewModel.kt#L56)) uses the default `false`, so the +20 is **always** added. (2) "Neighbour agreement" only counts nearby nodes heard in the last 600 s; the neighbours are not asked whether they also lost the node |
| D3 | `fun checkStatus(lastHeard: Long): TriageLevel`; "if > 900 s the node is classified as **CRITICAL**" (pp. 28, 35) | ❌ | No `checkStatus` anywhere in the repo. `TriageLevel` is a **medical START scale**, BLACK/RED/YELLOW/GREEN ([TriageLevel.kt:3-21](../core/model/src/main/kotlin/org/meshtastic/core/model/triage/TriageLevel.kt#L3-L21)), with no CRITICAL value. Silent nodes become **RED** pins ([TriageMapViewModel.kt:205-235](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/TriageMapViewModel.kt#L205-L235); [app/.../SilentNodeDetector.kt:316](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L316)) |
| D4 | Table 3.5: Active → Warning (soft threshold) → Silent (critical threshold); "nodes classified into triage levels depending on duration of inactivity" (pp. 4, 19, 21) | 🟡 | Matches the **undocumented** service detector: `ONLINE / SILENT / CONFIRMED_SILENT` ([app/.../SilentNodeDetector.kt:32](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L32)), with a 15-min silence timeout, 2-min pings, 2 missed pings → SILENT, 3 → CONFIRMED, and a 10-min promote / 5-min minimum confirm delay ([:501-515](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L501-L515)). Describe *this* class and its constants |
| D5 | Firmware mesh heartbeats update `lastHeard` (pp. 20, 29) | 🟡 | `lastHeard` is updated on any received packet (upstream). The app **also** sends its own `HEARTBEAT_PING` (unicast, `PRIVATE_APP`, hopLimit 2, wantAck, BACKGROUND priority) every 2 min ([app/.../SilentNodeDetector.kt:400-416](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L400-L416)). This is your mechanism, and the report doesn't describe it |
| D6 | "Nodes that have gone silent are transmitted across the mesh" (p. 54) | ✅ | `broadcastSilenceReport` ([:419](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L419)), `broadcastAlertToChannel` ([:282](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L282)), `autoPlaceTriagePin` ([:301](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L301)) |
| D7 | Silent detection "without producing false positives during brief signal interruptions" (p. 37) | ❌ / ⬜ | No measurement in the report. Your own commit `43623ee41` (2026-02-20) is titled **"Fix false silent-node alerts during DeviceSleep / BLE reconnect"**, so false positives did occur and were fixed. Report this honestly as a found-and-fixed issue |
| D8 | `TriagePinEntity` schema: `pin_id` PK, lat, lon, triage_level, victim_count, created_by, timestamp, claimed_by, claim_timestamp, is_silent_node_conversion, source_node_num (pp. 48–50) | ✅ | [TriagePinEntity.kt:9-48](../core/database/src/main/kotlin/org/meshtastic/core/database/entity/TriagePinEntity.kt#L9-L48) |
| D9 | Pins synchronised across nodes; "packets … serialized using protocol buffers" (pp. 16, 33, 50) | 🟡 | Sync exists, but triage/claim/assignment packets are **JSON** (`kotlinx.serialization`) on custom port **256** ([TriagePackets.kt:9-62](../core/model/src/main/kotlin/org/meshtastic/core/model/triage/TriagePackets.kt#L9-L62)), decoded at [MeshDataHandler.kt:247](../app/src/main/java/com/geeksville/mesh/service/MeshDataHandler.kt#L247). Conflicting pins are merged by [TriageMergeEngine.kt:14](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/TriageMergeEngine.kt#L14). JSON is larger than protobuf on a ~230-byte LoRa payload, which is worth discussing as a trade-off |
| D10 | Custom pins for "hazards, victims, checkpoints"; waypoints for hospitals and landmarks (pp. 4, 19) | 🟡 | Triage pins carry START level + victim count. Waypoint presets include Hospital/Police/Fire ([EditWaypointDialog.kt:299-306](../feature/map/src/main/kotlin/org/meshtastic/feature/map/component/EditWaypointDialog.kt#L299-L306), your commit `d8bcb1449`); waypoints themselves are upstream. Hazard polygons only arrived in Sept 2026 (hazard zones) |
| D11 | Node markers colour-coded by triage status (p. 36) | ⬜ | Not verified; would need a screenshot or UI test |

## E. Heartbeat (radio link)

| # | Claim (page) | Verdict | Evidence |
|---|---|---|---|
| E1 | `HEARTBEAT_INTERVAL_MILLIS = 30_000L`; `startHeartbeat()` loop calls `keepAlive()` (pp. 28, 36, 54) | ✅ code / ❌ attribution | [RadioInterfaceService.kt:94](../app/src/main/java/com/geeksville/mesh/repository/radio/RadioInterfaceService.kt#L94) (`30 * 1000L`), [:201-208](../app/src/main/java/com/geeksville/mesh/repository/radio/RadioInterfaceService.kt#L201-L208). **Both are upstream** (James Rich, `c98e74d80` 2025-10-06 and `3b0dda449` 2026-01-18), but the report presents them as the project's own "multi-level heartbeat" design (§4.1.5) |
| E2 | "If heartbeats are not acknowledged, the application can detect radio disconnection" (pp. 29, 36) | ⬜ | `keepAlive()` only sends ([RadioInterfaceService.kt:118-130](../app/src/main/java/com/geeksville/mesh/repository/radio/RadioInterfaceService.kt#L118-L130)); there's no ACK check. Disconnection is detected by the BLE stack callbacks |

## F. Security

| # | Claim (page) | Verdict | Evidence |
|---|---|---|---|
| F1 | "All communications must be encrypted to prevent unauthorized interception"; AES-256 (pp. 5, 10, 15, 22, 43) | 🟡 | Encryption happens in the firmware, not in this app (AES-256 not verifiable here). The app's **default channel uses PSK index 1, the publicly known Meshtastic default key** ([Channel.kt:19-46](../core/model/src/main/kotlin/org/meshtastic/core/model/Channel.kt#L19-L46)), so default-channel traffic, including SOS on `channel = 0`, can be read by anyone with a Meshtastic radio. Confidentiality needs a custom PSK. DMs can use PKI public keys ([MeshCommandSender.kt:388](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L388), upstream). State this limitation in the report |

## G. Results and performance claims

| # | Claim (page) | Verdict | Notes |
|---|---|---|---|
| G1 | Range 5–10 km/hop; delivery > 95 % multi-hop; battery ≥ 24 h (p. 22) | ⬜ | Stated as requirements, but no measurement anywhere in the report |
| G2 | "UI performance remained stable … continuous messaging sessions lasting several hours" (p. 34) | ⬜ | No data |
| G3 | "SOS packets were observed to transmit earlier than default-priority messages" under simulated congestion (p. 35, 37) | ❌ / ⬜ | No data. The congestion was **simulated** (B6), and under simulated congestion the app *rejects* low-priority messages rather than reordering them. "Earlier" does not describe what the code does |
| G4 | "Message persistence ensured zero loss during temporary Bluetooth disconnections" (p. 37) | ⬜ | No data. Note `enqueueForSending` only queues port types in `rememberDataType` ([MeshCommandSender.kt:168-172](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L168-L172)); verify it covers TEXT before claiming zero loss |
| G5 | "SOS propagated successfully across multi-hop setups" (p. 37) | ⬜ | No hop counts reported; see 03-log-analysis |
| G6 | "Battery … no abnormal drain" (p. 37, 41) | ⬜ | No data |

---

## H. Features in the code that the report omits

| Feature | Evidence | When | Comment |
|---|---|---|---|
| **Upstream base (Meshtastic-Android)** | 01-contribution-map | — | Most important omission |
| Rescuer↔victim **assignment via Hungarian algorithm**, incident-commander UI, claim packets | [HungarianSolver.kt:5](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/HungarianSolver.kt#L5), [AssignmentEngine.kt:20](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/AssignmentEngine.kt#L20), [TriageMapViewModel.kt:116-147](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/TriageMapViewModel.kt#L116-L147) | Feb–Mar 2026 | Algorithmically your most interesting contribution, yet absent from the report (the companion `research paper.pdf` mentions an incident-commander view) |
| Offline **Emergency Help** first-aid guide (`feature/emergency`, JSON asset) | 01 §2 #2 | Jan 2026 | Not mentioned |
| Background **silent-node service** with pings, notifications, auto-pins | D4–D6 | Feb 2026 | Only the simpler map detector is described |
| **Congestion gating** with simulated channel utilisation | B6 | Mar 2026 | The real priority mechanism |
| SOS repeating location beacon, lock-screen quick action | C7 | Feb/Sep 2026 | |
| **Codec2** voice (vendored LGPL C library + JNI) | B10 | Mar 2026 | Mentioned only as "voice", with no credit |
| **Geofenced hazard zones** (enter/exit alerts) | 01 §2 #6 | **Sep 2026** | Implemented after the report; the report lists "dynamic geofencing alerts" as **Future Work** (p. 43). Update it if the code is what you submit |
| **Message Mule** delay-tolerant relay | 01 §2 #7 | **Sep 2026** | After the report |
| BLE reconnect / handshake timeout fixes | `cf9899617`, `b3936c75f`, `15567ea5f` | Sep 2026 | |
| Removed upstream firmware-update module, traceroute map, Google Maps | `1b0e9790c`, `c19ed2a12` | Feb 2026 | Worth one sentence on scope |

## I. Summary counts

Out of 44 checked claims: ✅ 15 · 🟡 11 · ❌ 9 · ⬜ 9, plus 2 rows that are omissions (B6, C7). Rows with two verdicts are counted under the first, so D2 and E1 count as ✅ even though each has a semantic or attribution problem.

Highest-impact fixes:
1. Disclose the Meshtastic-Android base (A1).
2. Remove or correct the invented `checkStatus()` and CRITICAL level (D3), the SOS "countdown" (C1), "RELIABLE" (C3) and "Priority:Int" (B2).
3. Credit the 30 s heartbeat to upstream (E1).
4. Rewrite Table 3.3 to describe the actual congestion gating (B5, B6).
5. Remove or support every Results claim (G1–G6) with data from 03.

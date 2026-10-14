# 03 — Log Analysis: what the captured logs actually measure

Every number here is produced by `python -I thesis-review/scripts/analyze_logs.py --json thesis-review/scripts/log_metrics.json`, run from the repo root. The script uses only the standard library and only reads the logs. Its output is committed alongside as `scripts/log_metrics.json`. Section references like "(→ `S2.edge50pro.ack_rtt`)" point to the JSON key each number comes from.

## 1. What was captured

| Session | Date / time (phone clock) | Files | App PID | Captured app duration | Capture mode |
|---|---|---|---|---|---|
| **S1** | 2026-02-19, 18:23–18:27 | `logcat_edge50.txt` / `logcat_edge60.txt` | 13397 / 28716 | 249 s / 232 s | full system logcat (brief format), filtered by PID in script |
| **S2** | 2026-02-20, 07:22–07:55 | `logcat_edge50pro_live.txt` / `logcat_edge60pro_live.txt` | 22379 / 28920 | 1,861 s / 1,925 s (≈ 31–32 min) | `adb logcat --pid` (from `start_capture.ps1`) |
| S2 excerpt | 07:24–07:48 | `silent_events.txt` | — | — | filtered tail produced by `monitor_silent.ps1`; every line is also in the S2 files |
| **S3** | 2026-09-15, 22:17–22:45 | `logcat_edge50pro_sep15.txt` / `logcat_edge60pro_sep15.txt` | 25641 / 26585 | 1,491 s / 1,668 s | `adb logcat --pid` (from `start_capture_sep15.ps1`) |
| (duplicates) | 2026-02-19 | `logcat_edge50pro.txt` (3 lines), `logcat_edge60pro.txt` (1 line) | — | — | hand-copied excerpts of S1; not analysed separately |

**Total app-log time: 7,426 s ≈ 2 h 4 min summed over both phones (≈ 65 min of wall-clock across the three sessions).** PIDs come from `.mesh_pids.txt` / `.mesh_pids_sep15.txt` and the capture scripts.

### Test setup reconstructed from the logs

| Item | Value | Source |
|---|---|---|
| Phones | Motorola **edge 60 pro** (adb serial `ZA222XYK4Q`) and **edge 50 pro** (`ZD222KRTPM`) | comments in `start_capture.ps1:2-3` |
| App build | `com.geeksville.mesh.google.debug` (google flavour, debug) | process name in logs |
| Radio hardware | firmware reports target **`heltec-v3`** (79 log lines) | → `hardware_targets` |
| Radio nodes on the mesh | `!db582780` "module Gamma" (paired to edge 60 pro in S1/S2), `!9e752d58` (paired to edge 50 pro, BLE `F0:9E:9E:75:2D:59`), `!9e75b4c4` (third node, no phone logged; paired to edge 60 pro in S3) | → `nodes_seen`; BLE MACs in log prefixes |
| **Distance between the two phones** | **4.5 m (S1), 4.0 m (S2)**: median of each phone's own GPS fixes, decoded from the `POSITION_APP` protobufs it sent (8 + 8 fixes in S1, 56 + 41 in S2) | → `S1.phone_separation_m`, `S2.phone_separation_m`. The decoder was cross-checked: it gives 12.94951, 80.12855, which matches the coordinates the app itself printed in the S2 silent-node alert |
| Modem preset / hop limit | not logged; the code default is LONG_FAST with hop limit 3 ([Channel.kt:44-50](../core/model/src/main/kotlin/org/meshtastic/core/model/Channel.kt#L44-L50)) | not verified from logs |
| Location | ≈ 12.9495 °N, 80.1285 °E. ⚠ precise GPS coordinates are in committed, public log files (see 06-cleanup) | |

**Conclusion: every capture is a bench test with the two phones about 4 m apart, almost certainly within direct radio range. No range, multi-hop or field data exists in these logs.**

## 2. Measurements extracted

### 2.1 Silent-node detection (S2): the one complete end-to-end experiment

Node Gamma (`!db582780`) went off the mesh and came back. Timeline from `silent_events.txt` and the S2 logs (→ `S2.edge50pro.silent_detection`, `S2.edge60pro.phone_radio_outages_s`):

| Time | Event | Evidence |
|---|---|---|
| 07:23:59 | Gamma last heard (derived: alert says "Last seen: 7m 16s ago" at 07:31:15) | edge50pro |
| 07:24:02 | last "Firmware heartbeat" (`HB|`) from Gamma before the gap | edge60pro |
| 07:25:54 | edge 60 pro loses BLE link to Gamma (`Connected -> Disconnected`) | edge60pro |
| 07:27:15 | 1st heartbeat ping to Gamma unanswered (`missed=1`) | edge50pro |
| 07:29:15 | Gamma **marked SILENT** (2 pings unanswered); `SILENCE_REPORT` broadcast | edge50pro |
| 07:31:15 | Gamma **CONFIRMED SILENT** (3 pings); text alert broadcast with GPS; RED triage pin auto-placed | edge50pro |
| 07:34:18 | edge 60 pro reconnects BLE to Gamma | edge60pro |
| 07:34:44 | Gamma **back online** on edge 50 pro | edge50pro |

| Metric | Value |
|---|---|
| Last heard → SILENT | **316 s** (5 min 16 s) |
| Last heard → CONFIRMED SILENT | **436 s** (7 min 16 s) |
| SILENT → CONFIRMED | 120 s (one ping interval, as designed: `PING_INTERVAL_MS = 120_000`) |
| BLE disconnect (proxy for radio going down) → SILENT / CONFIRMED | 201 s / 321 s |
| Radio reconnect → detector reports "back online" | 26 s |
| Outage of the edge 60 pro ↔ Gamma BLE link | 503 s (8 min 23 s) |
| Gamma `HB|` heartbeat gap (on both phones) | 07:24:02 → 07:34:42 (no `HB|` for 640 s, vs. a normal 120 s interval) |
| False positives in this session | 0 detections for the other two nodes, whose `HB|` heartbeats arrived regularly |

**Discrepancy with the report:** the report says silent nodes are classified "after the defined 15-minute interval" (pp. 27–28, 37). In the run that was actually logged, the background detector flagged the node after **≈ 5 min** and confirmed it after **≈ 7 min**, driven by missed pings. The 900 s timeout was not the trigger.

**Sample size: n = 1 event.** You can present this as a worked example, not as a detection-accuracy result.

### 2.2 Radio-link and mesh timing

| Metric | S1 edge50 | S1 edge60 | S2 edge50 | S2 edge60 | JSON key |
|---|---|---|---|---|---|
| Packets sent phone → radio | 8 | 9 | 65 | 48 | `sent_packets_total` |
| …written successfully to BLE (`queueJob success true`) | 8/8 | 9/9 | 65/65 | 46/47 (1 still pending at capture end) | `ble_queue` |
| Phone→radio BLE write latency, median (max) | 0.096 s (0.31) | 0.285 s (0.34) | 0.099 s (0.39) | 0.315 s (1.04) | `ble_queue.latency_s` |
| App→radio keep-alive interval, median | 30.002 s | 30.004 s | 30.002 s | 30.006 s | `ble_keepalive` (confirms the upstream 30 s heartbeat in [RadioInterfaceService.kt:94](../app/src/main/java/com/geeksville/mesh/repository/radio/RadioInterfaceService.kt#L94)) |
| Own-position broadcast interval, median | 33.6 s | 32.6 s | 33.3 s | 31.3 s | `position_broadcasts` |
| `HB|` heartbeat interval per node, median | 120.1 / 119.9 s | 120.6 / 120.2 s | 120.1 / 120.1 / 120.1 s | 120.1 / 120.1 / 120.2 s | `firmware_heartbeats` |

### 2.3 ACK round-trip time (packets with `want_ack = true`)

Matched `Sending to radio packet … id: X` to `[ackNak] req=X … isAck=true` on the same phone (→ `ack_rtt_samples`).

| Phone | n | min | median | mean | max | Packets |
|---|---|---|---|---|---|---|
| S2 edge 50 pro | 5 | 3.74 s | 5.82 s | 6.84 s | 13.32 s | 5 × HEARTBEAT_PING (unicast, hop_limit 2, BACKGROUND) |
| S2 edge 60 pro | 4 | 0.62 s | 1.97 s | 2.49 s | 5.39 s | 2 × ADMIN to its own radio, 1 × HEARTBEAT_PING, 1 × WAYPOINT broadcast |

- No NAKs, routing errors or max-retransmit events were logged (→ `ack_failures = 0`).
- ⚠ **ACK ≠ delivery.** Four of the five edge 50 pro pings were addressed to Gamma *while Gamma was off the mesh* (§2.1), yet each came back `isAck=true, routeErr=0` within 5.4–13.3 s. These ACKs cannot have come from Gamma; they are most likely implicit ACKs from a relaying radio (the source node is not logged, so this is **not verified**). Do not report ACK ratio as a delivery ratio.
- The silent-node detector correctly did *not* treat these ACKs as proof of life: `missedPings` is reset only by packets *from* the node ([SilentNodeDetector.kt:122-127](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L122-L127)). That is a design point worth a sentence in the report.

### 2.4 Application packets delivered phone → phone

Matched by triage `pin_id` (or, for pings, by the nearest earlier send). One-way times use **two different phone clocks** and are *uncorrected*. Both phones probably use network time, but the offset is unknown.

| Session | From → To | Packet | Outcome | Send → receive log (uncorrected) |
|---|---|---|---|---|
| S1 | edge60 → edge50 | triage pin (legacy JSON, no `type` field) | **received but decode failed** (`decoded=null`; the pin was not shown) | 2.29 s |
| S2 | edge60 → edge50 | `MANUAL_TRIAGE_PIN` (broadcast, hop 2, HIGH) | received and decoded | 2.50 s |
| S2 | edge50 → edge60 | `CLAIM_PIN` (broadcast, hop 1, HIGH) | received and decoded | 2.69 s |
| S2 | edge60 → edge50's radio | `HEARTBEAT_PING` | received | 1.18 s |
| S2 | edge50 → mesh | `SILENCE_REPORT`, silent-alert text, auto RED pin | **not observable**: the only other phone was disconnected from its radio at the time | — |

**Application-level delivery in the logs: 4 packets observed arriving, 3 decoded correctly, 1 failed to decode (a format bug in the Feb-19 build, fixed by S2).** No packet can be shown to have been lost, because the logs don't show which packets *should* have arrived when a phone was offline.

### 2.5 BLE reconnection (S3, September build with the reconnect fix `15567ea5f`)

Three automatic recoveries on edge 60 pro after `Radio interface error: Operation failed: Insufficient resources` (→ `S3.edge60pro.auto_reconnects`):

| # | Error at | Error → forced reconnect | → BLE connected | → config handshake done | → node-info handshake done (usable) | "service not found" retries |
|---|---|---|---|---|---|---|
| 1 | 22:32:01.7 | 10.01 s | 12.34 s | 15.73 s | **18.72 s** | 2 |
| 2 | 22:34:28.3 | 10.01 s | 11.23 s | 14.47 s | **17.93 s** | 2 |
| 3 | 22:40:39.8 | 10.01 s | 11.40 s | 14.45 s | **17.17 s** | 2 |

- Median full recovery: **17.9 s**. 10.0 s of that is the fixed `RECONNECT_RETRY_DELAY_MILLIS` ([RadioInterfaceService.kt:95](../app/src/main/java/com/geeksville/mesh/repository/radio/RadioInterfaceService.kt#L95)). The actual reconnect plus handshake takes ≈ 7–9 s.
- 3 link errors in ≈ 28 min, with no manual intervention needed. edge 50 pro had no errors in S3.
- S2 (older build): "Starting connect" → "MyNodeInfo received" took 0.92 s and 0.89 s (n = 2) (→ `start_connect_to_mynodeinfo_s`).
- S3 contains **no packet traffic** (no `Sending to radio` lines), so S3 says nothing about messaging.

### 2.6 Stability and UI performance

| Metric | Value | Key |
|---|---|---|
| Crashes / ANRs (`FATAL EXCEPTION`, `ANR in`) in all logs | **0** | `fatal_or_anr_lines` |
| App E-level lines | S2 edge60: `Error writing LocalConfig settings: SESSIONKEY` ×2, `DEVICE_UI` ×2; 10 hidden-API warnings; all other files 0 | `errors_E_F` |
| Main-thread jank (`Choreographer: Skipped N frames`) | S2 edge60: 10 events, median 36, max 59 frames (≈ 1 s freeze at 60 Hz); S2 edge50: 1 (35); S3 edge60: 1 (37) | `skipped_frames` |
| `Showing on map: …` debug lines | 26–55 per second while the map is on screen (56,658 lines in S2 edge50) | `map_recompose_per_s`. Indicates the map composable is recomposing continuously; a performance bug worth fixing or at least mentioning |
| `Auto-removed triage pin for recovered node` | 55 (edge50) / 45 (edge60) in S2 for a handful of recoveries | repeated work on every packet from a recovered node |

## 3. What the logs do **NOT** show

| Report claim / desired metric | Why the logs can't support it |
|---|---|
| Range (5–10 km per hop) | Phones ≈ 4 m apart; no RSSI/SNR values are logged (S3 only logs `readRssi()` calls, not results) |
| Multi-hop delivery / relay hops | No `hop_start`/hops-away on received packets is logged; with all radios at one bench, packets were almost certainly direct |
| Packet delivery ratio (> 95 %) | Too few app packets (n = 4 observed arrivals), no send-schedule to compare against, and ACKs are not end-to-end (§2.3) |
| End-to-end SOS latency or propagation | **No SOS was sent in any captured session** (0 `TEXT_SOS` packets) |
| Chat-message latency | **No chat text messages** in any session |
| Priority behaviour under congestion | No congestion test logged; no high- vs low-priority comparison |
| Voice messages | No `AUDIO_APP` traffic |
| Hazard zones, Message Mule | Not exercised (S3 has no traffic) |
| Battery drain / 24 h endurance | No battery telemetry in the logs; longest session ≈ 32 min |
| "Several hours" of stable messaging (report p. 34) | Longest capture is ≈ 32 min |
| Clock-corrected one-way latency | Phone clocks were not synchronised or measured |

## 4. Tests to run for a credible Results section

Each test lists its procedure and what to log. Repeat each one **≥ 30 times** (or for ≥ 30 min) and report mean, median, standard deviation and n.

1. **PDR and latency vs. distance (single hop).** Two phones+radios at 10 m, 100 m, 500 m, 1 km and 2 km (line-of-sight and urban). Send 100 numbered texts (`seq|t_send_ms`) at 1 per 10 s. Report delivered/100 and median latency. Log `rx_rssi`/`rx_snr` on receive; this needs a one-line log in `MeshDataHandler` for received packets.
2. **Multi-hop.** Three radios in a line, with the end nodes out of direct range of each other (verify by switching off the middle node: PDR should drop to ≈ 0). Report PDR and latency at 1 vs. 2 hops, and log `hop_start - hop_limit` on receive.
3. **SOS end-to-end.** 30 SOS activations: measure time from tap to first receipt on every other phone, delivery count, and beacon interval accuracy.
4. **Priority/congestion.** Set the simulated channel-utilisation slider to 0 / 75 / 90 %. Send 20 messages at each priority and report accepted/rejected counts; this verifies the gating in [MeshCommandSender.kt:116-127](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L116-L127). Be explicit that the congestion is simulated.
5. **Silent-node detection accuracy.** Switch a radio off 20 times and leave it on for a 2-h control period. Report detection latency (mean ± sd), plus false positives per hour during normal operation and during phone BLE disconnects (the scenario fixed in `43623ee41`).
6. **BLE recovery.** 20 forced disconnects (radio power-cycle, phone Bluetooth toggle, walking out of range). Report time to node-info handshake, as in §2.5.
7. **Battery.** Phone and radio at 100 %, a scripted message every 5 min, logged every 30 min via `dumpsys battery` and the radio's telemetry. Run until 20 % or 24 h.
8. **Clock sync.** Before each latency test, record `adb shell date +%s%3N` on both phones back-to-back and subtract the offset; or measure round-trip only.

A helper that would make all of this reproducible: log one structured line per send and receive, e.g. `RESQ_METRIC|tx|<id>|<port>|<prio>|<t_ms>` and `RESQ_METRIC|rx|<id>|<from>|<hops>|<rssi>|<snr>|<t_ms>`, then extend `analyze_logs.py` to join them.

## 5. Draft Results table (only measured values)

> Suggested caption: *Table 5.x – Measured behaviour from bench tests (two Motorola phones, three Heltec V3 nodes, ≈ 4 m separation, Feb and Sep 2026). n is the number of observed events; values come from Android logcat and are reproducible with `analyze_logs.py`.*

| Metric | Value | n | Conditions / caveat |
|---|---|---|---|
| Phone→radio BLE write latency (median) | 0.10–0.32 s (max 1.04 s) | 128 writes | depends on phone; S1 + S2 |
| App→radio keep-alive interval | 30.00 s (median) | 132 intervals | confirms the configured 30 s |
| Node `HB|` heartbeat interval | 120.1 s (median) | 3 nodes, 2 sessions | radio-side heartbeat |
| ACK round-trip, unicast ping, hop limit 2 | median 5.8 s (range 3.7–13.3 s) | 5 | implicit ACKs; not proof of delivery |
| ACK round-trip, all want-ACK packets (edge 60 pro) | median 2.0 s (range 0.6–5.4 s) | 4 | includes ACKs from the local radio |
| App-packet arrival time phone→phone (uncorrected clocks) | 1.2–2.7 s | 4 | bench distance, likely single hop |
| App packets received / decoded | 4 / 3 | 4 | 1 decode failure (legacy pin format, Feb-19 build) |
| Silent-node detection: last heard → SILENT | 316 s | 1 | ping-based detector, 2-min pings |
| Silent-node detection: last heard → CONFIRMED | 436 s | 1 | |
| Recovery after node returns → "back online" | 26 s | 1 | |
| BLE auto-reconnect after link error (to usable) | median 17.9 s (17.2–18.7 s) | 3 | includes the fixed 10 s retry delay |
| Crashes / ANRs during capture | 0 | ≈ 124 min of per-phone app logs | |
| UI jank events (> 30 skipped frames) | 12; worst 59 frames | ≈ 124 min | mostly on the map screen |

Do **not** add rows for range, PDR, multi-hop, SOS, battery or congestion until tests 1–7 have been run.

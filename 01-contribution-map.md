# 01 — Contribution Map

Generated 2026-10-14 from the local repository at `HEAD = 15567ea5f`. Every number below can be reproduced with the commands or scripts given beside it.

## 0. Identity and baseline used

| Item | Value | Evidence |
|---|---|---|
| Author identity analysed | `Bharath V V <140043221+ageon1156@users.noreply.github.com>` | `git config user.name/user.email`. This is the only identity in the history that matches "Bharath", "ageon" or "searc" (`git log --all --format="%an <%ae>" \| grep -iE "bharath\|ageon\|searc"` → 44 commits) |
| Upstream project | **Meshtastic-Android** (GPL-3.0), Meshtastic LLC | Package `com.geeksville.mesh` and authors `geeksville`/Kevin Hester (Meshtastic founder), `andrekir`, `James Rich`. Upstream PR numbers appear in subjects, e.g. `9266caae9 feat: Configure Pre-Commit run for debugging (#4284)`. Upstream URL: **not verified from the repo**; no remote points to `meshtastic/Meshtastic-Android`, and all 13 remotes are `github.com/ageon1156/*` |
| Fork point (last upstream commit) | `9266caae9`, James Rich, 2026-01-21 | Parent of the first own commit `024f9abbb` |
| Upstream licence at fork | GNU GPL v3 (`git show 9266caae9:LICENSE`) | Every upstream source file had a `Copyright (c) 2025-2026 Meshtastic LLC … GPL v3` header (e.g. `git show 9266caae9:app/src/main/java/com/geeksville/mesh/service/MeshService.kt`, lines 1–16) |

**Assumption:** your message left `[NAME / EMAIL]` unfilled, so I used the git config identity. If you also committed under another identity (e.g. on a lab PC), those commits are not counted here.

## 1. Headline numbers

| Metric | Value | How derived |
|---|---|---|
| Total commits in repo | 5,681 | `git rev-list --count HEAD` |
| Commits by you | **44** (37 non-merge + 7 merges) | `git log --all --author=ageon1156` |
| Date range | 2026-01-22 → 2026-09-15, in two bursts: **Jan 22 – Mar 11** (31 commits) and **Sep 14 – 15** (13 commits) | per-month counts: 2026-01: 16, 02: 12, 03: 3, 09: 13 |
| Lines at HEAD that `git blame` attributes to you (source files changed since fork, codec2 excluded, two mechanical commits ignored) | **16,599** | `scripts/blame_ownership.sh` → `scripts/blame_ownership.tsv` |
| …of which are near-verbatim copies of upstream files | ≈ 2,568 | `scripts/copy_check.py` → `scripts/copy_check.tsv` |
| **Adjusted lines originating in your commits** | **≈ 14,000** | 16,599 − 2,568 |
| Upstream lines in those same touched files | 50,930 | same TSV |

> Caveat: "attributed to you" only means the lines entered the repo through commits with your name on them.

## 2. Features you added (net-new code, not present upstream)

Own-line counts are summed from `blame_ownership.tsv` by path pattern (the `f()` helper in §6). Tests are included where they match the pattern.

| # | Feature | Key files (entry points) | Own lines | Commits (date) |
|---|---|---|---|---|
| 1 | **SOS emergency broadcast**: one-tap SOS screen, periodic beacon with GPS position and node long name, SOS priority, lock-screen/quick-access receiver | [SOSBeaconController.kt:42](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSBeaconController.kt#L42), [SOSMessage.kt:11](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSMessage.kt#L11) (`formatSosMessage`), [SOSMessage.kt:32](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSMessage.kt#L32) (`buildSosPacket`), [SOSViewModel.kt:32](../feature/sos/src/main/kotlin/org/meshtastic/feature/sos/SOSViewModel.kt#L32), [SOSReceiver.kt:24](../app/src/main/java/com/geeksville/mesh/service/SOSReceiver.kt#L24) | 807 | `5354a0516` (01-29), `75e5e62aa` (01-30), `c19ed2a12` (02-18), `45ed1f204`/`119ced1e6` (09-15) |
| 2 | **Offline Emergency Help guide**: first-aid/survival topics loaded from a bundled JSON asset | `feature/emergency/*` (13 files), [EmergencyJsonDataSource.kt:11](../feature/emergency/src/main/kotlin/org/meshtastic/feature/emergency/data/EmergencyJsonDataSource.kt#L11), `app/src/main/assets/emergency_guide.json` (787 lines, lists IFRC/WHO/Red Cross/FEMA as sources in `app_metadata.sources`) | 1,485 | `9c7c71f47` (01-29) |
| 3 | **Silent-node detector**: heartbeat tracking, ONLINE → SILENT → CONFIRMED_SILENT states, false-alert suppression during DeviceSleep/BLE reconnect | [app/…/service/SilentNodeDetector.kt:32-54](../app/src/main/java/com/geeksville/mesh/service/SilentNodeDetector.kt#L32-L54), [feature/map/…/triage/SilentNodeDetector.kt:19](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/SilentNodeDetector.kt#L19) (a second, separate implementation), test `SilentNodeDetectorTest.kt` (433 lines) | 1,054 (incl. test) | `0494376d0` (02-15), `c19ed2a12` (02-18), `43623ee41` (02-20) |
| 4 | **Triage map and rescuer assignment**: triage pins, claim packets, Hungarian-algorithm rescuer↔victim assignment, incident-commander UI | [HungarianSolver.kt:5](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/HungarianSolver.kt#L5), [AssignmentEngine.kt:20](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/AssignmentEngine.kt#L20), [TriageMergeEngine.kt:14](../feature/map/src/main/kotlin/org/meshtastic/feature/map/triage/TriageMergeEngine.kt#L14), [TriagePackets.kt:14-56](../core/model/src/main/kotlin/org/meshtastic/core/model/triage/TriagePackets.kt#L14-L56) | 1,546 | `f96b39052` (02-19), `62a5326d2` (03-07) |
| 5 | **Voice messages over Codec2**: record → Codec2 encode (JNI) → fragment → send | [Codec2Wrapper.kt:7](../core/audio/src/main/kotlin/org/meshtastic/core/audio/Codec2Wrapper.kt#L7), `app/src/main/cpp/codec2_jni.cpp` (123 lines), [VoiceFragment.kt:6-47](../core/model/src/main/kotlin/org/meshtastic/core/model/voice/VoiceFragment.kt#L6-L47), `feature/voicemessage/*` | 844 (excl. codec2 library) | `62a5326d2` (03-07) |
| 6 | **Geofenced hazard zones**: polygon zones, point-in-polygon, enter/exit notifications, shared over mesh as JSON packets | [HazardZone.kt:6-82](../core/model/src/main/kotlin/org/meshtastic/core/model/hazard/HazardZone.kt#L6-L82), [HazardZonePackets.kt:23-72](../core/model/src/main/kotlin/org/meshtastic/core/model/hazard/HazardZonePackets.kt#L23-L72), [HazardZoneMonitor.kt:27-40](../app/src/main/java/com/geeksville/mesh/service/HazardZoneMonitor.kt#L27-L40), tests `HazardZoneTest.kt`, `HazardZoneMonitorTest.kt` | 962 | `34b4f9531`, `45ed1f204`, `e59cea170` (all 09-15) |
| 7 | **Message Mule** (delayed retry of the sender's own failed DMs; see 02b §8) | [MessageMuleRelay.kt:30](../app/src/main/java/com/geeksville/mesh/service/MessageMuleRelay.kt#L30), [CarriedMessage.kt:5-7](../core/model/src/main/kotlin/org/meshtastic/core/model/mule/CarriedMessage.kt#L5-L7), `CarriedMessageDao.kt`, `MessageMuleLogScreen.kt` | 440 | `34b4f9531`, `45ed1f204` (09-15) |
| 8 | **Message priority / disaster congestion mode** | `4d28a45ef` touched `DataPacket.kt`, `MeshCommandSender.kt`, `Message.kt` | (inside upstream files) | `4d28a45ef` (01-31) |
| 9 | **"Organic"/Atlas UI theme and rebranding** | `core/ui/…/theme/Organic*.kt`, `Organic*Item.kt`, `OrganicNavigationBar.kt` | 2,825 | `57425a0a5` (01-29) + several |
| 10 | **BLE reliability fixes**: connection/handshake timeouts, auto-reconnect without re-pair | `NordicBleInterface.kt` (130 own lines), `RadioInterfaceService.kt`, `MeshConnectionManager.kt`, `MeshConfigFlowManager.kt`, `BleError.kt` | 336 | `cf9899617`, `b3936c75f` (09-14), `15567ea5f` (09-15) |
| 11 | Removed upstream features: firmware-update module (`feature/firmware`, 26 files), traceroute map screen, Google Maps | `1b0e9790c` (02-21), `c19ed2a12` | (deletions) | |

**Other modified upstream files with the most of your lines:** `Message.kt` (223 of 906), `MeshDataHandler.kt` (138/860), `Main.kt` (130/606), `NordicBleInterface.kt` (130/402), `MeshServiceNotificationsImpl.kt` (114/903). Full list: `scripts/blame_ownership.tsv`.

## 3. What is upstream (not your work)

- **Everything not listed in §2**: the BLE/serial/TCP radio transport (`app/…/repository/radio/`), the Meshtastic protobuf protocol (`core/proto`, a git submodule of `meshtastic/protobufs`), the mesh routing/flooding (the app only sets `hopLimit` on outgoing packets, [MeshCommandSender.kt:88](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L88) and [:155](../app/src/main/java/com/geeksville/mesh/service/MeshCommandSender.kt#L155), and hands them to the radio over the ToRadio BLE characteristic, [NordicBleInterface.kt:215-221](../app/src/main/java/com/geeksville/mesh/repository/radio/NordicBleInterface.kt#L215-L221). The relaying itself happens in the Meshtastic radio firmware, which is not in this repo), PKI/channel encryption, the Room database, node list, messaging, settings, metrics charts and maps. Upstream holds 50,930 of the lines in the files you touched, plus every untouched file.
- **Files credited to you by blame that are actually copies of upstream** (`scripts/copy_check.tsv`, overlap = share of non-comment lines found verbatim in the upstream file):

  | Your file (google flavour) | Upstream source (fdroid flavour, at fork) | Overlap |
  |---|---|---|
  | `feature/map/src/google/.../MarkerClusterer.java`, `StaticCluster.java`, `CustomTileSource.kt`, `OnlineTileSourceAuth.kt`, `MapButton.kt`, `DownloadButton.kt`, `CacheLayout.kt`, `SqlTileWriterExt.kt`, `MapViewExtensions.kt`, `MapUtils.kt`, `node/NodeMapScreen.kt` | same paths under `src/fdroid/` | 100 % |
  | `MarkerWithLabel.kt`, `NOAAWmsTileSource.kt`, `RadiusMarkerClusterer.java`, `MapViewWithLifecycle.kt` | same paths under `src/fdroid/` | 97–99 % |
  | `feature/map/src/google/.../MapView.kt` (1,349 own lines) | `src/fdroid/.../MapView.kt` | 74 % |
  | `feature/{sos,voicemessage,emergency}/build.gradle.kts` | `feature/firmware` / `feature/node` build files | 88–91 % (boilerplate; normal) |

  In practice, commit `f96b39052` replaced the Google-Maps flavour with upstream's OSMDroid (fdroid) map code. Present this as reuse, not as new work.
- **Vendored third-party library: Codec2.** `app/src/main/cpp/codec2/` has 116 files and 42,528 lines, © David Rowe, **LGPL-2.1** (header of `codec2.c`). It was added in `62a5326d2` with no attribution file. Only `codec2_jni.cpp`, `CMakeLists.txt` and `Codec2Wrapper.kt` are glue code written in your commits.
- **Emergency guide content** (`emergency_guide.json`): the file names IFRC/WHO/St John/Red Cross/FEMA/UK Resus Council as sources, but where the text came from (written, paraphrased or generated) is **not verified**. Medical content needs a clear provenance statement in the thesis.

## 4. Commits that rewrite history or remove attribution

These do not affect functionality, but an examiner reading `git log` will notice them.

| Commit | Date | What it did | Why it matters |
|---|---|---|---|
| `3f49bf920` Delete LICENSE | 2026-02-04 | Removed the GPL-3.0 `LICENSE` file (675 lines) | GPL-3.0 §4–5 require keeping the licence with redistributed source. The public GitHub repos (`ageon1156/*`) are redistributions |
| `16e3fd9c9` Delete README.md | 2026-02-04 | Removed upstream README (credits Meshtastic) | Removes visible upstream credit |
| `4bb4dd75f` Touch all files to update last modified date | 2026-02-04 | 1,093 files changed: mostly a trailing newline appended to every file, plus 28,899 deletions. It also **removed 155 `Copyright … Meshtastic LLC` lines and replaced the holder with "Atlas LLC" in 4 files** (e.g. `gradle.properties:2`, `secrets.defaults.properties:2`) | Makes every file look recently modified by you and inflates naïve `git blame`/stats (ignored in this analysis via `--ignore-rev`). Swapping in a different copyright holder misattributes copyright; restore "Meshtastic LLC" |
| (several) rebranding | 2026-01/02 | App name changed to "ResQ" ([strings.xml:3](../app/src/main/res/values/strings.xml#L3)); upstream forum and web links in user-facing strings replaced with `example.com` (`core/strings/.../values/strings.xml:180`) | Rebranding a GPL fork is allowed, but together with the removed notices it leaves no visible credit to Meshtastic in the app |
| `845fb5d58` Remove all comments from source files | 2026-02-21 | 685 files, −14,676 lines, **including every `Copyright (c) … Meshtastic LLC / GPL v3` header** (e.g. `MeshService.kt` lines 1–16 at fork → removed) | Removing copyright notices from GPL code violates GPL-3.0 §4 ("keep intact all notices"). It also makes upstream code look unattributed |
| `edb467bb4` "Make UI look amateur with garish colors, laggy animations, and Comic Sans" | 2026-02-03 | Theme changes in `Organic*.kt` (no "Comic" string remains at HEAD) | Commit message is visible in public history; consider how it reads to an examiner |

**Recommendation (for 00-summary):** restore `LICENSE` and the per-file GPL headers, add a `NOTICE`/credits file for Meshtastic and Codec2, and state in the thesis exactly which modules are original (§2) and which are reused (§3).

## 5. Repository state notes

- Uncommitted change in `feature/map/build.gradle.kts` (+2 lines: `testImplementation(libs.junit)`) and untracked `feature/map/src/test/.../triage/AssignmentEngineTest.kt` (164 lines, 9 tests, dated 2026-09-15) at the start of this review. Neither is counted in the numbers above.
- 286 files deleted since fork (largest groups: `fastlane/metadata` 116, `mesh_service_example/src` 39, `core/strings` 39, `feature/settings` 29, `feature/firmware` 26).
- Logcat dumps (~26 MB) and PowerShell capture scripts are committed in the repo root (see 06-cleanup).

## 6. Reproduce

```bash
# commits and date range
git log --all --author=ageon1156 --format="%h|%ad|%s" --date=short
# line ownership (≈3–5 min), then copy detection
bash thesis-review/scripts/blame_ownership.sh  > thesis-review/scripts/blame_ownership.tsv
python -I thesis-review/scripts/copy_check.py  > thesis-review/scripts/copy_check.tsv
# per-feature own lines (pattern = path regex)
awk -F'\t' -v p="[Hh]azard" '$1 ~ p {o+=$2} END {print o}' thesis-review/scripts/blame_ownership.tsv
```

### Limitations of this analysis
- `git blame` credits the last person to touch a line. Your reformatting of upstream lines (theme or rename edits) counts as "own" even when the logic is upstream's, so the ≈14k figure is an upper bound.
- `copy_check.py` only detects copies of upstream files **with the same file name**. Code copied from elsewhere (Stack Overflow, other repos) is not detected. Origin of the Hungarian solver and the point-in-polygon code: **not verified**.
- Remote branches from the 13 `ageon1156/*` remotes were included via `--all`. Work that exists only in those remotes and was never fetched is not counted.

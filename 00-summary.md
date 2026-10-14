# 00 — Summary: what to fix before submission

**Inputs reviewed:**
- the repo at `HEAD = 15567ea5f` (5,681 commits);
- the thesis `C:\Users\searc\Downloads\DOCS\done.pdf` (May 2026, 69 pp.);
- the companion `research paper.pdf` (references and evaluation sections only);
- the 8 logcat files and `silent_events.txt`.

Nothing in the repo was modified; all output is in `thesis-review/`.

| File | Contents |
|---|---|
| [01-contribution-map.md](01-contribution-map.md) | your work vs. Meshtastic upstream, attribution removals |
| [02-claims-vs-code.md](02-claims-vs-code.md) | 44 report claims checked against code |
| [02b-features-to-add.md](02b-features-to-add.md) | verified fact sheets for the 8 features the report omits *(added at your request)* |
| [03-log-analysis.md](03-log-analysis.md) | measurements from logs, gaps, test plan, draft Results table |
| [04-citations.md](04-citations.md) | in-text citations vs. reference list |
| [05-README-draft.md](05-README-draft.md) | README draft |
| [06-cleanup.md](06-cleanup.md) | secrets check, cleanup and `.gitignore` suggestions |
| `scripts/` | `blame_ownership.sh`, `copy_check.py`, `analyze_logs.py` and their outputs |

---

## Top 9 fixes, ranked by impact

### 1. State that ResQ is built on Meshtastic-Android, and say exactly what you added
The report never mentions that the app is a fork (02 A1). It presents upstream code as the project's design: the 30 s radio heartbeat (02 E1), the protobuf packet path, Room/Paging, reactions and the BLE layer.

**Fix:** add a "Base system and contribution" section to Ch. 1 or 3, with a two-column table: upstream (Meshtastic-Android, GPL-3.0, commit `9266caae9`) vs. ours (01 §2: SOS, priority gating, triage + Hungarian assignment, silent-node service, hazard zones, voice, guide, Mule, BLE fixes). Cite the repo. **This is the single biggest academic-integrity risk.**

### 2. Restore GPL and LGPL compliance in the public repos
- `LICENSE` was deleted (`3f49bf920`).
- All Meshtastic copyright headers were stripped (`845fb5d58`, `4bb4dd75f`).
- The holder was renamed to "Atlas LLC" in 4 files.
- The Spotless header templates were blanked.
- Codec2 (LGPL-2.1) is vendored without a notice.

**Fix:** follow the steps in 06 §6. These edits are mechanical and take about an hour. Left as they are, they look like deliberate removal of attribution.

### 3. Rebuild the Results section on real data
Current §5.3 has no numbers, and several claims are unsupported or contradicted: multi-hop SOS, "zero loss", "several hours", "no false positives" (contradicted by your fix commit `43623ee41`), and "SOS transmitted earlier" (the code rejects low-priority messages; it doesn't reorder them).

**Fix:** use the measured table in 03 §5. State that the tests were bench tests at about 4 m. If you have time, run tests 1, 2, 3 and 5 from 03 §4: distance PDR, multi-hop, SOS latency, silent detection ×20.

⚠ The companion research paper shows Figs. 6–9 (latency vs. hop count for two modem presets, PDR by environment, silent-node delay "measured"). **No data in the repo or logs supports them.** Find the source data, or label them as illustrative or simulated. Discuss this with your supervisor before the paper goes anywhere.

### 4. Correct the code descriptions that are factually wrong (02)
- `checkStatus()` and the "CRITICAL" level don't exist; `TriageLevel` is START triage (D3).
- The SOS safeguard is a confirmation dialog, not a countdown (C1).
- SOS priority is ALERT, not RELIABLE (C3); there is no `sendSOS()` (C4).
- "Priority:Int" isn't valid code (B2).
- Table 3.3 (ACK-gated, elevated hop limit, pre-emption) is wrong; replace it with the congestion-gating table from 02b §3 (B5/B6).
- Silent nodes were detected after about 5–7 min of missed pings in the logged run, not 15 min (03 §2.1).
- Triage, hazard and voice packets use JSON or a custom binary format, not protobuf (D9, B10).
- The 30 s heartbeat is upstream code (E1).

### 5. Fix the citations (04)
- Only 1 of 10 in-text citations matches its reference entry.
- 9 surveyed works are missing from the list, and 14 of 15 entries are effectively uncited.
- Chapters 1 and 3–6 have zero citations.

Rewrite Ch. 2 from papers you can actually open, check every quoted statistic, add Meshtastic-Android, Meshtastic docs, Codec2, START triage and Kuhn/Munkres, and delete unused entries.

### 6. Add the features the report leaves out (02b)
The strongest are Hungarian rescuer assignment, the background silent-node service (with real measurements), congestion-based priority gating, and hazard zones (which log their own metrics). Also commit and run the untracked `AssignmentEngineTest.kt` (9 tests), so you can cite passing unit tests. If you include the September features, remove "geofencing alerts" from Future Work.

### 7. Make the title, abstract and security claims honest
- "Hybrid BLE and LoRa" suggests phone-to-phone BLE, but BLE is only the phone↔radio link (02 A2). Retitle (e.g. "…Using BLE-Connected LoRa Mesh Radios") or explain it in the abstract.
- "All communications encrypted": the default channel uses Meshtastic's public key, so SOS on channel 0 is readable by any Meshtastic user (02 F1). State this and recommend custom PSKs.
- Message Mule retries only the sender's own messages; don't call it a relay (02b §8).

### 8. Fix the repetitive, generic writing
- The same 6-sentence paragraph ("This module plays an important role during disaster situations…") appears **verbatim 4 times** (pp. 25, 26, 28, 29). Delete all four.
- "ensure/ensures/ensuring" appears **79 times**, "critical" 24 times, "resilient/resilience" 12 times. Replace each with what the code concretely does.
- §5.3 restates every module twice (pp. 37–39) and the Conclusion restates it again. Keep one description per module.
- Generic benefit sentences, informal lines ("a map is pretty cool to have", "unfair odds"), and the inconsistent tense and voice.
- Replace generic statements with specifics from 02b and 03: constants, file names, measured values, limitations. Specific numbers and admitted limitations are the strongest signal of authentic writing.
- **Typos and inconsistencies:**
  - "Apllication" (certificate), "RESUSLT", "PROJ ECT", "VIVA VOICE" → "VIVA VOCE", "timestamp timestamps" ×2;
  - supervisor listed as "Associate Professor" (p. ii) and "Assistant Professor" (p. iv);
  - degree given as B.Tech (cover) and B.E. (bios);
  - "SOS: Save Our Souls" (SOS is a signal, not an acronym);
  - in the PDF's text layer the ToC chapter and section numbers don't line up with their titles. This may be only an extraction artefact, so check it visually.

### 9. Clean the repository before examiners clone it (06)
Move the 26 MB of logcat dumps (they contain GPS to about 1 m and device IDs) and the capture scripts out of `main`. Add the `.gitignore` entries, put the README from 05 at the root, and commit the pending test. Decide on any history rewrite *before* you cite commit hashes in the thesis.

---

## Open questions for you

1. **Other identities.** Did you commit under any identity other than `Bharath V V <…ageon1156@users.noreply.github.com>`? Only that one was analysed.
2. **Radio firmware.** The app receives `HB|…` heartbeat packets every 120 s from each radio (03 §2.2), and nothing in this repo sends them. Did you modify the Meshtastic firmware? If so, where is that code, and why isn't it in the report? It would be a contribution in its own right, or an undocumented dependency.
3. **Research paper data.** Where does the data for Figs. 6–9 of `research paper.pdf` come from? Was the paper submitted or published?
4. **Field tests.** Did you run any test that isn't in these logs (outdoor, multi-hop, SOS)? If so, do you still have its logs or photos? The S2 logs mention node "module Gamma", and there was a third node `!9e75b4c4`: where was it placed?
5. **Which code version do you submit?** The May 2026 report predates the September commits (hazard zones, Message Mule, BLE fixes). Should the report describe the September code?
6. **Emergency-guide text.** Was it written by you or paraphrased from the listed sources? Was it reviewed by anyone medically qualified?
7. **Hungarian solver.** Did you write it from the algorithm description or adapt it from a reference? If adapted, cite the source.
8. **Repo visibility.** Which of the 13 `ageon1156/*` remotes are public, and which one will you submit as the official project repo?
9. **ACK source.** The pings to the switched-off node still returned ACKs (03 §2.3). Do you want to add a log of the ACK's `from` and `relayNode` (already passed to `handleAckNak`), so this can be explained in the report?

## Assumptions made
- Author identity was taken from `git config` because `[NAME / EMAIL]` was a placeholder.
- The upstream is Meshtastic-Android; this is inferred from the package name, authors and PR numbers, since no remote points to it.
- The year in the log timestamps is 2026 (logcat doesn't record the year).
- I read only the file names in `Downloads\DOCS` and opened only `done.pdf` and `research paper.pdf`; the personal documents there were not opened.

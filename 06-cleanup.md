# 06 — Repository Cleanup (suggestions only; nothing was executed)

State at review time: branch `main`, `HEAD = 15567ea5f`, pack size 44.2 MiB.

## 1. Secrets check

| File | Tracked? | Content | Verdict |
|---|---|---|---|
| `secrets.defaults.properties` | yes | `datadogClientToken=faketoken1234…`, `datadogApplicationId=fakeappid1234…`, `MAPS_API_KEY=DEFAULT_API_KEY` | ✅ Placeholders, identical to upstream at `9266caae9`. No real secret. ⚠ Line 2 says `Copyright (c) 2025 Atlas LLC`; upstream says Meshtastic LLC (changed in `4bb4dd75f`). Restore it |
| `config.properties` | yes | version numbers, SDK levels, `APPLICATION_ID=com.geeksville.mesh` | ✅ No secrets |
| `app/google-services.json` | yes (despite `**/google-services.json` in `.gitignore`; upstream committed it in 2020) | `project_id: "xxx…"`, `current_key: "APlaceholder…"` | ✅ Placeholder |
| `secrets.properties`, `local.properties`, `keystore.properties`, `*.jks` | **not tracked** | — | ✅ Correctly ignored |
| `gradle.properties` | yes | no keys. ⚠ `Copyright (c) 2025 Atlas LLC` (was Meshtastic LLC). The machine-specific JDK path was already removed in `f488e3368` | restore the copyright line |
| Search `git grep -nE "(api[_-]?key\|secret\|token\|password)\s*[=:]"` in `*.properties *.json *.kts *.yml` | — | only `id-token: write` permissions in GitHub workflows (upstream CI) | ✅ |

**No committed credentials found.** Datadog SDK logs appear in S3 (`Write operation ignored, session is expired or RUM feature is disabled`), which confirms the fake token is in use and nothing is being reported.

## 2. Personal and location data in committed files

The tracked logs are in the history of at least these remotes: `ageon`, `anna`, `mesh-resq`, `resq`, `resq-main`, `stark`, `uni-resq` (`git branch -r --contains 1b0e9790c`). Whether those GitHub repos are public is **not verified**.

| Data | Where | Precision |
|---|---|---|
| GPS of the test site | plain text in `silent_events.txt` and `logcat_edge50pro_live.txt` (`maps.google.com/maps?q=12.94951,80.12854`), the triage-pin JSON in `logcat_edge60pro.txt`, and ≈ 200 binary `POSITION_APP` fixes in the S1/S2 logs | ≈ 1 m (decoded in 03 §1) |
| BLE MAC addresses of the radios | log line prefixes (`F0:9E:9E:75:2D:59`, `10:51:DB:58:27:81`, …) | device identifiers |
| adb serials / Wi-Fi debug names of both phones | `start_capture*.ps1`, `monitor_logs.ps1` (`ZA222XYK4Q`, `ZD222KRTPM`) | device identifiers |
| Windows username and paths | `C:\Users\searc\…` in every `.ps1` | low |

The location is a campus, so the sensitivity is low. Still, remove these from a public thesis repo. Removing them from **history** needs a rewrite (see §5).

## 3. What to move or delete

| Path | Tracked? | Size | Recommendation | Why |
|---|---|---|---|---|
| `logcat_edge50.txt`, `logcat_edge60.txt`, `logcat_edge50pro_live.txt`, `logcat_edge60pro_live.txt` | yes | 2.2 / 5.4 / 12.3 / 6.4 MB | **Move** to a separate evaluation-data archive (thesis CD, Zenodo, or a `data` branch). Delete from `main` | 26 MB of raw logs; the four largest blobs in the repo; location data |
| `logcat_edge50pro.txt`, `logcat_edge60pro.txt` | yes | < 1 KB | Delete | hand-copied excerpts of S1; redundant |
| `logcat_edge50pro_sep15.txt`, `logcat_edge60pro_sep15.txt` | **untracked** | 18 / 47 KB | Keep **out** of git; archive with the others | |
| `silent_events.txt` | yes | 8 KB | Move to the archive. It is cited as evidence in 03 §2.1, so keep a copy | |
| `.logcat_pids.txt`, `.mesh_pids.txt` (tracked); `*_sep15.txt` versions (untracked) | mixed | < 50 B, UTF-16 | Delete | transient capture state |
| `start_capture.ps1`, `start_capture_sep15.ps1`, `monitor_logs.ps1`, `monitor_silent.ps1`, `find_tags.ps1` | 4 tracked, 1 untracked | 1–3 KB | **Move** to `tools/log-capture/`, parameterised (adb serial and paths as arguments, no hard-coded `C:\Users\searc`). Or delete if 03's `analyze_logs.py` replaces them | the capture procedure is part of your methodology, so keep it reproducible but generic |
| `.idea/codeStyles/*`, `.idea/dictionaries/kevinh.xml`, `.idea/icon.svg` | yes | small | **Keep.** Upstream deliberately tracks these (see `.gitignore` `!/.idea/codeStyles`) | not personal files; `kevinh` is the upstream author |
| `.run/Pre-Commit [spotlessApply detekt].run.xml` | yes | small | Keep (upstream) | |
| `.vscode/`, `.kotlin/`, `.gradle/`, `build/`, `.claude/` | not tracked | — | Nothing to do; already ignored (`.vscode/settings.json` only; other `.vscode` files are untracked) | |
| `mesh_service_example/` | yes, 17 files, in `settings.gradle.kts` | — | Keep or drop. It's upstream's example of the AIDL API; removing it also needs `settings.gradle.kts` edited. Not part of ResQ | scope clarity |
| `fastlane/`, `app/src/main/play/listings/…` screenshots (1–2 MB each) | yes | — | Replace upstream store screenshots with ResQ ones, or remove | they show Meshtastic, not ResQ |
| `feature/map/src/test/.../AssignmentEngineTest.kt` + `feature/map/build.gradle.kts` change | untracked / modified | — | **Commit** after running `./gradlew :feature:map:testGoogleDebugUnitTest` | real test evidence for the report |
| `thesis-review/` | untracked | — | Don't commit to the public repo (it contains review notes); keep locally | |

## 4. Suggested `.gitignore` additions

```gitignore
# Device log captures and capture state
logcat_*.txt
silent_events*.txt
.logcat_pids*.txt
.mesh_pids*.txt

# Local capture scripts (keep parameterised versions under tools/ instead)
/start_capture*.ps1
/monitor_*.ps1
/find_tags.ps1

# Review notes
/thesis-review/
```

(`.idea/*` with exceptions, `.kotlin`, `local.properties`, `secrets.properties`, `.claude/` and `**/build/**` are already covered.)

## 5. Removing logs from history (optional, destructive)

`git rm` only removes the files from future commits; the 26 MB and the location data stay in history and in every remote listed in §2. If you want them gone:

1. Make a full backup clone first.
2. `git filter-repo --path-glob 'logcat_*.txt' --path silent_events.txt --path .logcat_pids.txt --path .mesh_pids.txt --invert-paths`
3. Force-push to each remote. This rewrites all commit hashes, so every hash quoted in the thesis and in these review files will change. **Decide this before** you freeze the hashes you cite.

Given the low sensitivity, the simpler option is to delete the files on `main` and accept that history keeps them.

## 6. Licence and attribution restoration (highest priority; see 01 §4)

1. Restore `LICENSE` (GPL-3.0) from `git show 9266caae9:LICENSE`.
2. Restore the per-file `Copyright (c) … Meshtastic LLC` GPL headers that `845fb5d58` and `4bb4dd75f` removed. Spotless can re-apply them (`licenseHeaderFile(...)` in [Spotless.kt:18](../build-logic/convention/src/main/kotlin/org/meshtastic/buildlogic/Spotless.kt#L18)), **but the header templates were emptied too**: `config/spotless/copyright.kt` and `copyright.kts` are now blank, and `copyright.txt` was reduced to "Licensed under GPL-3.0" (`4bb4dd75f`, `845fb5d58`). First restore them with `git checkout 9266caae9 -- config/spotless/`, then run `./gradlew spotlessApply`. Until then, Spotless will *strip* headers rather than add them. Also restore "Meshtastic LLC" where it was replaced by "Atlas LLC" (`gradle.properties`, `secrets.defaults.properties` and 2 more files changed in `4bb4dd75f`). For files you wrote, add your own copyright line under the Meshtastic one.
3. Add `NOTICE` or a Credits section crediting Meshtastic-Android and Codec2 (LGPL-2.1, David Rowe). Codec2's LGPL notice must ship with the source.
4. Put the README from 05 at the repo root.
5. Consider whether the user-facing `example.com` links (`core/strings/.../values/strings.xml:180`) should point back to Meshtastic or to your project page.

These are small, mechanical edits. I can make them if you ask, since this task was suggestions only.

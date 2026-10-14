# 04 — Citation Check

Source: `done.pdf` (thesis report). In-text citations appear **only in Chapter 2** (pp. 7–10), as `[1]`–`[10]`. Chapters 1 and 3–6 and the appendices contain **no citations at all**. The reference list (pp. 45–46) has 15 entries.

I couldn't check online whether the references exist or whether their details (volume, pages, DOI) are correct; that is **not verified**. Look up every entry on IEEE Xplore, Google Scholar or the DOI before submitting.

## 1. In-text citation vs. reference-list entry

| In text | Who/what the text describes (page) | Reference-list entry with that number | Match? |
|---|---|---|---|
| [1] | "Ozgun Pinarer et al.", Humanity Lifeline, BLE + LoRa + LoRaWAN, "5 km × 5 km … up to 99 % delivery" (p. 7) | [1] O. Pinarer and O. Komili, "Humanity Lifeline …," *IEEE Access*, 2025 | ✅ Same work. Minor issues: two authors, so write "Pinarer and Komili", not "et al."; the entry lacks vol./pages/DOI (your research paper has them: vol. 13, pp. 95922–95933, doi 10.1109/ACCESS.2025.3575712). The 99 % and 5 × 5 km figures are not verified against the paper |
| [2] | "El Khaled Z et al.", case studies of the 2004 tsunami and the 2015 Nepal earthquake (p. 7) | [2] B. Samuel et al., "A LoRa Based Emergency Communication Device …," ICTMIM 2025 | ❌ Different author and topic |
| [3] | "Martin Lea", organisational and technical causes of disaster-communication failure (p. 8) | [3] I. R. Lopes et al., "Evaluating the Performance of LoRa Networks in Disaster Monitoring Scenarios," *Sensors* 2025 | ❌ Different author and topic. [3]'s *title* fits the text of in-text [4] better |
| [4] | "Cecílio J et al.", LoRa in flooding, "> 90 % packet delivery" (p. 8) | [4] Semtech, "LoRa Modulation Basics," white paper, 2020 | ❌ |
| [5] | "Arregui Almeida D et al.", gateway-free LoRa mesh on ESP32-S3/SX1262 (p. 8) | [5] Bluetooth SIG, "Bluetooth Low Energy Specification and Overview," 2022 | ❌ |
| [6] | "Sharma A et al.", HELLO-beacon node discovery (p. 9) | [6] NDMA (India), "National Guidelines for Disaster Communication Systems," 2021 | ❌ |
| [7] | "Rahmali N et al.", IoT power optimisation, "up to 50 %" battery gain (p. 9) | [7] Li et al., "BLE2LoRa …," *IEEE IoT Journal*, 2024 | ❌ |
| [8] | "Usman A et al.", WiMesh (p. 9) | [8] Macaraeg et al., "LoRa Mesh Routing Protocol Enhancement …," Globecom Workshops 2024 | ❌ |
| [9] | "Agarwal A et al.", GPS in emergency IoT, "within 50 m is sufficient" (p. 9) | [9] Yen et al., "Temporary Disaster Relief Communication Architecture Using LoRa," *IEEE Comm. Letters*, 2023 | ❌ |
| [10] | "Meshtastic Project Documentation": managed flooding, TTL, AES-256 (p. 10) | [10] Sun et al., "Multi-Priority Data Routing Optimization …," *IEEE Trans. Veh. Tech.*, 2024 | ❌ Meshtastic is not in the reference list at all |

**Result: 1 of 10 in-text citations matches its entry. 9 point to the wrong work.** The survey and the reference list look as if they were written from two different source lists. Neither matches the reference list of your `research paper.pdf` either: of the surveyed authors, only Pinarer appears there.

## 2. Missing references (cited or described in the text, with no entry in the list)

1. El Khaled Z et al. (tsunami/Nepal case study)
2. Martin Lea (disaster-communication failures)
3. Cecílio J et al. (LoRa in floods)
4. Arregui Almeida D et al. (gateway-free LoRa mesh, ESP32-S3/SX1262)
5. Sharma A et al. (HELLO-beacon discovery)
6. Rahmali N et al. (IoT power optimisation)
7. Usman A et al. (WiMesh)
8. Agarwal A et al. (GPS in emergency IoT)
9. Meshtastic Project Documentation

For each of 1–8: find the actual paper and confirm that the specific numbers quoted (99 %, > 90 %, 50 %, 50 m, 5 × 5 km) appear in it. **If you cannot find a paper, remove the paragraph.** An examiner who searches for an untraceable author with a precise statistic will treat it as fabricated, which is a far worse outcome than a shorter survey.

## 3. Unused references (in the list, never cited for their actual content)

- **[11]–[15]** are never cited anywhere: Al-Fuqaha 2015, Centenaro 2016, Augustin 2016, Adelantado 2017, Raza 2017.
- **[2]–[10]** are only "cited" by a number that belongs to a different work, so in practice none of them is cited for its own content either.

That makes **14 of 15 references effectively uncited.** Either cite each one where its content is used (for example, Adelantado [14] and Augustin [13] fit the LoRa range and duty-cycle claims in §3.5.4 and §3.6), or remove it.

## 4. Claims in the body that need a citation but have none

| Location | Claim | Suggested source (verify before use) |
|---|---|---|
| Ch. 1, pp. 1–2 | towers collapse and networks overload during disasters | El Khaled / NDMA [6], once fixed |
| §3.5.4, p. 22 | LoRa range 5–10 km per hop; > 95 % delivery; 24 h battery | Augustin [13], Adelantado [14], or your own measurement (see 03) |
| §3.6, p. 23 | spreading-factor range/throughput trade-off | Semtech [4], Augustin [13] |
| p. 5, 10, 43 | AES-256 encryption | Meshtastic encryption documentation (add the URL and access date) |
| Ch. 4 | managed-flood routing, TTL/hop limit | Meshtastic docs (add) |
| Table 3.4, D-sections | START triage colours (RED/YELLOW/GREEN/BLACK) | Benson, Koenig & Schultz, "Disaster triage: START, then SAVE…," *Prehospital and Disaster Medicine* 11(2), 1996 |
| Features to add (02b) | Hungarian assignment | Kuhn 1955 (*Naval Research Logistics Quarterly*); Munkres 1957 (*J. SIAM*) |
| 02b | point-in-polygon ray casting | Shimrat, "Algorithm 112," *CACM* 5(8), 1962 |
| 02b | Codec2 voice codec | D. Rowe, Codec2 project (LGPL-2.1), URL plus access date |
| 02b | first-aid content | IFRC 2020 guidelines, WHO, etc., as listed inside `emergency_guide.json` |
| 3.5.2 / Ch. 5 | Room, Paging 3, Protocol Buffers, Jetpack Compose | Android developer docs; protobuf docs |
| **Everywhere** | **The app is built on Meshtastic-Android** | Meshtastic-Android repository (GPL-3.0), URL + commit `9266caae9` + access date. **This citation is mandatory** |

## 5. Formatting inconsistencies

- In-text names mix styles ("Ozgun Pinarer" with full first name, "El Khaled Z" with surname then initial). IEEE style uses only the number: "Pinarer and Komili [1] proposed…".
- Several entries lack volume, issue, pages and DOI ([1]–[3], [7]–[10]). The "Technical Standard, 2022" for BLE [5] should name the actual Core Specification version.
- Web sources need a URL and an access date.
- The two-author paper [1] shouldn't use "et al."

## 6. Recommended fix procedure

1. Decide the final list of works you actually read (keep it to the ones you can open and quote).
2. Rewrite Chapter 2 so each paragraph cites the matching number. Check every quoted statistic against the PDF.
3. Add the missing entries (§2 if found, plus §4: Meshtastic-Android, Meshtastic docs, Codec2, START, Kuhn/Munkres).
4. Delete every entry not cited.
5. Use a reference manager (Zotero, or Word's built-in citations) so the numbers can't drift again.

"""Extract every quantitative figure used in 03-log-analysis.md from the logcat captures.

Usage (from repo root):  python -I thesis-review/scripts/analyze_logs.py [--json out.json]
Stdlib only. Read-only: it never modifies the logs.

Sessions and app PIDs are taken from the capture scripts and .mesh_pids*.txt files:
  S1 2026-02-19  logcat_edge50.txt (pid 13397, brief format, full system log)
                 logcat_edge60.txt (pid 28716, brief format, full system log)
  S2 2026-02-20  logcat_edge50pro_live.txt (pid 22379)  logcat_edge60pro_live.txt (pid 28920)
                 silent_events.txt is a filtered excerpt of S2 produced by monitor_silent.ps1
  S3 2026-09-15  logcat_edge50pro_sep15.txt (pid 25641) logcat_edge60pro_sep15.txt (pid 26585)
Year is not stored by logcat; 2026 is assumed from git history (capture scripts committed 2026-02/09).
"""
import json
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
YEAR = 2026

SESSIONS = {
    "S1": {"edge50pro": ("logcat_edge50.txt", "13397"), "edge60pro": ("logcat_edge60.txt", "28716")},
    "S2": {"edge50pro": ("logcat_edge50pro_live.txt", "22379"), "edge60pro": ("logcat_edge60pro_live.txt", "28920")},
    "S3": {"edge50pro": ("logcat_edge50pro_sep15.txt", "25641"), "edge60pro": ("logcat_edge60pro_sep15.txt", "26585")},
}

# threadtime: "02-20 07:25:14.958 22379 22432 D TAG: msg"
RE_THREADTIME = re.compile(r"^(\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+(.*?):\s?(.*)$")
# brief:      "02-19 18:26:25.869 D/TAG( 13397): msg"
RE_BRIEF = re.compile(r"^(\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\s+([VDIWEF])/(.*?)\(\s*(\d+)\):\s?(.*)$")


def ts(s):
    return datetime.strptime(f"{YEAR}-{s}", "%Y-%m-%d %H:%M:%S.%f")


def read_lines(fname, pid):
    """Yield (datetime, level, tag, msg) for lines of the app process only."""
    with open(ROOT / fname, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            raw = raw.rstrip("\r\n")
            m = RE_THREADTIME.match(raw)
            if m:
                if m.group(2) != pid:
                    continue
                yield ts(m.group(1)), m.group(4), m.group(5).strip(), m.group(6)
                continue
            m = RE_BRIEF.match(raw)
            if m and m.group(4) == pid:
                yield ts(m.group(1)), m.group(2), m.group(3).strip(), m.group(5)


def node_hex(n):
    return "!%08x" % (int(n) & 0xFFFFFFFF)


def summ(xs):
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "min": round(min(xs), 3), "median": round(st.median(xs), 3),
            "mean": round(st.mean(xs), 3), "max": round(max(xs), 3)}


RE_SEND = re.compile(r"Sending to radio packet \{\s*to: (\d+)\s+decoded \{\s*portnum: (\w+)\s+payload: \"((?:[^\"\\]|\\.)*)\"\s*\}(.*)\}")
RE_ACK = re.compile(r"\[ackNak\] req=(\d+) routeErr=(\d+) isAck=(true|false) maxRetransmit=(true|false)")
RE_QWAIT = re.compile(r"queueJob packet id=(\d+) waiting")
RE_QOK = re.compile(r"queueJob packet id=(\d+) success (true|false)")


def unescape_c(s):
    """Decode the C-style escaped bytes protobuf's TextFormat prints in `payload: "..."`."""
    out, i = bytearray(), 0
    simple = {"n": 10, "r": 13, "t": 9, "a": 7, "b": 8, "f": 12, "v": 11, "\\": 92, "'": 39, '"': 34}
    while i < len(s):
        c = s[i]
        if c != "\\":
            out.append(ord(c) & 0xFF)
            i += 1
            continue
        nxt = s[i + 1]
        if nxt in "01234567":
            j = i + 1
            while j < len(s) and j < i + 4 and s[j] in "01234567":
                j += 1
            out.append(int(s[i + 1:j], 8) & 0xFF)
            i = j
        else:
            out.append(simple.get(nxt, ord(nxt)))
            i += 2
    return bytes(out)


def decode_position(payload_escaped):
    """Meshtastic Position: field 1 latitude_i (tag 0x0d, sfixed32), field 2 longitude_i (tag 0x15), 1e-7 deg."""
    try:
        b = unescape_c(payload_escaped.replace('\\"', '"'))
    except (IndexError, ValueError):
        return None
    if len(b) < 10 or b[0] != 0x0D or b[5] != 0x15:
        return None
    lat = int.from_bytes(b[1:5], "little", signed=True) / 1e7
    lon = int.from_bytes(b[6:10], "little", signed=True) / 1e7
    return (lat, lon) if -90 <= lat <= 90 and -180 <= lon <= 180 and (lat, lon) != (0, 0) else None


def haversine_m(a, b):
    from math import asin, cos, radians, sin, sqrt
    la1, lo1, la2, lo2 = map(radians, (a[0], a[1], b[0], b[1]))
    h = sin((la2 - la1) / 2) ** 2 + cos(la1) * cos(la2) * sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * asin(sqrt(h))


def classify(port, payload):
    if port == "PRIVATE_APP":
        for k in ("HEARTBEAT_PING", "SILENCE_REPORT", "MANUAL_TRIAGE_PIN", "CLAIM_PIN", "ASSIGNMENT"):
            if k in payload:
                return k
        if "pin_id" in payload:
            return "TRIAGE_PIN_legacy_no_type"
        return "PRIVATE_other"
    if port == "TEXT_MESSAGE_APP":
        if payload.startswith("SOS"):
            return "TEXT_SOS"
        if payload.startswith("SILENT NODE DETECTED"):
            return "TEXT_SILENT_ALERT"
        return "TEXT_chat"
    return port


def analyze_device(fname, pid):
    r = {"file": fname, "pid": pid}
    lines = list(read_lines(fname, pid))
    r["app_lines"] = len(lines)
    if not lines:
        return r, [], {}
    r["first"], r["last"] = lines[0][0].isoformat(sep=" "), lines[-1][0].isoformat(sep=" ")
    r["duration_s"] = round((lines[-1][0] - lines[0][0]).total_seconds(), 1)

    sends, acks, qwait, qok = {}, {}, {}, {}
    send_types, send_meta = Counter(), Counter()
    keepalive, pos_bcast = [], []
    fw_hb = defaultdict(list)
    errors, warn_conn = Counter(), Counter()
    events = []  # (t, kind, detail) for timelines
    skipped_frames = []
    positions = []
    map_spam = 0
    for t, lvl, tag, msg in lines:
        m = RE_SEND.search(msg)
        if m:
            to, port, payload, rest = m.groups()
            pid_m = re.search(r"\bid: (\d+)", rest)
            kind = classify(port, payload)
            wa = "want_ack: true" in rest
            hl = re.search(r"hop_limit: (\d+)", rest)
            pr = re.search(r"priority: (\w+)", rest)
            send_types[kind] += 1
            send_meta[(kind, "broadcast" if to == "4294967295" else "unicast", f"hop_limit={hl.group(1) if hl else 'default'}",
                       f"want_ack={wa}", f"priority={pr.group(1) if pr else 'unset'}")] += 1
            pin = re.search(r'pin_id\\":\\"([0-9a-f-]+)', payload)
            rec = {"t": t, "kind": kind, "to": to, "want_ack": wa, "pin": pin.group(1) if pin else None}
            if port == "POSITION_APP":
                p = decode_position(payload)
                if p:
                    positions.append(p)
            if pid_m:
                sends[pid_m.group(1)] = rec
            events.append((t, "SEND", kind))
            continue
        m = RE_ACK.search(msg)
        if m:
            acks[m.group(1)] = {"t": t, "routeErr": int(m.group(2)), "isAck": m.group(3) == "true", "maxRetransmit": m.group(4) == "true"}
            continue
        m = RE_QWAIT.search(msg)
        if m:
            qwait.setdefault(m.group(1), t)
            continue
        m = RE_QOK.search(msg)
        if m:
            qok[m.group(1)] = (t, m.group(2) == "true")
            continue
        if "BLE keepAlive" in msg:
            keepalive.append(t)
        elif "Sending our position/time" in msg:
            pos_bcast.append(t)
        elif msg.startswith("Firmware heartbeat from node"):
            fw_hb[node_hex(msg.split()[-1])].append(t)
        elif msg.startswith("Showing on map"):
            map_spam += 1
        mm = re.search(r"Skipped (\d+) frames", msg)
        if mm:
            skipped_frames.append(int(mm.group(1)))
        for pat, kind in (
            (r"Ping sent to node (-?\d+) \(missed=(\d+)\)", "PING"),
            (r"Node (-?\d+) marked SILENT", "SILENT"),
            (r"Node (-?\d+) CONFIRMED SILENT", "CONFIRMED_SILENT"),
            (r"Node (-?\d+) came back online", "BACK_ONLINE"),
            (r"Last seen: (\d+)m (\d+)s ago", "LAST_SEEN"),
            (r"onConnectionChanged: (\w+) -> (\w+)", "CONN_CHANGE"),
            (r"^Starting connect", "START_CONNECT"),
            (r"MyNodeInfo received", "MYNODEINFO"),
            (r"Radio interface error: (.*?), shouldReconnect", "RADIO_ERROR"),
            (r"Radio interface connected", "RADIO_CONNECTED"),
            (r"Forcing reconnect", "FORCE_RECONNECT"),
            (r"Meshtastic service not found", "SERVICE_NOT_FOUND"),
            (r"Config-only handshake complete", "CONFIG_DONE"),
            (r"Node-info handshake complete", "NODEINFO_DONE"),
            (r"Received triage pin ([0-9a-f-]+)", "RX_PIN"),
            (r"Received claim for pin ([0-9a-f-]+)", "RX_CLAIM"),
            (r"possible triage packet from (-?\d+), len=(\d+)", "RX_PRIVATE"),
            (r"handlePrivateApp: decoded=(\w+)", "RX_DECODED"),
            (r"text prefix=(HEARTBEAT_PING|SILENCE_REPORT)", "RX_PRIVATE_TEXT"),
        ):
            mm = re.search(pat, msg)
            if mm:
                events.append((t, kind, mm.groups()))
                if kind == "RADIO_ERROR":
                    warn_conn[mm.group(1)] += 1
        if lvl in ("E", "F"):
            errors[re.sub(r"\d+", "N", f"{tag}: {msg}")[:120]] += 1

    r["sent_packets_total"] = sum(send_types.values())
    r["sent_by_type"] = dict(send_types)
    r["sent_by_type_detail"] = {" | ".join(k): v for k, v in sorted(send_meta.items())}

    # ACK round-trip: send (id) -> [ackNak] req=id on the same phone. Only meaningful for want_ack packets.
    rtts, unacked = [], []
    for pid_, s in sends.items():
        if not s["want_ack"]:
            continue
        a = acks.get(pid_)
        if a and a["isAck"]:
            rtts.append({"id": pid_, "kind": s["kind"], "to": node_hex(s["to"]) if s["to"] != "4294967295" else "broadcast",
                         "rtt_s": round((a["t"] - s["t"]).total_seconds(), 3)})
        else:
            unacked.append({"id": pid_, "kind": s["kind"], "to": node_hex(s["to"]) if s["to"] != "4294967295" else "broadcast",
                            "sent": s["t"].isoformat(sep=" ")})
    r["ack_rtt"] = summ([x["rtt_s"] for x in rtts])
    r["ack_rtt_samples"] = rtts
    r["want_ack_sent"] = len(rtts) + len(unacked)
    r["want_ack_unacked"] = unacked
    r["ack_failures"] = sum(1 for a in acks.values() if not a["isAck"] or a["routeErr"] or a["maxRetransmit"])

    # phone -> radio BLE write queue: "waiting" -> "success"
    qlat = [(qok[i][0] - qwait[i]).total_seconds() for i in qok if i in qwait]
    r["ble_queue"] = {"queued": len(qwait), "success_true": sum(1 for v in qok.values() if v[1]),
                      "success_false": sum(1 for v in qok.values() if not v[1]), "latency_s": summ(qlat)}

    def intervals(tlist):
        return [(b - a).total_seconds() for a, b in zip(tlist, tlist[1:])]

    r["ble_keepalive"] = {"count": len(keepalive), "interval_s": summ(intervals(keepalive))}
    r["position_broadcasts"] = {"count": len(pos_bcast), "interval_s": summ(intervals(pos_bcast))}
    r["firmware_heartbeats"] = {n: {"count": len(v), "interval_s": summ(intervals(v))} for n, v in sorted(fw_hb.items())}
    r["errors_E_F"] = dict(errors.most_common(10))
    r["radio_errors"] = dict(warn_conn)
    r["skipped_frames"] = summ(skipped_frames)
    if positions:
        med = (st.median(p[0] for p in positions), st.median(p[1] for p in positions))
        r["own_position"] = {"fixes": len(positions), "median_lat": round(med[0], 5), "median_lon": round(med[1], 5),
                             "max_spread_from_median_m": round(max(haversine_m(med, p) for p in positions), 1)}
    r["map_recompose_log_lines"] = map_spam
    r["map_recompose_per_s"] = round(map_spam / r["duration_s"], 1) if r["duration_s"] else None
    return r, events, sends


def timeline_metrics(dev, events):
    out = {}
    # Silent-node detection timeline (service detector, app/.../SilentNodeDetector.kt)
    sil = [e for e in events if e[1] in ("PING", "SILENT", "CONFIRMED_SILENT", "BACK_ONLINE", "LAST_SEEN")]
    if any(e[1] == "SILENT" for e in sil):
        t_sil = next(e[0] for e in sil if e[1] == "SILENT")
        t_conf = next((e[0] for e in sil if e[1] == "CONFIRMED_SILENT"), None)
        t_back = next((e[0] for e in sil if e[1] == "BACK_ONLINE"), None)
        ls = next((e for e in sil if e[1] == "LAST_SEEN"), None)
        node = next(e[2][0] for e in sil if e[1] == "SILENT")
        pings = [e for e in sil if e[1] == "PING" and e[2][0] == node]
        d = {"node": node_hex(node), "first_unanswered_ping": pings[0][0].isoformat(sep=" ") if pings else None,
             "marked_SILENT": t_sil.isoformat(sep=" ")}
        if ls and t_conf:
            last_heard = t_conf.timestamp() - (int(ls[2][0]) * 60 + int(ls[2][1]))
            lh = datetime.fromtimestamp(last_heard)
            d["last_heard_derived"] = lh.isoformat(sep=" ")
            d["last_heard_to_SILENT_s"] = round((t_sil - lh).total_seconds(), 1)
            d["last_heard_to_CONFIRMED_s"] = round((t_conf - lh).total_seconds(), 1)
        if t_conf:
            d["marked_CONFIRMED"] = t_conf.isoformat(sep=" ")
            d["SILENT_to_CONFIRMED_s"] = round((t_conf - t_sil).total_seconds(), 1)
        if t_back:
            d["back_online"] = t_back.isoformat(sep=" ")
            d["outage_as_seen_by_detector_s"] = round((t_back - t_sil).total_seconds(), 1)
        d["pings_sent_to_node"] = len(pings)
        out["silent_detection"] = d

    # Connection outages: Connected -> Disconnected ... Disconnected -> Connected
    cc = [e for e in events if e[1] == "CONN_CHANGE"]
    outages, down = [], None
    for t, _, (a, b) in cc:
        if b == "Disconnected" and a == "Connected":
            down = t
        if b == "Connected" and down:
            outages.append(round((t - down).total_seconds(), 1))
            down = None
    out["phone_radio_outages_s"] = outages
    # Connect handshake: "Starting connect" -> "MyNodeInfo received"
    hs = []
    for i, e in enumerate(events):
        if e[1] == "START_CONNECT":
            nxt = next((x for x in events[i + 1:] if x[1] == "MYNODEINFO"), None)
            if nxt:
                hs.append(round((nxt[0] - e[0]).total_seconds(), 3))
    out["start_connect_to_mynodeinfo_s"] = hs
    # Automatic reconnect (S3 code path): RADIO_ERROR -> RADIO_CONNECTED -> CONFIG_DONE -> NODEINFO_DONE
    rc = []
    for i, e in enumerate(events):
        if e[1] == "RADIO_ERROR" and "Meshtastic service not found" not in e[2][0]:
            tail = events[i + 1:]
            nxt_err = next((x for x in tail if x[1] == "RADIO_ERROR" and "service not found" not in x[2][0]), None)
            window = [x for x in tail if nxt_err is None or x[0] < nxt_err[0]]

            def first(kind):
                return next((x[0] for x in window if x[1] == kind), None)
            c, cfg, ni = first("RADIO_CONNECTED"), first("CONFIG_DONE"), first("NODEINFO_DONE")
            fr = first("FORCE_RECONNECT")
            rc.append({"error_at": e[0].isoformat(sep=" "), "cause": e[2][0],
                       "error_to_force_reconnect_s": round((fr - e[0]).total_seconds(), 3) if fr else None,
                       "force_reconnect_to_ble_connected_s": round((c - fr).total_seconds(), 3) if (c and fr) else None,
                       "error_to_ble_connected_s": round((c - e[0]).total_seconds(), 3) if c else None,
                       "error_to_config_done_s": round((cfg - e[0]).total_seconds(), 3) if cfg else None,
                       "error_to_nodeinfo_done_s": round((ni - e[0]).total_seconds(), 3) if ni else None,
                       "service_not_found_retries": sum(1 for x in window if x[1] == "SERVICE_NOT_FOUND")})
    out["auto_reconnects"] = rc
    return out


def cross_device(sends_a, events_b, name_a, name_b):
    """Application packets sent by A and logged as received by B (matched by triage pin id)."""
    rx = {}
    for t, kind, g in events_b:
        if kind in ("RX_PIN", "RX_CLAIM"):
            rx.setdefault((kind, g[0]), t)
    res = []
    for s in sends_a.values():
        if s["kind"] in ("MANUAL_TRIAGE_PIN", "CLAIM_PIN", "TRIAGE_PIN_legacy_no_type") and s["pin"]:
            key = ("RX_CLAIM" if s["kind"] == "CLAIM_PIN" else "RX_PIN", s["pin"])
            t_rx = rx.get(key)
            # legacy S1 packet: receiver logs only "possible triage packet ... decoded=null"
            if t_rx is None and s["kind"] == "TRIAGE_PIN_legacy_no_type":
                t_rx = next((t for t, k, g in events_b if k == "RX_PRIVATE" and t >= s["t"]), None)
                status = "received_but_decode_failed" if t_rx else "not_seen"
            else:
                status = "received_and_decoded" if t_rx else "not_seen"
            res.append({"from": name_a, "to": name_b, "kind": s["kind"], "pin": s["pin"][:8], "sent": s["t"].isoformat(sep=" "),
                        "status": status,
                        "one_way_s_uncorrected": round((t_rx - s["t"]).total_seconds(), 3) if t_rx else None})
    # heartbeat pings from A delivered to B (B logs "text prefix=HEARTBEAT_PING"); matched to the nearest earlier send
    pings = sorted(s["t"] for s in sends_a.values() if s["kind"] == "HEARTBEAT_PING")
    for t, kind, g in events_b:
        if kind == "RX_PRIVATE_TEXT" and g[0] == "HEARTBEAT_PING":
            prev = [p for p in pings if p <= t]
            if prev:
                res.append({"from": name_a, "to": name_b, "kind": "HEARTBEAT_PING", "pin": "-", "sent": prev[-1].isoformat(sep=" "),
                            "status": "received", "one_way_s_uncorrected": round((t - prev[-1]).total_seconds(), 3)})
    return res


def main():
    out = {}
    for sname, devs in SESSIONS.items():
        sess = {}
        per = {}
        for dname, (fname, pid) in devs.items():
            r, ev, sends = analyze_device(fname, pid)
            r.update(timeline_metrics(dname, ev))
            sess[dname] = r
            per[dname] = (ev, sends)
        a, b = "edge50pro", "edge60pro"
        sess["cross_device"] = cross_device(per[a][1], per[b][0], a, b) + cross_device(per[b][1], per[a][0], b, a)
        pa, pb = sess[a].get("own_position"), sess[b].get("own_position")
        if pa and pb:
            sess["phone_separation_m"] = round(haversine_m((pa["median_lat"], pa["median_lon"]), (pb["median_lat"], pb["median_lon"])), 1)
        out[sname] = sess
    # hardware / node identity evidence (all files)
    hw, users = Counter(), Counter()
    for f in sorted(ROOT.glob("logcat_*.txt")):
        txt = f.read_text(encoding="utf-8", errors="replace")
        hw.update(re.findall(r"using reported target ([\w-]+)", txt))
        users.update(re.findall(r"MeshUser\(id=([^,]*), longName=([^,]*),", txt))
    out["hardware_targets"] = dict(hw)
    out["nodes_seen"] = {f"{k[0]} / {k[1]}": v for k, v in users.items()}
    out["fatal_or_anr_lines"] = sum(len(re.findall(r"FATAL EXCEPTION|ANR in ", f.read_text(encoding="utf-8", errors="replace")))
                                    for f in ROOT.glob("logcat_*.txt"))
    js = json.dumps(out, indent=2, default=str)
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(js, encoding="utf-8")
    print(js)


if __name__ == "__main__":
    main()

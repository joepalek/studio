"""
pool_test_battery.py
====================
8-test quality gate for all Tier 1 pool agents.
Run manually or called by pool_job_creator.py.

Usage:
  python pool_test_battery.py --pool wasde-parser      # test one pool
  python pool_test_battery.py --pool wasde-parser --dry # skip live AI calls
  python pool_test_battery.py --all                    # test all queued pools
  python pool_test_battery.py --status                 # show catalog summary

Outputs result to:
  pool_catalog.json        (test_results field updated)
  data/review-queue.json   (PASS pools queued for human review)
  logs/pool-battery.log    (full test log)
"""
import json, sys, time, logging, argparse, importlib.util
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "G:/My Drive/Projects/_studio")

STUDIO = Path("G:/My Drive/Projects/_studio")
CATALOG_PATH  = STUDIO / "pool_catalog.json"
QUEUE_PATH    = STUDIO / "data/review-queue.json"
LOG_PATH      = STUDIO / "logs/pool-battery.log"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── LOGGING ────────────────────────────────────────────────────────

def setup_log():
    log = logging.getLogger("pool_battery")
    log.setLevel(logging.INFO)
    if not log.handlers:
        fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
        fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s",
                                          datefmt="%Y-%m-%d %H:%M:%S"))
        log.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
        log.addHandler(ch)
    return log

# ── CATALOG HELPERS ────────────────────────────────────────────────

def load_catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

def save_catalog(catalog):
    tmp = str(CATALOG_PATH) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    import os; os.replace(tmp, CATALOG_PATH)

def get_pool(catalog, pool_id):
    for p in catalog["pools"]:
        if p["pool_id"] == pool_id:
            return p
    return None

# ── TEST RUNNERS ───────────────────────────────────────────────────

def t1_fetch(pool, agent_module, log):
    """T1: Can the agent fetch data?"""
    log.info("  T1 FETCH...")
    try:
        t0 = time.time()
        raw = agent_module.fetch_raw(agent_module.AGENT_CONFIG)
        elapsed = time.time() - t0
        if not raw or len(raw) < 500:
            return {"result":"FAIL","reason":f"Response too small ({len(raw)} bytes)"}
        log.info(f"  T1 PASS — {len(raw):,} chars in {elapsed:.1f}s")
        return {"result":"PASS","bytes":len(raw),"seconds":round(elapsed,1)}
    except Exception as e:
        log.warning(f"  T1 FAIL — {str(e)[:100]}")
        return {"result":"FAIL","reason":str(e)[:100]}


def t2_parse(pool, agent_module, raw, log):
    """T2: Does parse_raw() return usable records?"""
    log.info("  T2 PARSE...")
    expected = pool.get("expected_fields", [])
    try:
        records = agent_module.parse_raw(raw, agent_module.AGENT_CONFIG)
        if not records:
            return {"result":"FAIL","reason":"Zero records returned"}
        # Check field coverage — but also accept narrative-only months
        total_fields = len(expected) * len(records)
        populated = sum(1 for r in records for f in expected
                        if r.get(f) not in (None, "", [], {}))
        coverage = (populated / total_fields * 100) if total_fields > 0 else 0
        # Check if narrative field covers the gap (no-change months)
        with_narrative = sum(1 for r in records if r.get("narrative",""))
        narrative_coverage = (with_narrative / len(records) * 100) if records else 0
        if coverage < 60 and narrative_coverage < 60:
            return {"result":"FAIL",
                    "reason":f"Field coverage {coverage:.0f}% < 60% and narrative coverage {narrative_coverage:.0f}% < 60%",
                    "records":len(records),"coverage":round(coverage,1)}
        mode = "table" if coverage >= 60 else "narrative"
        log.info(f"  T2 PASS — {len(records)} records, {coverage:.0f}% numeric, {narrative_coverage:.0f}% narrative [{mode} mode]")
        return {"result":"PASS","records":len(records),"coverage":round(coverage,1),
                "narrative_coverage":round(narrative_coverage,1),"mode":mode}
    except Exception as e:
        log.warning(f"  T2 FAIL — {str(e)[:100]}")
        return {"result":"FAIL","reason":str(e)[:100]}


def t3_plausibility(pool, records, log):
    """T3: Are the values sane? (flags don't auto-fail, >25% implausible = fail)"""
    log.info("  T3 PLAUSIBILITY...")
    flags = []
    total_checks = 0
    implausible = 0
    for r in records:
        for k, v in r.items():
            if v in (None, "", [], {}): continue
            total_checks += 1
            s = str(v)
            # Numeric sanity: reject negatives for supply figures
            try:
                num = float(s.replace(",",""))
                if num < 0:
                    flags.append(f"{k}={v} negative")
                    implausible += 1
            except: pass
            # Date sanity: reject dates before 2000 or after 2030
            if "date" in k.lower() and len(s) >= 4:
                try:
                    year = int(s[:4])
                    if not (2000 <= year <= 2030):
                        flags.append(f"{k}={s} year out of range")
                        implausible += 1
                except: pass
    pct = (implausible / total_checks * 100) if total_checks > 0 else 0
    if pct > 25:
        log.warning(f"  T3 FAIL — {pct:.0f}% implausible values")
        return {"result":"FAIL","implausible_pct":round(pct,1),"flags":flags[:5]}
    if flags:
        log.info(f"  T3 WARN — {len(flags)} suspicious values flagged")
        return {"result":"WARN","implausible_pct":round(pct,1),"flags":flags[:5]}
    log.info(f"  T3 PASS — {total_checks} values checked, all plausible")
    return {"result":"PASS","checked":total_checks}


def t4_consistency(pool, agent_module, log):
    """T4: Does data change as expected? (uses checksum comparison)"""
    log.info("  T4 CONSISTENCY...")
    import hashlib
    cadence = pool.get("cadence","monthly")
    try:
        raw1 = agent_module.fetch_raw(agent_module.AGENT_CONFIG)
        ck1 = hashlib.md5(raw1.encode()).hexdigest()[:12]
        # For daily/weekly sources: immediate re-fetch should be same (stable API)
        # For monthly: we just verify data has content — full consistency needs 2 runs
        if cadence == "monthly":
            log.info(f"  T4 PASS (monthly — single run checksum: {ck1})")
            return {"result":"PASS","checksum":ck1,"note":"Monthly cadence — single-run check"}
        time.sleep(2)
        raw2 = agent_module.fetch_raw(agent_module.AGENT_CONFIG)
        ck2 = hashlib.md5(raw2.encode()).hexdigest()[:12]
        if ck1 != ck2:
            log.warning(f"  T4 WARN — checksums differ between fetches (unstable source?)")
            return {"result":"WARN","reason":"Source data changed between two rapid fetches"}
        log.info(f"  T4 PASS — stable checksum {ck1}")
        return {"result":"PASS","checksum":ck1}
    except Exception as e:
        return {"result":"FAIL","reason":str(e)[:100]}

def t5_dual_ai(pool, agent_module, normalized, log, dry=False):
    """T5: Do Mistral and Gemini agree on the signal?"""
    log.info("  T5 DUAL AI SIGNAL...")
    if dry:
        log.info("  T5 SKIP (dry mode)")
        return {"result":"SKIP","reason":"dry mode"}
    try:
        from wasde_dual_ai import dual_synthesize
        cfg = agent_module.AGENT_CONFIG
        result = dual_synthesize(normalized, cfg, log)
        conf = result["confidence"]
        agree = result["agreement"]
        if conf == "failed":
            return {"result":"FAIL","reason":"Both AI models failed"}
        if conf == "consensus":
            log.info(f"  T5 PASS CONSENSUS — A={result['model_a_direction']} B={result['model_b_direction']}")
            return {"result":"PASS","confidence":"consensus",
                    "model_a":result["model_a_direction"],"model_b":result["model_b_direction"]}
        log.info(f"  T5 WARN DIVERGENT — A={result['model_a_direction']} B={result['model_b_direction']}")
        return {"result":"WARN","confidence":"divergent",
                "model_a":result["model_a_direction"],"model_b":result["model_b_direction"],
                "note":"Divergent signals — human review needed but not a hard fail"}
    except Exception as e:
        log.warning(f"  T5 FAIL — {str(e)[:80]}")
        return {"result":"FAIL","reason":str(e)[:80]}


def t6_trend(pool, agent_module, log, dry=False):
    """T6: Can we detect signal variation over 3 data points?"""
    log.info("  T6 TREND DETECTION...")
    if dry:
        return {"result":"SKIP","reason":"dry mode"}
    # For monthly pools: try last 3 months using URL pattern if available
    cadence = pool.get("cadence","monthly")
    if cadence != "monthly":
        log.info("  T6 PASS (non-monthly — single run sufficient)")
        return {"result":"PASS","note":"Non-monthly cadence — trend check on live data"}
    from datetime import datetime, timedelta
    directions = []
    for months_back in [1, 2, 3]:
        try:
            cfg_copy = dict(agent_module.AGENT_CONFIG)
            # Only works if agent has _build_wasde_url pattern
            if hasattr(agent_module, "_build_wasde_url"):
                target = datetime.now() - timedelta(days=30 * months_back)
                cfg_copy["source_url"] = agent_module._build_wasde_url(target)
            raw = agent_module.fetch_raw(cfg_copy)
            records = agent_module.parse_raw(raw, cfg_copy)
            if records:
                # Use pre-computed signals
                sigs = [r.get("signal","UNKNOWN") for r in records]
                dominant = max(set(sigs), key=sigs.count)
                directions.append(dominant)
                time.sleep(2)
        except Exception as e:
            log.warning(f"  T6 month-{months_back} failed: {str(e)[:60]}")
    if not directions:
        return {"result":"FAIL","reason":"Could not fetch historical data"}
    non_neutral = [d for d in directions if d not in ("NEUTRAL","UNKNOWN")]
    score = "HIGH" if len(non_neutral) >= 2 else "MEDIUM" if len(non_neutral) == 1 else "LOW"
    if score == "LOW":
        log.info(f"  T6 WARN — all NEUTRAL signals, low trend detectability")
        return {"result":"WARN","trend_score":score,"directions":directions}
    log.info(f"  T6 PASS — trend score {score}, directions={directions}")
    return {"result":"PASS","trend_score":score,"directions":directions}


def t7_sellability(pool, t1, t2, t3, t5, t6, log):
    """T7: Automated sellability scoring 1-10."""
    log.info("  T7 SELLABILITY SCORING...")
    scores = {}
    # Freshness (daily=10, weekly=8, monthly=6, annual=2)
    cadence_scores = {"daily":10,"weekly":8,"monthly":6,"annual":2}
    scores["freshness"] = cadence_scores.get(pool.get("cadence","monthly"), 5)
    # Signal clarity from T5
    t5r = t5.get("result","FAIL")
    scores["signal_clarity"] = 10 if t5r == "PASS" else 6 if t5r == "WARN" else 3
    # Trend detectability from T6
    trend = t6.get("trend_score","LOW") if t6.get("result") in ("PASS","WARN") else "LOW"
    scores["trend"] = {"HIGH":10,"MEDIUM":7,"LOW":4}.get(trend, 4)
    # Reliability: how many tests passed cleanly
    test_results = [t1, t2, t3, t5, t6]
    passes = sum(1 for t in test_results if t.get("result") == "PASS")
    warns  = sum(1 for t in test_results if t.get("result") == "WARN")
    scores["reliability"] = round((passes * 10 + warns * 6) / (len(test_results) * 10) * 10, 1)
    # Uniqueness: placeholder — human sets this post-review
    scores["uniqueness"] = 5
    # Weighted average
    weights = {"freshness":0.2,"signal_clarity":0.3,"trend":0.2,"reliability":0.2,"uniqueness":0.1}
    total = sum(scores[k] * weights[k] for k in scores)
    tier = "Institutional" if total >= 8 else "Pro" if total >= 6 else "Free"
    log.info(f"  T7 COMPLETE — sellability={total:.1f}/10, recommended_tier={tier}")
    return {"result":"PASS","score":round(total,1),"breakdown":scores,"recommended_tier":tier}


def t8_schema(pool, agent_module, log, dry=False):
    """T8: Does the agent output conform to Tier 1 schema?"""
    log.info("  T8 SCHEMA VALIDATION...")
    state_path = Path(agent_module.AGENT_CONFIG.get("state_path",""))
    try:
        result = agent_module.run(agent_module.AGENT_CONFIG, dry=True)
        status = result.get("status")
        if status not in ("ok","skipped","empty"):
            return {"result":"FAIL","reason":f"run() returned status={status}"}
        # Check state.json written
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            required = {"last_run","last_checksum","run_count","handoff_note"}
            missing = required - set(state.keys())
            if missing:
                return {"result":"FAIL","reason":f"state.json missing: {missing}"}
        log.info(f"  T8 PASS — dry run status={status}")
        return {"result":"PASS","run_status":status}
    except Exception as e:
        log.warning(f"  T8 FAIL — {str(e)[:100]}")
        return {"result":"FAIL","reason":str(e)[:100]}

# ── BATTERY RUNNER ─────────────────────────────────────────────────

def run_battery(pool_id, dry=False, url_override=None):
    log = setup_log()
    catalog = load_catalog()
    pool = get_pool(catalog, pool_id)

    if not pool:
        log.error(f"Pool '{pool_id}' not found in catalog")
        return None

    log.info(f"=== BATTERY START: {pool_id} | dry={dry} ===")
    t0 = time.time()

    # Load agent module dynamically
    agent_file = pool.get("agent_file")
    agent_module = None
    if agent_file:
        agent_path = STUDIO / agent_file
        if agent_path.exists():
            spec = importlib.util.spec_from_file_location(pool_id, agent_path)
            agent_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(agent_module)
            log.info(f"Loaded agent: {agent_path}")
            # Apply URL override AFTER module is loaded
            if url_override:
                agent_module.AGENT_CONFIG["source_url"] = url_override
                log.info(f"URL override: {url_override}")
        else:
            log.warning(f"Agent file not found: {agent_path} — T1/T2/T4/T8 will fail")

    results = {}

    # T1 FETCH
    if agent_module:
        t1 = t1_fetch(pool, agent_module, log)
        raw = None
        if t1["result"] == "PASS":
            try: raw = agent_module.fetch_raw(agent_module.AGENT_CONFIG)
            except: pass
    else:
        t1 = {"result":"SKIP","reason":"No agent file built yet"}
        raw = None
    results["T1_fetch"] = t1

    # T2 PARSE
    records = []
    if agent_module and raw and t1["result"] == "PASS":
        t2 = t2_parse(pool, agent_module, raw, log)
        if t2["result"] == "PASS":
            try: records = agent_module.parse_raw(raw, agent_module.AGENT_CONFIG)
            except: pass
    else:
        t2 = {"result":"SKIP","reason":"T1 failed or no agent"}
    results["T2_parse"] = t2

    # T3 PLAUSIBILITY
    if records:
        t3 = t3_plausibility(pool, records, log)
    else:
        t3 = {"result":"SKIP","reason":"No records from T2"}
    results["T3_plausibility"] = t3

    # T4 CONSISTENCY
    if agent_module:
        t4 = t4_consistency(pool, agent_module, log)
    else:
        t4 = {"result":"SKIP","reason":"No agent file"}
    results["T4_consistency"] = t4

    # Normalize for T5
    normalized = "[]"
    if agent_module and records:
        try:
            from ai_gateway import call as gw_call
            prompt = (f"Normalize this data to clean JSON array, no markdown:\n"
                      f"{json.dumps(records[:10], ensure_ascii=False)}")
            resp = gw_call(prompt, task_type="batch", max_tokens=500)
            normalized = resp.text if resp.success else json.dumps(records, ensure_ascii=False)
        except: normalized = json.dumps(records, ensure_ascii=False)

    # T5 DUAL AI
    t5 = t5_dual_ai(pool, agent_module, normalized, log, dry=dry) if agent_module \
         else {"result":"SKIP","reason":"No agent file"}
    results["T5_dual_ai"] = t5

    # T6 TREND
    t6 = t6_trend(pool, agent_module, log, dry=dry) if agent_module \
         else {"result":"SKIP","reason":"No agent file"}
    results["T6_trend"] = t6

    # T7 SELLABILITY
    t7 = t7_sellability(pool, t1, t2, t3, t5, t6, log)
    results["T7_sellability"] = t7

    # T8 SCHEMA
    t8 = t8_schema(pool, agent_module, log, dry=dry) if agent_module \
         else {"result":"SKIP","reason":"No agent file"}
    results["T8_schema"] = t8

    # ── OVERALL VERDICT ────────────────────────────────────────────
    hard_fails = [k for k, v in results.items() if v.get("result") == "FAIL"]
    warns      = [k for k, v in results.items() if v.get("result") == "WARN"]
    sellability = t7.get("score", 0)

    if hard_fails:
        overall = "FAILED"
        new_status = "failed"
    elif sellability >= 6:
        overall = "PASS"
        new_status = "review"
    else:
        overall = "LOW_SIGNAL"
        new_status = "review"  # Still send to review — human decides

    elapsed = round(time.time() - t0, 1)
    log.info(f"=== BATTERY COMPLETE: {pool_id} | {overall} | {elapsed}s ===")
    if hard_fails: log.warning(f"  Hard fails: {hard_fails}")
    if warns:      log.info(f"  Warnings: {warns}")

    # ── UPDATE CATALOG ─────────────────────────────────────────────
    for p in catalog["pools"]:
        if p["pool_id"] == pool_id:
            p["status"]            = new_status
            p["test_results"]      = results
            p["sellability_score"] = sellability
            p["recommended_tier"]  = t7.get("recommended_tier")
            break
    save_catalog(catalog)

    # ── WRITE TO REVIEW QUEUE ──────────────────────────────────────
    if new_status == "review":
        try:
            queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        except:
            queue = {"entries": []}
        # Remove existing entry for this pool if any
        queue["entries"] = [e for e in queue.get("entries",[])
                            if e.get("pool_id") != pool_id]
        synthesis_sample = ""
        if t5.get("result") in ("PASS","WARN"):
            synthesis_sample = str(t5.get("model_a",""))[:200]
        queue["entries"].append({
            "pool_id":          pool_id,
            "pool_number":      pool.get("pool_number"),
            "pool_name":        pool.get("pool_name"),
            "status":           "AWAITING_REVIEW",
            "overall":          overall,
            "sellability_score": sellability,
            "recommended_tier": t7.get("recommended_tier"),
            "queued_at":        datetime.now().isoformat(),
            "test_results":     {k: v.get("result","?") for k, v in results.items()},
            "test_detail":      results,
            "sample_synthesis": synthesis_sample,
            "hard_fails":       hard_fails,
            "warnings":         warns,
            "human_decision":   None,
            "rejection_reason": None,
            "approved_at":      None,
        })
        tmp = str(QUEUE_PATH) + ".tmp"
        with open(tmp,"w",encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
        import os; os.replace(tmp, QUEUE_PATH)
        log.info(f"Added to review queue: {QUEUE_PATH}")

    return {"pool_id":pool_id,"overall":overall,"sellability":sellability,
            "hard_fails":hard_fails,"warns":warns,"elapsed":elapsed}

# ── CLI ENTRYPOINT ─────────────────────────────────────────────────

def show_status():
    catalog = load_catalog()
    print(f"\n{'='*60}")
    print(f"POOL CATALOG STATUS — {catalog['meta']['total_pools']} pools")
    print(f"{'='*60}")
    by_status = {}
    for p in catalog["pools"]:
        s = p["status"]
        by_status.setdefault(s, []).append(p)
    for status, pools in sorted(by_status.items()):
        print(f"\n  {status.upper()} ({len(pools)})")
        for p in pools:
            score = p.get("sellability_score")
            score_str = f" | sell={score:.1f}" if score else ""
            print(f"    #{p['pool_number']:3d} {p['pool_id']:30s} {p.get('data_category','?')}{score_str}")
    print()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Pool Test Battery")
    parser.add_argument("--pool",   help="Pool ID to test")
    parser.add_argument("--all",    action="store_true", help="Test all queued pools")
    parser.add_argument("--status", action="store_true", help="Show catalog summary")
    parser.add_argument("--url",    help="Override source URL (useful for historical testing)")
    parser.add_argument("--dry",    action="store_true", help="Skip live AI calls")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.pool:
        result = run_battery(args.pool, dry=args.dry, url_override=args.url)
        print(f"\nResult: {result}")
        sys.exit(0 if result and result["overall"] in ("PASS","LOW_SIGNAL") else 1)
    elif args.all:
        catalog = load_catalog()
        queued = [p["pool_id"] for p in catalog["pools"] if p["status"] == "queued"]
        print(f"Testing {len(queued)} queued pools...")
        results = []
        for pool_id in queued:
            r = run_battery(pool_id, dry=args.dry)
            results.append(r)
            time.sleep(5)  # rate limit between pools
        passed = sum(1 for r in results if r and r["overall"] in ("PASS","LOW_SIGNAL"))
        print(f"\nBattery complete: {passed}/{len(queued)} passed")
    else:
        parser.print_help()

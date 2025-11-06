import os, subprocess, sys, glob, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LSG_DIR = os.path.join(ROOT, "lsg")

pyexe = sys.executable
results = []

# Wenn RUN_LSG_TIMEOUT_SECS > 0 gesetzt ist, wird dieser Timeout pro Level verwendet (Sekunden).
# Setze nicht oder auf 0, um unbegrenzt zu warten (empfohlen, wenn Framework im Test-Modus selbst endet).
TIMEOUT_SECS = int(os.getenv("RUN_LSG_TIMEOUT_SECS", "0"))

paths = sorted(glob.glob(os.path.join(LSG_DIR, "lsg*.py")))
if not paths:
    print("Keine lsg/*.py Dateien gefunden.")
    sys.exit(1)

for path in paths:
    name = os.path.basename(path)
    print(f"\n=== Running {name} ===")
    env = os.environ.copy()
    env["OOP_TEST"] = "1"
    env["PYTHONPATH"] = ROOT  # damit 'import framework' aus lsg funktioniert

    proc = subprocess.Popen(
        [pyexe, path],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=env, text=True, bufsize=1
    )

    out_lines = []
    start = time.time()

    try:
        if TIMEOUT_SECS and TIMEOUT_SECS > 0:
            # communicate mit Timeout (einfacher Fall)
            out, _ = proc.communicate(timeout=TIMEOUT_SECS)
            out_lines = out.splitlines(True)
            for l in out_lines:
                print(l, end="")
        else:
            # Live-Streaming und unbegrenztes Warten
            with proc.stdout:
                for line in proc.stdout:
                    print(line, end="")
                    out_lines.append(line)
            proc.wait()
    except subprocess.TimeoutExpired:
        proc.kill()
        # versuche Restausgabe einzulesen
        try:
            rest = proc.stdout.read() if proc.stdout else ""
            if rest:
                print(rest)
                out_lines.append(rest)
        except Exception:
            pass
        print("=> TIMEOUT")
        results.append((name, False, 124))
        continue

    rc = proc.returncode
    ok = (rc == 0)
    # determine expectation: files containing '_expected_fail' are expected to fail
    expected_ok = ("_expected_fail" not in name)
    print(f"=> {'OK' if ok else f'FAIL (code {rc})'} (expected: {'OK' if expected_ok else 'FAIL'})")
    results.append((name, ok, rc, expected_ok))

print("\n--- summary ---")
for name, ok, code, expected_ok in results:
    status = "OK" if ok else f"FAIL ({code})"
    expect = "OK" if expected_ok else "FAIL"
    print(f"{name}: {status} (expected: {expect})")

# Report deviations: where actual result differs from expected
deviations = []
for name, ok, code, expected_ok in results:
    if ok != expected_ok:
        if ok and not expected_ok:
            deviations.append((name, 'UNEXPECTED_PASS'))
        elif (not ok) and expected_ok:
            deviations.append((name, f'UNEXPECTED_FAIL (code {code})'))

if deviations:
    print("\nDeviations detected:")
    for name, reason in deviations:
        print(f" - {name}: {reason}")
    # return non-zero to indicate mismatch between actual and expected outcomes
    sys.exit(2)
else:
    print("\nAll tests behaved as expected.")
    sys.exit(0)
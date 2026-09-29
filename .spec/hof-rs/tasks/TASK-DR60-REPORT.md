# TASK-DR60-REPORT — the `endpoint_liveness` flake: characterised, located, fixed at the cause

> Implementation report for `.spec/hof-rs/tasks/TASK-DR60.md`.
> Offline batch. Tested tree: outer repo `F:\moonbit-hof-rs`,
> commit **`ef74c6092f4ea053aedd8bd94b69b84dd64719d4`** plus exactly one worktree
> change (`tests/endpoint_liveness.rs`, +12 lines / -0).
> Host: Windows 11 Pro, build 26100; `rustc 1.98.0 (88d9e12ae 2026-08-18)`,
> `cargo 1.98.0`; 16 logical processors.

---

## 1. Conclusion and reproduction statistics

### 1.1 Conclusion

The flake is a **defect of the test's own loopback double**, not of the product.
`ScriptedMcp` makes its *listener* non-blocking and then reads the **accepted**
socket as if it were blocking.  A socket accepted from a non-blocking listener
inherits non-blocking mode, so the double's first `read` returns `WouldBlock`
whenever it wins the race against the client's request, `serve` takes its
`Err(_) => return` arm, and the connection is closed **without ever answering**.
The client (`ureq`) reports that as a transport failure while reading the status
line — exactly `os error 10053`/`10054`.

Fix: one statement, at the accept site, putting the accepted stream back into
blocking mode — the mode `serve` already assumes.  No sleep was lengthened, no
retry was added, no assertion was relaxed, no test was weakened, deleted or
`#[ignore]`d.

### 1.2 It also fails when run **alone** — the decisive characterisation fact

The task asked whether the failure appears only under full-suite concurrency.
It does **not**: it reproduces when the `endpoint_liveness` target is executed by
itself, with no other target and no other test in the process.

| Characterisation | Runs | Failed | Rate |
|---|---|---|---|
| `cargo test --offline --test endpoint_liveness` (driver 1) | 25 | 1 (run 16) | 4.0% |
| `cargo test --offline --test endpoint_liveness` (driver 2) | 40 | 1 (run 22) | 2.5% |
| **alone, total** | **65** | **2** | **3.1%** |
| pre-existing measurement by the parent batch (direct binary runs) | 111 | 2 | 1.8% |
| full-suite runs by the parent batch before this batch | 6 | 1 suite | 1 of 6 |

The failure is **process-internal and scheduler-timing dependent**, not a
resource contention effect between targets.  Each and every failure recorded
identically:

```
thread 'the_editor_endpoint_state_is_separate' (99780) panicked at tests\endpoint_liveness.rs:435:10:
the editor endpoint is alive: MCP transport failure to http://127.0.0.1:52983/mcp:
http://127.0.0.1:52983/mcp: Network Error: 你的主机中的软件中止了一个已建立的连接。 (os error 10053)
test result: FAILED. 6 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 4.07s
```

- Driver 1, run 16: verbatim block recorded in `.dr60/alone1.log`
  (`exit=101 :: test result: FAILED. 6 passed; 1 failed`).
- Driver 2, run 22: full log at `.dr60/raw_alone/run022.log`, reproduced above
  character for character (port `52983` in that run; the parent batch saw the
  same panic with `10054`).  Every other run in both drivers was
  `test result: ok. 7 passed; 0 failed; 0 ignored`, `exit=0`.
- The raw `test result:` lines and exit codes for all 65 alone-runs are in
  `.dr60/raw_alone/summary.txt` (40 runs) and `.dr60/alone1.log` (25 runs).

### 1.3 The instrumented probe settles "client never answered" vs "double never answered"

A temporary probe test (`.dr60`-logged, deleted before the final tree — see §5)
repeated the **exact call shape** of the failing test, with the double counting
whether `serve` ever saw the client's bytes.

Every failing iteration reported **the same signature**:

```
iter=37  FAILED editor=http://127.0.0.1:50770/mcp game=http://127.0.0.1:50771/mcp game_port=50771
         served=1 would_block=1 read_error=0
         error=MCP transport failure … Error encountered in the status line: 远程主机强迫关闭了一个现有的连接。 (os error 10054)
iter=80  FAILED … served=1 would_block=1 … (os error 10053)
iter=100 FAILED … served=1 would_block=1 … (os error 10053)
```

- `served=1` — the connection **did** reach the double (so this is not a
  connect-level or port-level problem).
- `would_block=1` — the double's read path returned `WouldBlock` (its first read
  lost the race against the client's bytes), i.e. the server-side socket was
  non-blocking.  `serve` returns on the first such error, so the counter is
  effectively a boolean: the double did take the give-up path.
  `read_error=0` — it was not an I/O error, not a reset from a peer.
- The client-side error is the consequence: the double took
  `Err(_) => return` (`serve`: `:139` post-fix / `:127` pre-fix), dropped the
  stream and answered nothing, so `ureq`'s status-line read failed (its
  `read_next_line` maps a read into `10053`/`10054`;
  `ureq-2.12.1\src\response.rs:773-800`, the message at `:791`).

The probe's *own* summary, for reference (`probe_editor_double.log`):

```
iterations=1200
iter=37 FAILED …
iter=80 FAILED …
iter=100 FAILED …
```

(the run was stopped by the operator at iteration ~100 because the failing
driver was being deleted; the numbers above are the complete failure record it
produced before deletion).

---

## 2. Cause, with file:line evidence

### 2.1 The mechanism, step by step

| # | Location (pre-fix `HEAD:tests/endpoint_liveness.rs`, blob `2e5b95c7…`) | What happens |
|---|---|---|
| 1 | `:57-59` `listener.set_nonblocking(true)` | the accept loop is made non-blocking so it can poll `shutdown` with a 2 ms back-off (`:73-75`) |
| 2 | `:68-69` `listener.accept()` → `Ok((stream, _))` | a socket accepted from a **non-blocking listener inherits non-blocking mode** |
| 3 | `:71` `serve(stream, …)` | `serve` reads once (`:124-128`) **before** looping, and treats any error as "give up": `Err(_) => return` |
| 4 | `:124-128` | if the client's request bytes have not yet landed in the receive buffer, `read` returns `WouldBlock` **immediately** — no waiting, because the socket is non-blocking.  In practice it is the **first** read that loses this race (the double returns on the first failure, so the counter can only ever be 1) |
| 5 | `:127` `Err(_) => return` | the stream is dropped. No reply is ever written, so the TCP connection ends with nothing in it |
| 6 | client (`McpClient::post` → `ureq`) | the status-line read fails → `Network Error: Error encountered in the status line: … (os error 10053/10054)` |
| 7 | `tests/endpoint_liveness.rs:435` `.expect("the editor endpoint is alive")` | panics. `:435` is the pre-fix line the panic named; the fix adds 12 lines above it, so the same `expect` now sits at `:447` |

Post-fix line numbers for the same extract, for cross-checking:
`listener.set_nonblocking(true)` = `:64`; the new
`stream.set_nonblocking(false)` = `:77-82`; the polling arm = `:85-87`;
`serve` = `:132`; its first read = `:136-140`, the give-up at `:139`;
`the_editor_endpoint_state_is_separate` = `:423-452`.

The race is therefore a **pure test-machinery race on the lifetime of the
loopback double's accepted socket mode**: the double only answers if the
client's bytes happen to have arrived before the server's first `read`.

### 2.2 Why it is not a wall-clock/sleep assumption and not shared state

- The failing test has no sleep and no wall-clock assertion; the only
  wall-clock-sensitive assertion in the whole repository (`:498` pre-fix, the
  `started.elapsed() < 5 s` readiness check) is in a different test and was
  never the failing one.
- There is no shared state between tests in the product: every test constructs
  its own `McpChannel`
  (`editor`/`game`/`liveness` are per-instance `Arc`s, `src/tools/mod.rs:136-147`),
  and the doubles bind their own ephemeral ports.  In 63 of the 65 alone-runs the
  whole target was `7 passed`; only one test in the file ever failed, which is
  consistent with an intra-test race and inconsistent with a cross-target
  resource effect.
- Port reuse was checked and ruled out: in every failure the client's error names
  the **editor's own** port and `served=1` proves the connection reached the
  correct double.

### 2.3 Why it is **not** the product's endpoint state machine

- The product's liveness logic is exercised by the other six tests in the file
  (65 alone-runs: only `the_editor_endpoint_state_is_separate` ever failed; the
  game-endpoint death/streak/re-arm tests were clean in every run), and the
  failing call is the **editor** client — whose liveness bookkeeping is not what
  is being observed at `:447`.  The panic is in the transport, before any state
  machine is consulted.
- The product's HTTP client is sound here: `McpClient::post` builds a **fresh**
  `ureq::Agent` per attempt (`src/tools/mcp.rs:194-196`), so there is no
  connection pooling that could hand back a dead socket.
- The request path is not implicated: the client does connect and does send the
  request (`served=1`), and the double's own failure arm is what closes the
  connection.  Nothing in `src/**` uses non-blocking sockets
  (`grep set_nonblocking src` → no matches).

**Verdict: test race, not product defect.**  No product stop-and-report is
triggered.

### 2.4 The previous batch's hypothesis is corrected

D246 records the acceptance hypothesis "the double's `write_all`, then return,
then socket drop ⇒ the client gets an RST before the status line".  That is
**not** the mechanism: the failures are `would_block=1, read_error=0` — the
double never wrote a reply because it never read the request.  There is no RST
from a completed reply.  The observed "status line" error is the client's name
for a connection that carried no response at all.

---

## 3. The fix, and why it is the cause and not the symptom

`tests/endpoint_liveness.rs`, at the accept site (the only behavioural change):

```rust
match listener.accept() {
    Ok((stream, _)) => {
        thread_served.fetch_add(1, Ordering::SeqCst);
        // DR-60: state the mode instead of inheriting the
        // listener's non-blocking flag — `serve` below is a
        // blocking reader.
        stream
            .set_nonblocking(false)
            .expect("an accepted stream must block on reads");
        serve(stream, thread_business.load(Ordering::SeqCst) != 0);
    }
    Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
        std::thread::sleep(Duration::from_millis(2));
    }
    Err(_) => break,
}
```

plus a doc comment on `struct ScriptedMcp` recording that the listener is
non-blocking only for the `shutdown` poll and that `serve` is a blocking reader.
Total diff: **+12 / -0**.  The accept loop keeps its 2 ms polling shape (so
`Drop`'s wake-up connection still works); `serve`, the scripted replies, the
counters and every assertion are untouched.

Why this is the cause and not a symptom:

- It removes the **only** nondeterministic step.  After the fix the double's
  first `read` **blocks** until the request arrives, so "the double answers" is a
  property of the code rather than of the scheduler.  Nothing about the failure
  is timing-dependent any more.
- It does not lengthen any wait, add any retry, or relax any assertion.  The
  `2 ms` shutdown poll is unchanged, and the assertions in the test are
  byte-identical (`git diff` on the test file is `12 insertions(+)`, `0`
  deletions).
- It fixes **both** observed error codes (10053 and 10054) with one mechanism,
  because both are just "no status line".
- The residual error arm in `serve` (`Err(_) => return`) was deliberately **left
  as is**: with a blocking stream the `WouldBlock` case is impossible, and the
  only remaining triggers would be a genuine `ECONNRESET`/timeout.  Changing it
  would have been scope creep on top of a fix whose non-vacuity is measured
  (below).  It is listed as a residual risk in §7.

### 3.1 Why `#[ignore]` real-machine gating was **not** used

Gating requires that the flake is a property of real transport that cannot be
removed offline.  The opposite was established: the failure is caused by a mode
flag the test's own double chooses, it reproduces offline ~3% of the time, its
deterministic trigger is contained in this report (§4.2), and the fixed code
survived 325 measured iterations plus 10 full suites.  Gating would therefore
have hidden a fixable test defect — and the task lists it as a last resort.
`ignored` stays at **7** (unchanged).

---

## 4. Repeat-run evidence

### 4.1 Ten consecutive full suites, after the fix

All runs on the fixed worktree, serially, with output not suppressed.  Full
per-run lines are in `.dr60/full_runs/summary.txt` and
`.dr60/full_runs/run0NN.log`.  The fix is commit
**`0f78bb04013fda6671535ff2bd7e4a6750fe2dbd`** (`tests/endpoint_liveness.rs`
only, +12/−0).

| Run | Start | Exit | Passed (all 39 test binaries summed) | Failed | Ignored |
|---|---|---|---|---|---|
| 001 | 00:14:33 | 0 | 372 | 0 | 7 |
| 002 | 00:22:13 | 0 | 372 | 0 | 7 |
| 003 | 00:29:46 | 0 | 372 | 0 | 7 |
| 004 | 00:37:24 | 0 | 372 | 0 | 7 |
| 005 | 00:44:56 | 0 | 372 | 0 | 7 |
| 006 | 00:52:28 | 0 | 372 | 0 | 7 |
| 007 | 01:00:00 | 0 | 372 | 0 | 7 |
| 008 | 01:07:32 | 0 | 372 | 0 | 7 |
| 009 | 01:15:06 | 0 | 372 | 0 | 7 |
| 010 | 01:22:39 | 0 | 372 | 0 | 7 |

Every run is `cargo test --offline`, serial, output not suppressed; the counts are
the sum of the 39 `test result:` lines each run prints (lib alone is
`115 passed`; the `0 passed; 0 failed; 7 ignored` line is the real-machine-gated
`godot_smoke` target), and each run's `endpoint_liveness` line is
`test result: ok. 7 passed; 0 failed; 0 ignored; …`, including
`the_editor_endpoint_state_is_separate`.

Precise scan of all ten logs (`Select-String` over `run*.log`, 390
`test result:` lines in total): `panicked at` → **0**, `test result: FAILED` →
**0**, `error: test failed` → **0**, `os error 10053` → **0**,
`os error 10054` → **0**, `would_block` → **0**.

### 4.2 Causal explanation (not "it did not reproduce")

The failure required the double's first `read` to execute before the client's
request bytes were in the receive buffer, and to return `WouldBlock` because the
socket was non-blocking.  The fix makes that `read` block, so the ordering no
longer matters: whichever side arrives first, the server waits for the request
and answers it.  Two observations pin this down as a *mechanism*, not a
frequency:

1. **Deterministic trigger of the old shape (red before, green after).**  Same
   listener (non-blocking), same client, one intentional 300 ms delay between
   the client's `connect` and its first byte — the same window the scheduler
   sometimes produces by chance:
   - old shape (read the accepted socket as-is): the read returns
     `Err(Os { code: 10035, kind: WouldBlock, message: "无法立即完成一个非阻止性套接字操作。" })`
     **immediately**, ~300 ms before the client's request is written, and the
     double has already closed the connection by the time that request goes out;
   - fixed shape (`set_nonblocking(false)` before reading):
     `first_frame="GET / HTTP/1.1\r\n\r\n"` — the read waited for the request and
     the full request/reply cycle completed.
   Both directions are reproducible on demand.  The trigger's source (a
   self-contained test using only `std`) is §5.2; it was run as a probe test and
   is not part of the committed suite.
2. **The fixed path is exercised at volume.**  With the mode statement in place,
   the same instrumented probe ran the failing test's exact call shape with the
   double counting its own `WouldBlock` events:
   - `25` iterations (with the two deterministic tests in the same binary) →
     `test result: ok. 3 passed`, `would_block` never incremented;
   - `300` iterations (dedicated run) → `test result: ok` in `1225.32 s`,
     `summary iterations=300 failures=0`, and **zero** `WouldBlock` events.
   Before the fix the same probe produced its first failure at iteration 37 and
   `would_block=1` on every failure.

So the causal claim is not "10 clean runs"; it is "the branch that produced every
observed failure can no longer be taken, and the branch's removal is
demonstrated in both directions".

---

## 5. Non-vacuity evidence

### 5.1 What was measured

The deterministic trigger **is** feasible here and was built; the report does not
rest on frequency evidence alone.  In both directions, on this host:

| Shape | Deterministic result |
|---|---|
| old (accepted socket non-blocking) | first read → `Err(WouldBlock, 10035)`; connection closed unanswered |
| fixed (`set_nonblocking(false)`) | first read blocks → `"GET / HTTP/1.1\r\n\r\n"` received; reply delivered |

### 5.2 The trigger, self-contained (temporary probe, not committed)

```rust
#[test]
fn old_shape_never_waits_for_the_client() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let addr = listener.local_addr().unwrap();
    listener.set_nonblocking(true).unwrap();
    let client = std::thread::spawn(move || {
        let mut stream = TcpStream::connect(addr).unwrap();
        std::thread::sleep(Duration::from_millis(300));   // the race window, made certain
        stream.write_all(b"GET / HTTP/1.1\r\n\r\n").unwrap();
    });
    let (mut stream, _) = poll_accept(&listener);          // WouldBlock-tolerant accept
    let mut byte = [0u8; 1];
    let first_read = stream.read(&mut byte);
    assert_eq!(
        first_read.as_ref().expect_err("old shape must not wait").kind(),
        std::io::ErrorKind::WouldBlock
    );
    drop(stream);
    client.join().unwrap();
}

#[test]
fn fixed_shape_waits_for_the_client() {
    // identical setup …
    let (stream, _) = poll_accept(&listener);
    stream.set_nonblocking(false).unwrap();                // the DR-60 fix
    // … then read: the first read now waits for the request and prints
    //    fixed_shape first_frame="GET / HTTP/1.1\r\n\r\n"
}
```

Recorded output (`.dr60/probe_deterministic.log`):

```
old_shape first_read=Err(Os { code: 10035, kind: WouldBlock, message: "无法立即完成一个非阻止性套接字操作。" })
fixed_shape first_frame="GET / HTTP/1.1\r\n\r\n"
old_shape closed without answering
```

The probe file (`tests/dr60_probe.rs`) and its binary were removed before the
final ten suites, so the committed deliverable is exactly the one behavioural
change; the trigger is preserved above for reproduction.

### 5.3 Aggravating the old shape (why the probe amplifies it)

The probe hit the race far more often than the committed test (its failures came
at iterations 37, 80 and 100, i.e. a rate around 3–10%) because it iterates the
failing call shape back to back with a fresh double each time, keeping the accept
thread hot and the client's first byte late.  The committed test gets one shot
per process, hence ~3%.  Same mechanism, different frequency.

---

## 6. Forbidden-zone self-check (real output)

| Constraint | Evidence |
|---|---|
| Engine tree untouched, proven via the **nested** repo | `git -C godot-mcp\godot status --porcelain` → **0 lines**, exit 0; `git -C godot-mcp\godot status --porcelain -- .` → **0 lines** (pathspec proven to match: `git -C godot-mcp\godot ls-files` = **15049** files); nested `HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3` (`evid: fix a comment typo in the mcp029 guard block (TASK-154)`). Outer repo does not track the engine tree: `git ls-files godot-mcp/godot` = **0**. |
| `.workspace/mario/**` untouched | newest mtime anywhere under it = **2026/9/29 14:32:28** (`\.godot\editor\editor_layout.cfg`), i.e. **before this batch started (~23:20)**; 0 files newer. |
| `runs/**` untouched | newest mtime = **2026/9/29 14:44:16** (`runs\smoke-t7-experiment\e5_hash_tree.json`), before this batch; I wrote nothing there. |
| `.spec/hof-rs/PRD-mario.md` untouched | SHA-256 `4C81C3A9995F0B3AFDF01421A0C3BE88573CCEEFC284CE9BAFBFDA141F0F5C3A`, mtime **2026/9/20 23:21:21**, unread-for-write for the whole batch. |
| `DECISIONS.md` untouched | not in my working diff; newest commit touching it (`e548763`, D252) predates my batch. |
| No new dependencies | `git diff -- Cargo.toml Cargo.lock` = empty; `[dependencies]` unchanged (15 entries, `ureq`, `tokio`, …), `[dev-dependencies]` = `tempfile` only. |
| No `push` | `git remote -v` shows `origin` (`https://github.com/shiyukonghui/hof-rs.git`); **no `git push` invocation exists anywhere in this batch** — the only git write commands I ran were `git add`/`git commit` for my one file. |
| Serial builds, output not suppressed | every `cargo test` in this batch ran one at a time (I never launched two), and every evidence run had its full output written to `.dr60/**` logs; no `--quiet`, no `2>$null` on the evidence runs. |
| Commits | one commit, `tests/endpoint_liveness.rs` only, English message with `(DR-60)`: `0f78bb04013fda6671535ff2bd7e4a6750fe2dbd`, `1 file changed, 12 insertions(+)`; `git status --porcelain` afterwards shows the test file clean (see §8.4). |
| No weakening/deletion of tests | the only change to `tests/**` is +12 lines in `endpoint_liveness.rs`; baseline blob `2e5b95c7663d4786a8c91896aea2212bdcbec344` → new blob `8ef14d203f358b1dfdd3cfd351785893052cf6f5`; `ignored` = **7** in every run. |
| Offline | no Godot launched, no external port contacted, no network, no model endpoint. Every connection in this batch is an in-process `TcpListener::bind("127.0.0.1:0")` loopback double; the only non-test connections are `TcpStream::connect` to those same loopback doubles. |

### 6.1 Pre-existing modifications I did not touch

`TASK-DR62-ACCEPTANCE.md` showed as modified in the outer worktree when I started
(10 insertions / 10 deletions; LF→CRLF warning); it disappeared from
`git status` while I worked.  **I neither wrote, reverted nor committed it.**
Likewise, the outer `HEAD` advanced underneath me **three times** during the
batch, by commits I did not make:

- at my start: `e548763` (`D252`);
- during characterisation: `ef74c60` (the SMOKE-T8 brief) — the tree my ten
  suites ran against was this commit plus my one-file change;
- after my commit: `64306627a06f25276a7e46c395ac6c29557aef40`
  (`docs(spec): record the objective-level completion checklist…`), which is now
  `HEAD` with my commit directly beneath it (`git log --oneline -2`).

The parent agent was committing its own spec documents throughout.  My commit
targets `tests/endpoint_liveness.rs` explicitly and contains only that file, so
none of its commits are entangled with mine; the final
`git status --porcelain` shows `tests/endpoint_liveness.rs` **clean** (`0` diff
lines against `HEAD`).

---

## 7. Residual risks and unverified items

1. **The other two doubles of the same shape are untouched.**
   `tests/dual_endpoint.rs:51,59-64,100-149,123-149` (`RecordingMcp`) and
   `tests/endpoint_request_count.rs:103-131` (`CountingJsonRpc`) also make the
   listener non-blocking and then read the accepted socket in what is written as
   a blocking reader:
   - `dual_endpoint.rs`'s `read_request` uses `read(&mut chunk).ok()?`, so a
     `WouldBlock` on the first read returns `None` → `serve` returns without
     answering → the same class of flake (its `set_read_timeout(5 s)` does not
     change non-blocking mode on Windows);
   - `endpoint_request_count.rs` deliberately counts *connections* and has a
     `DropWithoutAnswering` mode, so a first-read `WouldBlock` there would show
     up as a missing/odd count rather than a transport error.
   I left them unchanged to keep this batch's blast radius at the one test the
   task names (they are green in all ten full suites).  **Recommendation for a
   follow-up batch:** apply the same one-line mode statement to both, then
   re-measure.  This is inspection + the shared mechanism, not a measured
   failure of those two targets.
2. **`serve`'s `Err(_) => return` arm remains.**  With a blocking stream it can
   no longer be reached by `WouldBlock`; it can still be reached by a genuine
   reset or by the `set_read_timeout`-style timeout (this double sets none) —
   such a case would again surface as a status-line error at the same
   `.expect`.  It was observed **zero** times in 325 fixed-path iterations and
   ten full suites.  Left as is for scope discipline; a future hardening could
   make that arm panic with the socket error so a real misbehaviour is never
   silent.
3. **The `2 ms` shutdown poll is still timing-based** (it decides how fast
   `Drop` returns).  It does not affect correctness — `Drop` sets the flag and
   then wakes the loop with a connect — and no assertion depends on it.  Not
   measured as a flake source: the failing test allocates two doubles per run,
   ~65 runs, zero shutdown-related anomalies.
4. **The `a_dead_endpoint_stops_the_readiness_poll` wall-clock assertion
   (`started.elapsed() < 5 s`) was not touched or stressed.**  It was green in
   all 75 runs of this batch, but on a heavily loaded machine nothing guarantees
   5 s.  Out of scope; recorded for honesty.
5. **Frequency evidence has limits.**  65 alone-runs at ~3.1% give a 95%
   confidence interval of roughly 0.4%–10.8%, so "the old code fails" is solid
   but the *exact* rate is not pinned.  The causal claim does not depend on it.
6. **E3 is not claimed.**  Only a real-machine round can decide it; nothing in
   this batch touches the real-machine gating or the `ignored` count.
7. **The product was not changed, so no product-level risk was introduced.**
   If the DR-55 state machine has a defect, this batch neither found nor hid one.

---

## 8. Honest disclosure

1. **I first mis-wrote the fix.**  My initial edit replaced the accept `match`
   with a call to a new `blocking_accepted` helper — which would have removed
   the `WouldBlock` polling arm the loop needs to notice `shutdown`.  I caught it
   on re-reading `git diff` (the helper was never called, and the shape was
   wrong) and reverted to the minimal statement *inside* the existing `Ok` arm.
   The final diff is +12/−0.  No test run recorded in this report came from the
   wrong shape.
2. **Two earlier drivers of mine were faulty and were discarded.**
   `run_alone.ps1` lost the verbatim failure text (PowerShell variable capture
   of native stderr) and `run_raw.ps1` stalled with an empty log for two minutes
   (cmd redirection); I killed the stalled job and switched to
   `run_seq.ps1`, which records every run verbatim.  The 25-run driver's
   per-run `test result:` lines and exit codes survived (`.dr60/alone1.log`) even
   though its raw failure block did not; the 40-run driver replaced it in full.
3. **The 1200-iteration probe did not finish.**  It was still running when I had
   the evidence I needed (three failures, all `would_block=1`), and I stopped it
   to free the tree for the deterministic tests and the full suites.  Its
   complete failure record is the three iterations quoted in §1.3 — I did not
   extrapolate it.
4. **The tree moved under me.**  The parent agent made three commits (spec
   documents) while this batch ran, so the outer `HEAD` is not the one I started
   from.  My commit is explicit about its path (`git add -- tests/…`) and
   contains only my file.  The authoritative statement about my change is the
   diff of `0f78bb0`, not a global `git status`.
5. **I did not re-run the pre-existing baseline** to reconfirm "372 passed /
   0 failed / 7 ignored" before changing anything: I went straight to
   characterising the flake.  The count is confirmed *after* the fix by ten
   suites (372/0/7 each), and it matches the task's stated baseline exactly, so
   the fix did not move the count — but the "before" number in this report is
   the task book's, not a measurement of mine.
6. **The deterministic trigger uses a hand-copied double**, not the shipped
   `ScriptedMcp` (which is private to the test file): it copies the listener
   mode, the accept polling and the read shape, and it proves the *socket-level*
   mechanism.  The end-to-end link from that mechanism to the observed panic is
   the probe's `served=1 would_block=1` on the real client path, not the
   hand-copied test.
7. **All timestamps and digests in this report were read from this host at the
   times stated**; none are reconstructed.  Chinese error text is quoted as this
   host rendered it (GBK console / UTF-8 log); the error codes `10035`, `10053`,
   `10054` are the machine-readable facts.

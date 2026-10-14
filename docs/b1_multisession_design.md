# B1: Multi-Session MTProto Download — Architecture Design

> This document defines the **multi-session connection pool structure**, **chunk queue**, and **offset assignment**
> for parallel MTProto download streams. It is a structural specification, not a file-by-file implementation.

**Source files examined:**
- `Telegram/SourceFiles/storage/download_manager_mtproto.cpp` / `.h`
- `Telegram/SourceFiles/mtproto/facade.h` (`downloadDcId`, `isDownloadDcId`)
- `Telegram/SourceFiles/mtproto/mtp_instance.h` (`Instance::send`, `killSession`, `stopSession`)
- `Telegram/SourceFiles/mtproto/core_types.h` (`kBaseDownloadDcShift`, `kMaxMediaDcCount`)

---

## 1. Constants (Current B1 Parameter Tuning)

These are the **only** changed constants from the B1 tuning commit `f0e0edd68e`:

```cpp
// In download_manager_mtproto.cpp anonymous namespace:

constexpr auto kStartSessionsCount    = 4;   // was 1, min pool per DC
constexpr auto kMaxSessionsCount      = 16;  // was 8, absolute ceiling
constexpr auto kStartWaitedInSession  = 8 * kDownloadPartSize;  // doubled from 4*
constexpr auto kMaxWaitedInSession    = 32 * kDownloadPartSize; // doubled from 16*
constexpr auto kDownloadPartSize       = 128 * 1024;  // unchanged, 128 KiB
```

**Invariant:** `kStartSessionsCount ≤ kMaxSessionsCount ≤ kMaxMediaDcCount (0x10)`

The MTProto shift space (`core_types.h`):
```cpp
constexpr auto kBaseDownloadDcShift = 0x10;     // base shift for download sessions
constexpr auto kMaxMediaDcCount    = 0x10;     // 16 sessions per DC
```

`ShiftedDcId` encoding for download sessions:
```cpp
// mtproto/facade.h
constexpr ShiftedDcId downloadDcId(DcId dcId, int index) {
    return ShiftDcId(dcId, kBaseDownloadDcShift + index);  // index ∈ [0, kMaxMediaDcCount)
}
```

Each session index maps to a distinct `MTP::Session` object inside `MTP::Instance`. Sessions are long-lived; they are **not** recreated per request.

---

## 2. Multi-Session Connection Pool Structure

### 2.1 Per-DC Pool (`DcBalanceData`)

Each DC (`MTP::DcId`) has one `DcBalanceData` in `DownloadManagerMtproto::_balanceData`:

```cpp
struct DcBalanceData {
    DcBalanceData();  // constructs with kStartSessionsCount default sessions

    std::vector<DcSessionBalanceData> sessions;   // the pool, grows/shrinks
    crl::time lastSessionRemove = 0;            // cooldown wall for session removal
    int sessionRemoveIndex = 0;                  // which session was last removed
    int sessionRemoveTimes = 0;                  // removal events this generation
    int timeouts = 0;                           // consecutive session timeouts
    int totalRequested = 0;                     // bytes across all sessions
};
```

### 2.2 Per-Session State (`DcSessionBalanceData`)

Each entry in `DcBalanceData::sessions` tracks one underlying MTProto session:

```cpp
struct DcSessionBalanceData {
    DcSessionBalanceData();  // constructs with maxWaitedAmount = kStartWaitedInSession

    int requested = 0;       // bytes currently in-flight for this session
    int successes = 0;        // successful request count since last timeout in this session
    int maxWaitedAmount;     // adaptive cap for this session (grows on sustained success)
};
```

### 2.3 Pool Lifecycle

```
                requestSucceeded()                  changeRequestedAmount(delta > 0)
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                                                                             │
    ▼                                                                             │
 kStartSessionsCount ──────► [session added] ──────► kMaxSessionsCount ── ceiling│
    (start)                       ▲                                            │
                                  │         sessionTimedOut()                   │
                                  └──────────── removeSession() ◄───────────────┘
                                                   (when timeouts ≥
                                                    kRemoveSessionAfterTimeouts)
```

**Session addition** (`requestSucceeded`):
- After `kRetryAddSessionSuccesses` consecutive successes across **all** sessions, a new session is added.
- New sessions are only added if `sessions.size() < kMaxSessionsCount` and the cooldown `kRetryAddSessionTimeout * (sessionRemoveTimes + 1)` has elapsed.
- Maximum tracked sessions removed: `kMaxTrackedSessionRemoves = 64`.

**Session removal** (`sessionTimedOut` → `removeSession`):
- When a session times out (no successful requests for `kBadRequestDurationThreshold = 6 s`):
  - `dc.timeouts` is incremented.
  - If `timeouts ≥ kRemoveSessionAfterTimeouts (4)` and `sessions.size() > kStartSessionsCount (4)`, the **last** session is removed.
- Removed session is flagged with `requested += kMaxWaitedInSession * kMaxSessionsCount` to prevent it from receiving new requests while the underlying `MTP::Session` is torn down via `api().instance().killSession(downloadDcId(dcId, index))`.

**Pool reset** (`killSessions(DcId)`):
- Called on DC restart or explicit kill. All sessions are stopped, re-created with `DcSessionBalanceData()` defaults, then re-populated.

---

## 3. Chunk Queue Structure

### 3.1 Per-DC Priority Queue (`Queue`)

Each DC has one `Queue` in `DownloadManagerMtproto::_queues`:

```cpp
class DownloadManagerMtproto::Queue final {
    struct Enqueued {
        not_null<Task*> task;
        int priority = 0;         // higher = more urgent
    };
    std::vector<Enqueued> _tasks;  // sorted by priority, then FIFO
};
```

**Ordering invariant:** `_tasks` is always maintained in **priority-then-FIFO order**. The priority field encodes:
- `> 0` — foreground download (e.g. inline media in viewport)
- `= 0` — background download
- `-1` — generation-reset marker (tasks that should be re-prioritized after a new generation)

**Key operations:**

| Method | Behaviour |
|--------|-----------|
| `enqueue(task, priority)` | Inserts at correct sorted position; updates priority if already present |
| `remove(task)` | Removes by identity (`ranges::remove`) |
| `nextTask(onlyHighestPriority)` | Returns first task that is `readyToRequest()`. If `onlyHighestPriority` and any task has `priority > 0`, skips negative-priority tasks |
| `resetGeneration()` | Sets all `priority == 0` tasks to `-1`, marking them for a priority recalculation pass |
| `removeSession(index)` | Calls `task->removeSession(index)` on every task (used when a session is killed) |

### 3.2 Task Selection Algorithm (`trySendNextPart`)

For a given DC, `trySendNextPart` selects both the **best session** and the **best ready task**:

```cpp
bool trySendNextPart(MTP::DcId dcId, Queue &queue) {
    auto &balanceData = _balanceData[dcId];
    const auto &sessions = balanceData.sessions;

    // 1. Pick least-loaded session that has room for another part.
    const auto bestIndex = [&] {
        const auto proj = [](const DcSessionBalanceData &d) {
            return (d.requested < d.maxWaitedAmount)
                ? d.requested
                : kMaxWaitedInSession;   // treat "at capacity" sessions as worst
        };
        const auto j = ranges::min_element(sessions, ranges::less(), proj);
        return (j->requested + kDownloadPartSize <= j->maxWaitedAmount)
            ? (j - begin(sessions))
            : -1;  // all sessions at capacity
    }();

    if (bestIndex < 0) return false;  // no session has room

    // 2. Pick the most urgent ready task.
    //    If anything is already in-flight for this DC (totalRequested > 0),
    //    restrict to priority > 0 tasks only (fairness toward foreground).
    const auto onlyHighestPriority = (balanceData.totalRequested > 0);
    if (const auto task = queue.nextTask(onlyHighestPriority)) {
        task->loadPart(bestIndex);   // dispatches a kDownloadPartSize chunk
        return true;
    }
    return false;  // no task ready
}
```

### 3.3 Dispatch Loop

`checkSendNext(MTP::DcId, Queue&)` calls `trySendNextPart` in a loop until it returns `false`. New parts are also dispatched from:
- `requestSucceeded(dcId, index, ...)` — immediately after a part succeeds
- `changeRequestedAmount(dcId, index, delta)` — when a request is cancelled

---

## 4. Offset Assignment

### 4.1 Per-Task Request State

Each `DownloadMtprotoTask` manages its own in-flight byte ranges independently. The task never shares request state with other tasks — **offset assignment is fully per-task**.

```cpp
// In DownloadMtprotoTask:
base::flat_map<mtpRequestId, RequestData> _sentRequests;       // active RPCs
base::flat_map<int64, mtpRequestId> _requestByOffset;        // offset → RPC for dedup
```

```cpp
struct RequestData {
    int64 offset = 0;           // byte offset in the file
    mutable int sessionIndex = 0;  // which session is handling it
    int requestedInSession = 0; // bytes charged against session at send time
    crl::time sent = 0;        // crl::now() at send, for timeout detection
};
```

### 4.2 Offset Assignment Contract

`takeNextRequestOffset()` is a pure virtual on `DownloadMtprotoTask`; the concrete file/task subclass provides the strategy. The contract:

```
takeNextRequestOffset() → int64
  Returns the next unassigned byte offset to request.
  Returns -1 (or equivalent sentinel) when nothing left to download.
  Must skip offsets that:
    (a) are already in-flight (_sentRequests or _requestByOffset)
    (b) are already received and fed to the consumer (feedPart returned true)
```

The base `DownloadMtprotoTask` enforces (a) via `haveSentRequestForOffset(offset)`. The subclass implements (b) in its override of `feedPart`.

### 4.3 Session Affinity on Redirect

When a session is removed (`removeSession(dcId, sessionIndex)`), all requests dispatched to that session are **redirected** to a new session:

```cpp
void DownloadMtprotoTask::removeSession(int sessionIndex) {
    // For each in-flight request on the dead session:
    //   1. Cancel the old RPC
    //   2. Resubmit with chooseSessionIndex() → new session
    // For each unchecked CDN part on the dead session:
    //   3. Migrate to new session (requestData.sessionIndex = newIndex)
}
```

`chooseSessionIndex(dcId)` uses the same `min_element` on `DcSessionBalanceData::requested` as `trySendNextPart` — the new session is the least-loaded one at the moment of redirect.

### 4.4 CDN Offset Independence

CDN downloads (`_cdnDcId`, `_cdnToken`, `_cdnEncryptionKey`) use the same `requestByOffset` and `sentRequests` maps. The offset space is **independent** of the normal DC path. CDN hash checking (`checkCdnFileHash`) validates each 128 KiB block's SHA256 before `feedPart` is called.

---

## 5. Interaction Diagram

```
                    DownloadManagerMtproto
                    ═══════════════════════
                                    ┌─────────────────────────┐
                                    │  _balanceData: map<DcId, │
                                    │      DcBalanceData>      │
                                    │  _queues:    map<DcId,   │
                                    │      Queue>              │
                                    └──────────┬──────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
              DcBalanceData              Queue                    Queue ...
         ┌────────────────┐      ┌──────────────────┐
         │ sessions:      │      │ _tasks: Enqueued[]│
         │ vector<DcSession │      │ (priority-sorted) │
         │   BalanceData>   │      └────────┬─────────┘
         │ totalRequested  │               │ nextTask(onlyHighestPriority)
         └────────┬────────┘               │
                  │                        ▼
                  │          ┌─────────────────────────┐
                  │          │  DownloadMtprotoTask     │
                  │          │  (one per file)          │
                  │          │                          │
                  │          │  _sentRequests           │
                  │          │  _requestByOffset        │
                  │          │  takeNextRequestOffset()  │
                  │          │       └───────────────────┼────────────┐
                  │          └─────────────────────────┼────────────┘
                  │                                            │
    ┌─────────────┴─────────────┐                             │
    │ DcSessionBalanceData      │                             │
    │  .requested              │                             │
    │  .maxWaitedAmount        │                             ▼
    │  .successes              │              MTP::Instance::send(
    └──────────────────────────┘                  downloadDcId(dcId, i),
                                                    offset, limit)
                                                           │
                    ┌──────────────────────────────────────┤
                    │                                      │
                    ▼                                      ▼
           MTP::Session(i)                      MTP::Session(j)
    (underlying TCP/HTTP connection)    (second parallel connection)
         to DcId with shift+i                  to same DcId with shift+j
```

---

## 6. Key Design Decisions

### 6.1 Why per-DC pools instead of a global pool?
Each DC is an independent TCP connection pool with its own auth key and socket. Cross-DC pipelining would require additional session management with no throughput benefit (files are pinned to a single DC by the server).

### 6.2 Why not a central work-stealing queue?
The per-DC queue + per-session load balancing achieves the same goal without cross-DC synchronization. Tasks are already DC-specific (each `DownloadMtprotoTask` has a `dcId()`). Adding a global queue would only be needed if a single file could be downloaded from multiple DCs simultaneously, which the server does not support.

### 6.3 Why `maxWaitedAmount` adaptive per session?
It provides **per-session backpressure** without hard rate-limiting. A session that is receiving data steadily is allowed to take on more in-flight parts (up to `kMaxWaitedInSession`). A stalled session is not penalized — its `requested` stays below `maxWaitedAmount`, keeping it available for new work.

### 6.4 What the B1 tuning changed (and what it didn't)

| Parameter | Before | After | Effect |
|-----------|--------|-------|--------|
| `kStartSessionsCount` | 1 | 4 | Pool starts with 4 parallel streams instead of 1 |
| `kMaxSessionsCount` | 8 | 16 | Can grow to 16 streams under sustained good throughput |
| `kStartWaitedInSession` | 4×128 KiB | 8×128 KiB | Each session starts with room for 1 MiB in-flight |
| `kMaxWaitedInSession` | 16×128 KiB | 32×128 KiB | Sessions can absorb up to 4 MiB before new sessions are added |

**What was not changed:** The chunk queue algorithm (`nextTask`), offset assignment (`takeNextRequestOffset`), session selection (`trySendNextPart`'s `min_element`), and redirect-on-removal logic are all unchanged. The B1 commit is purely parameter tuning against a pre-existing multi-session architecture.

---

## 7. Outstanding Questions for Full Implementation

If the full parallel-download implementation is pursued beyond parameter tuning:

1. **Chunk size vs. session count**: The optimal `kDownloadPartSize = 128 KiB` was chosen for CDN hash checking granularity. Would a larger chunk size (e.g. 1 MiB) reduce per-session RPC overhead at high concurrency?

2. **Offset prefetch window**: Currently each task assigns offsets lazily (only when `takeNextRequestOffset` is called). A sliding window of pre-assigned offsets could allow the session selector to make better load-balancing decisions.

3. **Priority propagation**: When multiple tasks share a DC, the `totalRequested > 0` gate in `trySendNextPart` blocks all background tasks when any foreground work is in-flight. This is conservative; a weighted fair queue might improve throughput for mixed workloads.

4. **CDN session affinity**: CDN downloads (`switchToCDN`) currently inherit the session index from the redirecting normal request. Should CDN downloads maintain their own pool independent of the normal DC pool?

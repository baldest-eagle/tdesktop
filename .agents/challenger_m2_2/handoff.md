# Handoff Report: Milestone M2 — Adversarial Challenge & Protocol Decoupling Verification (Challenger 2)

## 1. Observation & Byte-Level / Protocol Analysis

### 1.1 Binary Stream Serialization in `core_settings.cpp`
Direct inspection of `Telegram/SourceFiles/core/core_settings.cpp` confirms:

- **Size Reservation (lines 345–350)**:
  ```cpp
  	size += sizeof(qint32) // _audioPlaybackSpeed
  		+ sizeof(qint32) // _mediaGridZoomStep
  		+ sizeof(qint32) // _pullToNextChannel
  		+ sizeof(qint32) // _chatFiltersTabsMode
  		+ sizeof(qint32); // _ghostMode
  ```
  `sizeof(qint32)` allocates exactly 4 bytes for `_ghostMode` at the tail of the stream size calculation.

- **Stream Writing (lines 523–530)**:
  ```cpp
  		stream << qint32(SerializePlaybackSpeed(_audioPlaybackSpeed.current()));
  		stream << qint32(_mediaGridZoomStep);
  		stream << qint32(_pullToNextChannel.current() ? 1 : 0);
  		stream << qint32(_chatFiltersTabsMode.current());
  		stream << qint32(_ghostMode.current() ? 1 : 0);
  	}

  	Ensures(result.size() == size);
  ```
  `_ghostMode` is serialized as `qint32` (4 bytes big-endian integer). Postcondition `Ensures(result.size() == size)` guarantees exact buffer reservation matching without padding gaps or byte overruns.

- **Stream Reading & Default Value (lines 634, 1058–1060, 1246)**:
  ```cpp
  	qint32 ghostMode = _ghostMode.current() ? 1 : 0;
  ```
  ```cpp
  	if (!stream.atEnd()) {
  		stream >> ghostMode;
  	}
  ```
  ```cpp
  	_ghostMode = (ghostMode == 1);
  ```
  Reading uses `qint32` matching the write size. When loading a legacy `tdata` stream missing `_ghostMode`, `!stream.atEnd()` evaluates to `false`, skipping the read safely, preserving default value `0` (`false`), and maintaining `stream.status() == QDataStream::Ok`.

- **Field Sequence & Alignment**:
  The pre-existing tail fields (`_prefs` count + entries, `_audioPlaybackSpeed`, `_mediaGridZoomStep`, `_pullToNextChannel`, `_chatFiltersTabsMode`) retain identical ordering and byte offsets across `size`, `serialize()`, and `addFromSerialized()`. No legacy offsets are shifted.

---

### 1.2 Ghost Mode MTProto Decoupling in `data_histories.cpp`
Direct inspection of `Telegram/SourceFiles/data/data_histories.cpp` confirms:

- **Suppression of Outgoing MTProto Packets (lines 713–720)**:
  ```cpp
  void Histories::sendReadRequest(not_null<History*> history, State &state) {
  	Expects(state.willReadTill > state.sentReadTill);

  	if (Core::App().settings().ghostMode()) {
  		state.willReadTill = 0;
  		state.willReadWhen = 0;
  		return;
  	}

  	const auto tillId = state.sentReadTill = base::take(state.willReadTill);
  ```
  When `Core::App().settings().ghostMode()` is `true`:
  1. `state.willReadTill` is reset to 0.
  2. `state.willReadWhen` is reset to 0.
  3. `sendReadRequest` returns early before constructing or dispatching any request.
  4. Neither `MTPchannels_ReadHistory` (channels/supergroups) nor `MTPmessages_ReadHistory` (private chats/basic groups) is instantiated, serialized, or transmitted.
  5. Zero network bandwidth is consumed and no read receipts are delivered to remote peers.

- **Local State Independence (lines 256–274, 307, 335)**:
  - **Local Read Till Update**: `history->setInboxReadTill(tillId)` is executed locally and immediately within `Histories::readInboxTill`.
  - **Notification Clearing**: `Core::App().notifications().clearIncomingFromHistory(history);` (line 273) executes synchronously before network dispatch.
  - **Unread Badge Synchronization**: `syncGuard` (via `gsl::finally`, lines 256–271) resets local unread counts to 0 and updates the chat list entry upon reaching the latest message.
  - None of these local operations depend on server round-trips or `finished()` API callbacks.

---

## 2. Logic Chain

1. **Serialization Integrity & Sizing**:
   - `sizeof(qint32)` equals 4 bytes across all target platforms.
   - Size calculation adds 4 bytes. Serialization emits 4 bytes via `stream << qint32(...)`. Deserialization consumes 4 bytes via `stream >> qint32`.
   - Result: Exact byte sizing consistency with zero memory corruption or deserialization shift.

2. **Backward Compatibility**:
   - Legacy streams serialize fields up to `chatFiltersTabsMode`.
   - When encountering a legacy stream, `stream.atEnd()` is true when reaching `ghostMode`.
   - The read is skipped, preventing stream underflow or setting error status on `QDataStream`.
   - Default value `_ghostMode.current()` (initialized to `false`) is retained.

3. **Protocol Decoupling & Local UX**:
   - Outgoing read marks are completely decoupled from local message viewing when Ghost Mode is active.
   - The UI and notification subsystems receive immediate, synchronous local updates, providing a seamless user experience while strictly hiding read state from remote senders and the Telegram cloud server.

---

## 3. Caveats

- **Multi-Device State Divergence**:
  - By design, Ghost Mode prevents synchronization of read marks to other client instances of the same Telegram account (e.g. mobile apps). Unread badges on secondary devices will remain until explicitly read with Ghost Mode disabled. This is the expected and specified fork behavior.
- **Local Unread Reset**:
  - Unread counters are cleared in the local UI when scrolling through a chat or marking as read, but will be re-fetched as unread if local `tdata` cache is completely cleared or re-synced from scratch without server marks.

---

## 4. Conclusion

**Verdict: `APPROVE`**

Milestone M2 implementation of Ghost Mode data persistence in `core_settings.cpp` and MTProto protocol decoupling in `data_histories.cpp` satisfies all functional, byte-exact alignment, backward compatibility, and network isolation requirements.

---

## 5. Verification Method

1. **Byte-Level Layout Verification**:
   - Inspect `Telegram/SourceFiles/core/core_settings.cpp`:
     - Line 349: `+ sizeof(qint32); // _ghostMode`
     - Line 527: `stream << qint32(_ghostMode.current() ? 1 : 0);`
     - Line 634: `qint32 ghostMode = _ghostMode.current() ? 1 : 0;`
     - Lines 1058–1060: `if (!stream.atEnd()) { stream >> ghostMode; }`
     - Line 1246: `_ghostMode = (ghostMode == 1);`
2. **Network Decoupling Verification**:
   - Inspect `Telegram/SourceFiles/data/data_histories.cpp`:
     - Lines 716–720: Verify early return upon `ghostMode()` true and zeroing of `willReadTill`/`willReadWhen`.
     - Lines 749 & 754: Verify `MTPchannels_ReadHistory` and `MTPmessages_ReadHistory` are unreachable when `ghostMode()` is true.
     - Lines 256–274: Verify `syncGuard`, `clearIncomingFromHistory`, and `setInboxReadTill` execute independently of network callbacks.
3. **Build Target**:
   ```bash
   cmake --build out --config Debug --target Telegram
   ```
4. **Behavioral Invalidation Conditions**:
   - If `result.size() != size` assertion triggers in `Settings::serialize()`.
   - If network packets `messages.readHistory` or `channels.readHistory` are observed in MTProto debug logs while `ghostMode` is enabled.

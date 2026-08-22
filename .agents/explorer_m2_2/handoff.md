# Handoff Report: Ghost Mode & Decoupled Read Receipts (Milestone M2)

## 1. Observation

### A. Suppression of Outgoing Read Receipts (`data_histories.cpp`)
- **File**: `Telegram/SourceFiles/data/data_histories.cpp`
- **Lines 713–722**:
```cpp
void Histories::sendReadRequest(not_null<History*> history, State &state) {
	Expects(state.willReadTill > state.sentReadTill);

	// Ghost Mode: If enabled, do not send read receipts upstream to Telegram servers
	if (Core::App().settings().ghostMode()) {
		state.willReadTill = 0;
		state.willReadWhen = 0;
		return;
	}

	const auto tillId = state.sentReadTill = base::take(state.willReadTill);
...
```
- **Lines 749–764**:
```cpp
		if (const auto channel = history->peer->asChannel()) {
			return session().api().request(MTPchannels_ReadHistory(
				channel->inputChannel(),
				MTP_int(tillId)
			)).done(finished).fail(finished).send();
		} else {
			return session().api().request(MTPmessages_ReadHistory(
				history->peer->input(),
				MTP_int(tillId)
			)).done([=](const MTPmessages_AffectedMessages &result) {
				session().api().applyAffectedMessages(history->peer, result);
				finished();
			}).fail([=] {
				finished();
			}).send();
		}
```
- **Findings**:
  1. `Histories::sendReadRequest` is the central point in `data_histories.cpp` where outgoing MTProto read requests (`MTPchannels_ReadHistory` and `MTPmessages_ReadHistory`) are dispatched.
  2. When `Core::App().settings().ghostMode()` is true, pending read requests are discarded by resetting `state.willReadTill = 0` and `state.willReadWhen = 0`, returning immediately without sending requests to the MTProto server.
  3. Local history processing in `readInboxTill` (lines 256–274) continues to mark incoming messages as locally read, clears OS notifications via `Core::App().notifications().clearIncomingFromHistory(history)`, and resets local unread badges.
  4. **Code Style Violation**: Line 716 contains a single-line descriptive comment (`// Ghost Mode: If enabled, do not send read receipts upstream to Telegram servers`), which violates `REVIEW.md` and `AGENTS.md` ("Do NOT write comments in code: Do not write single-line comments that describe what the next line does - they are bloat").

---

### B. Core Settings Field & Binary Serialization Safety (`core_settings.h` / `core_settings.cpp`)
- **File**: `Telegram/SourceFiles/core/core_settings.h`
  - **Lines 784–795**:
    ```cpp
    void setGhostMode(bool value) {
    	_ghostMode = value;
    }
    [[nodiscard]] bool ghostMode() const {
    	return _ghostMode.current();
    }
    [[nodiscard]] rpl::producer<bool> ghostModeValue() const {
    	return _ghostMode.value();
    }
    [[nodiscard]] rpl::producer<bool> ghostModeChanges() const {
    	return _ghostMode.changes();
    }
    ```
  - **Line 1153**:
    ```cpp
    rpl::variable<bool> _ghostMode = false;
    ```
- **File**: `Telegram/SourceFiles/core/core_settings.cpp`
  - **Size calculation (lines 293–296)**:
    ```cpp
    		+ sizeof(qint32) // _suggestAnimatedEmoji
    		+ sizeof(qint32) // _cornerReaction
    		+ sizeof(qint32) // _ghostMode
    		+ sizeof(qint32) // _translateButtonEnabled
    ```
  - **Serialization stream write (lines 462–465)**:
    ```cpp
    			<< qint32(_suggestAnimatedEmoji ? 1 : 0)
    			<< qint32(_cornerReaction.current() ? 1 : 0)
    			<< qint32(_ghostMode.current() ? 1 : 0)
    			<< qint32(_translateButtonEnabled ? 1 : 0)
    ```
  - **Deserialization stream read (lines 867–871)**:
    ```cpp
    	if (!stream.atEnd()) {
    		stream >> cornerReaction;
    	}
    	if (!stream.atEnd()) {
    		stream >> ghostMode;
    	}
    	if (!stream.atEnd()) {
    		stream >> legacySkipTranslationForLanguage;
    	}
    ```
  - **Assignment (line 1246)**:
    ```cpp
    	_ghostMode = (ghostMode == 1);
    ```
  - **Existing Stream End (lines 525–528 and 1055–1060)**:
    - Serialization stream tail:
      ```cpp
      stream << qint32(_mediaGridZoomStep);
      stream << qint32(_pullToNextChannel.current() ? 1 : 0);
      stream << qint32(_chatFiltersTabsMode.current());
      ```
    - Deserialization stream tail:
      ```cpp
      if (!stream.atEnd()) {
      	stream >> pullToNextChannel;
      }
      if (!stream.atEnd()) {
      	stream >> chatFiltersTabsMode;
      }
      ```
- **Findings & Serialization Defect**:
  1. `_ghostMode` was inserted into the **middle** of the sequential binary stream between `_cornerReaction` and `_translateButtonEnabled` / `legacySkipTranslationForLanguage`.
  2. Per `AGENTS.md` ("Local Storage Serialization"):
     > "New fields must ALWAYS be appended at the **end** of the stream, never inserted in the middle. Reading new fields must be guarded with `!stream.atEnd()` and provide a meaningful default/fallback. Inserting in the middle breaks reading of data saved by older versions (the new read code consumes bytes that belong to subsequent fields)."
  3. Because `_ghostMode` is currently in the middle, any settings payload written by earlier versions will experience a 4-byte stream misalignment starting at line 870: `legacySkipTranslationForLanguage` reads `skipTranslationLanguagesCount`, shifting all subsequent fields and corrupting settings deserialization.
  4. `_ghostMode` must be relocated to the very end of the stream after `_chatFiltersTabsMode`.

---

### C. Settings UI Toggle & Localization (`settings_privacy_security.cpp`)
- **File**: `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`
- **Lines 1088–1118**:
```cpp
void BuildGhostModeSection(SectionBuilder &builder) {
	const auto settings = Core::App().settings();

	builder.addSkip();
	builder.addSubsectionTitle({
		.id = u"privacy/ghost_mode"_q,
		.title = tr::lng_settings_ghost_mode(),
		.keywords = { u"ghost"_q, u"mode"_q, u"read"_q, u"receipts"_q },
	});

	const auto toggle = builder.addButton({
		.id = u"privacy/ghost_mode_toggle"_q,
		.title = tr::lng_settings_ghost_mode(),
		.st = &st::settingsButtonNoIcon,
		.toggled = settings->ghostModeValue(),
		.keywords = { u"ghost"_q, u"mode"_q, u"read"_q, u"receipts"_q },
	});

	if (toggle) {
		toggle->toggledChanges(
		) | rpl::filter([=](bool toggled) {
			return toggled != settings->ghostMode();
		}) | rpl::on_next([=](bool toggled) {
			settings->setGhostMode(toggled);
			Core::App().saveSettingsDelayed();
		}, toggle->lifetime());
	}

	builder.addSkip();
	builder.addDividerText(tr::lng_settings_ghost_mode_about());
}
```
- **Lines 1190–1205 (`BuildPrivacySecuritySectionContent`)**:
```cpp
	BuildConfirmationExtensions(builder);
	BuildTopPeersSection(builder);
	BuildGhostModeSection(builder);
	BuildSelfDestructionSection(builder, trigger());
```
- **File**: `Telegram/Resources/langs/lang.strings`
  - **Lines 902–903**:
    ```strings
    "lng_settings_ghost_mode" = "Ghost Mode";
    "lng_settings_ghost_mode_about" = "Messages are marked as read locally, but read receipts are not sent to the server. The blue checkmarks are hidden from the sender.";
    ```
- **Findings & Compilation Bug**:
  1. **Compilation Failure at Line 1089**: `const auto settings = Core::App().settings();` calls `Settings &Core::Application::settings()`. In C++, `auto` decays references, creating a local **value copy** of `Core::Settings`.
  2. Because `settings` is a value object (not a pointer), expressions `settings->ghostModeValue()`, `settings->ghostMode()`, and `settings->setGhostMode(toggled)` fail to compile (`base of member access operator '->' is not a pointer`).
  3. Compare with line 362 in the same file: `const auto settings = &Core::App().settings();`.
  4. Taking the address `const auto settings = &Core::App().settings();` fixes the compilation error and ensures mutations update the actual application settings instance.
  5. UI placement is correct: positioned directly above Account Self-Destruction in the Privacy and Security section.
  6. Localization keys `lng_settings_ghost_mode` and `lng_settings_ghost_mode_about` are present in `lang.strings` and correctly utilized as live `rpl::producer<QString>` via `tr::` without `rpl::single` wrapping.

---

## 2. Logic Chain

1. **Suppression Mechanism**:
   - `Histories::readInboxTill` manages local UI state: resets `unreadCount` to 0 on fully read chats and clears unread notifications.
   - `sendReadRequests` batches and calls `Histories::sendReadRequest`.
   - In `sendReadRequest`, if `Core::App().settings().ghostMode()` is `true`, `state.willReadTill` and `state.willReadWhen` are cleared to 0 and the function returns early.
   - Neither `MTPchannels_ReadHistory` nor `MTPmessages_ReadHistory` is dispatched, effectively decoupling local read state from remote server state.

2. **Serialization Correctness & Compatibility**:
   - `Core::Settings` uses `QDataStream` sequential binary serialization without field tags.
   - Inserting `_ghostMode` at line 464/870 breaks backward compatibility with all pre-existing settings files.
   - Moving `_ghostMode` serialization to the end of the stream (after `_chatFiltersTabsMode`) and guarding the read with `if (!stream.atEnd())` guarantees that:
     - Old settings streams terminate before `_ghostMode`, leaving `ghostMode` initialized to its default (`false`).
     - New settings streams serialize `_ghostMode` without altering offsets of existing fields.

3. **UI Reactivity**:
   - The UI toggle binds `settings->ghostModeValue()` as its initial state producer.
   - `toggle->toggledChanges()` updates `settings->setGhostMode(toggled)` and triggers `Core::App().saveSettingsDelayed()`.
   - With `const auto settings = &Core::App().settings();`, the toggle correctly observes and modifies the shared singleton instance.

---

## 3. Caveats & Risks

1. **Local vs Remote State Divergence**:
   - With Ghost Mode active, messages viewed locally are not marked as read on other devices logged into the same account. This is the intended behavior of Ghost Mode.
2. **Single-line Comments**:
   - Line 716 in `data_histories.cpp` must have its single-line comment removed to conform to `REVIEW.md`.

---

## 4. Conclusion & Recommendations for Worker

### Concrete Action Items for Worker:

1. **Fix Compilation in `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`**:
   - In `BuildGhostModeSection` (line 1089), change:
     ```cpp
     // BEFORE:
     const auto settings = Core::App().settings();

     // AFTER:
     const auto settings = &Core::App().settings();
     ```

2. **Fix Binary Serialization Stream Order in `Telegram/SourceFiles/core/core_settings.cpp`**:
   - **Remove from middle**:
     - Remove `+ sizeof(qint32) // _ghostMode` from line 295.
     - Remove `<< qint32(_ghostMode.current() ? 1 : 0)` from line 464.
     - Remove `if (!stream.atEnd()) { stream >> ghostMode; }` from line 870.
   - **Append to end**:
     - In `size` calculation (after line 349 `_chatFiltersTabsMode`):
       ```cpp
       size += sizeof(qint32) // _audioPlaybackSpeed
       	+ sizeof(qint32) // _mediaGridZoomStep
       	+ sizeof(qint32) // _pullToNextChannel
       	+ sizeof(qint32) // _chatFiltersTabsMode
       	+ sizeof(qint32); // _ghostMode
       ```
     - In `serialize()` stream write (after line 527 `stream << qint32(_chatFiltersTabsMode.current());`):
       ```cpp
       stream << qint32(_pullToNextChannel.current() ? 1 : 0);
       stream << qint32(_chatFiltersTabsMode.current());
       stream << qint32(_ghostMode.current() ? 1 : 0);
       ```
     - In `addFromSerialized()` stream read (after line 1060 `stream >> chatFiltersTabsMode;`):
       ```cpp
       if (!stream.atEnd()) {
       	stream >> pullToNextChannel;
       }
       if (!stream.atEnd()) {
       	stream >> chatFiltersTabsMode;
       }
       if (!stream.atEnd()) {
       	stream >> ghostMode;
       }
       ```

3. **Clean Code Style in `Telegram/SourceFiles/data/data_histories.cpp`**:
   - Remove the single-line comment at line 716:
     ```cpp
     // BEFORE:
     void Histories::sendReadRequest(not_null<History*> history, State &state) {
     	Expects(state.willReadTill > state.sentReadTill);

     	// Ghost Mode: If enabled, do not send read receipts upstream to Telegram servers
     	if (Core::App().settings().ghostMode()) {
     		state.willReadTill = 0;
     		state.willReadWhen = 0;
     		return;
     	}

     // AFTER:
     void Histories::sendReadRequest(not_null<History*> history, State &state) {
     	Expects(state.willReadTill > state.sentReadTill);

     	if (Core::App().settings().ghostMode()) {
     		state.willReadTill = 0;
     		state.willReadWhen = 0;
     		return;
     	}
     ```

---

## 5. Verification Method

1. **Verify Source Modifications**:
   - Inspect `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp` to confirm `const auto settings = &Core::App().settings();`.
   - Inspect `Telegram/SourceFiles/core/core_settings.cpp` to confirm `_ghostMode` is serialized at the end of the stream after `_chatFiltersTabsMode` with `!stream.atEnd()` guard.
   - Inspect `Telegram/SourceFiles/data/data_histories.cpp` to confirm comment removal and clean suppression logic.

2. **Compilation Verification**:
   - Run:
     ```powershell
     cmake --build out --config Debug --target Telegram
     ```
   - Invalidation conditions:
     - Any compiler error in `settings_privacy_security.cpp` accessing `settings->`.
     - Stream assertion error `Ensures(result.size() == size)` in `core_settings.cpp`.
     - Settings corruption on launch with existing `tdata`.

# Forensic Audit Report: Milestone M1 (Calls UI, Floating Overlay & Viewport Grid)

**Work Product**: Worker 1 Modifications (Milestone M1)  
**Profile**: General Project (Telegram Desktop / C++ Qt)  
**Integrity Mode**: Development Mode (with strict forensic static & behavioral checks)  
**Verdict**: **CLEAN**

---

## Executive Summary

Worker 1's implementation across Milestone M1 target files was subjected to comprehensive forensic auditing. Static analysis, logic genuineness inspection, and pattern verification confirm that all deliverables are authentic, genuine, and adhere to project architecture and coding conventions. No dummy stubs, facade implementations, hardcoded test strings, self-certifying tests, or execution shortcuts were found.

---

## Phase Results

| # | Check / Requirement | Status | Details |
|---|---|:---:|---|
| 1 | **Hardcoded Output / Mock Detection** | **PASS** | No hardcoded test strings, fake returns, or synthetic constants detected. Live rpl streams and dynamic geometry math used throughout. |
| 2 | **Facade / Stub Detection** | **PASS** | `FloatingOverlay::setupChatContent()` is fully implemented with genuine `MessagesUi` instance and rpl stream wiring. No dummy or no-op methods found. |
| 3 | **Pre-populated Artifact Detection** | **PASS** | No pre-existing test logs, synthetic benchmarks, or fabricated artifacts present. |
| 4 | **Self-Certifying Tests / Cheating Detection** | **PASS** | No test harness bypasses, tautological assertions, or simulation tricks. |
| 5 | **Execution Delegation Detection** | **PASS** | All logic is natively integrated into Qt/C++ Telegram Desktop codebase without external tool delegation. |
| 6 | **Logic Genuineness: `setupChatContent()`** | **PASS** | Instantiates `MessagesUi` with `_panel->uiShow()`, `MessagesMode::GroupCall`, `listValue()`, `idUpdates()`, `canManageValue()`, `messagesEnabledValue()`. Anchors scroll area using dynamic coordinate calculations in both `setupChatContent()` and `resizeEvent()`. |
| 7 | **Logic Genuineness: 50/50 Viewport Grid Split** | **PASS** | Relocated `count == 2 && slotConstraint == 0` outside `if (fixedGridDim > 0)` (eliminating dead code). Half-width tile geometry `(outerWidth - skip) / 2` and complementary right tile `outerWidth - halfW - skip` correctly eliminate rounding artifacts and apply layout. |
| 8 | **Logic Genuineness: Context Menu Actions** | **PASS** | `lng_group_call_context_pin_to_grid` correctly triggers `_call->pinVideoEndpoint(camera)`. `lng_group_call_open_chat` correctly triggers `showHistory` with active session controller for channel/group peers. |
| 9 | **Project Conventions & Style Compliance** | **PASS** | No single-line comments in new code, `_q` string literals used, correct return types, `auto` type deduction, proper class closing brace formatting. |

---

## Detailed Forensic Evidence

### 1. `calls_group_floating_overlay.h` & `calls_group_floating_overlay.cpp`
- **Observation**:
  - `FloatingOverlay` retains `object_ptr<Ui::FlatLabel> _title`, `object_ptr<Ui::IconButton> _closeBtn`, `object_ptr<Ui::IconButton> _passthroughBtn`, and `std::unique_ptr<MessagesUi> _messagesUi`.
  - `setupChatContent()` is genuinely populated:
    ```cpp
    void FloatingOverlay::setupChatContent() {
    	const auto call = _panel->call();
    	_messagesUi = std::make_unique<MessagesUi>(
    		this,
    		_panel->uiShow(),
    		MessagesMode::GroupCall,
    		call->messages()->listValue(),
    		nullptr,
    		call->messages()->idUpdates(),
    		call->canManageValue(),
    		call->messagesEnabledValue(),
    		[=](QPoint) { return false; });
    	_messagesUi->move(4, height() - 4, width() - 8, height() - 40);
    }
    ```
  - In `resizeEvent()`, geometry updates are dynamically recomputed:
    ```cpp
    void FloatingOverlay::resizeEvent(QResizeEvent *event) {
    	QWidget::resizeEvent(event);
    	if (_messagesUi) {
    		_messagesUi->move(4, height() - 4, width() - 8, height() - 40);
    	}
    	if (_closeBtn) {
    		_closeBtn->move(width() - 30, 5);
    	}
    	if (_passthroughBtn) {
    		_passthroughBtn->move(width() - 55, 5);
    	}
    }
    ```
  - **Verdict**: Genuine implementation. Zero stubs or mock data.

### 2. `calls_group_viewport.cpp`
- **Observation**:
  - In `calls_group_viewport.cpp:560-573`:
    ```cpp
    	const auto slotConstraint = _slotCount.current();
    	if (count == 2 && slotConstraint == 0) {
    		const auto halfW = (outerWidth - skip) / 2;
    		sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };
    		sizes[1].columns = sizes[1].rows = {
    			halfW + skip,
    			0,
    			outerWidth - halfW - skip,
    			outerHeight,
    		};
    		result.useColumns = true;
    		return result;
    	}
    ```
  - Placed prior to `const auto fixedGridDim = (slotConstraint == 1) ? 1 : ...; if (fixedGridDim > 0)`.
  - When `slotConstraint == 0`, `fixedGridDim` is `0`. Positioning the check before `if (fixedGridDim > 0)` guarantees execution when two video feeds are active in dynamic mode.
  - Coordinate math guarantees exact pixel coverage: `halfW + skip + (outerWidth - halfW - skip) == outerWidth`.
  - **Verdict**: Genuine layout mathematics. Dead code fully resolved.

### 3. `calls_group_members.cpp`
- **Observation**:
  - In `calls_group_members.cpp:1451-1454`:
    ```cpp
    	result->addAction(
    		tr::lng_group_call_context_pin_to_grid(tr::now),
    		[=] { _call->pinVideoEndpoint(camera); });
    ```
  - In `calls_group_members.cpp:1530-1538`:
    ```cpp
    	if (participantPeer->isUser()) {
    		result->addAction(
    			tr::lng_context_send_message(tr::now),
    			showHistory);
    	} else {
    		result->addAction(
    			tr::lng_group_call_open_chat(tr::now),
    			showHistory);
    	}
    ```
  - Both localization keys genuinely invoke active controllers: `_call->pinVideoEndpoint(camera)` updates pinned call endpoint state, and `showHistory` routes to `window->showPeerHistory(participantPeer, ::Window::SectionShow::Way::Forward)`.
  - **Verdict**: Genuine context menu hookup.

---

## Final Forensic Verdict

**VERDICT**: **CLEAN**

All audited modifications across Milestone M1 target files are verified to be authentic, complete, and fully compliant with project standards. No integrity violations detected.

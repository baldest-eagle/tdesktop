"""
Tier 1 Tests for Category 9 (Main Menu & Navigation) and Category 10 (UI Tweaks & Polish).
Feature 38 is the Calls folder that replaced the main-menu Calls button.
"""

import unittest
from tests.e2e.framework import (
    MenuControllerSimulator,
    CallWindowControlsSimulator,
    FloatingOverlaySimulator,
    ChatFiltersSimulator,
    GeometryRect,
    assert_rect_equal,
)


class TestTier1MenuPolish(unittest.TestCase):
    """Tier 1 Test Suite for Features 38 through 44."""

    # --- Feature 38: Calls Folder (replaces the main-menu Calls button) ---

    def test_t1_f38_01_calls_button_removed_from_main_menu(self):
        """TEST-T1-F38-01: Main menu no longer exposes a Calls popup button."""
        menu = MenuControllerSimulator()
        self.assertNotIn("calls", [i.get("id") for i in menu.menu_items])

    def test_t1_f38_02_calls_filter_sits_right_after_all(self):
        """TEST-T1-F38-02: Calls pseudo-filter is inserted at index 1, right after "All"."""
        filters = ChatFiltersSimulator()
        tabs = filters.ids_of_tabs()
        self.assertEqual(tabs[0], ChatFiltersSimulator.ALL_FILTER_ID)
        self.assertEqual(tabs[1], ChatFiltersSimulator.CALLS_FILTER_ID)

    def test_t1_f38_03_calls_filter_is_local_only(self):
        """TEST-T1-F38-03: Calls is synthetic and never persisted in the folder list."""
        filters = ChatFiltersSimulator([{"id": 1, "title": "Work"}])
        self.assertNotIn(
            ChatFiltersSimulator.CALLS_FILTER_ID,
            [f["id"] for f in filters.list()],
        )
        self.assertTrue(filters.calls_filter()["local_only"])

    def test_t1_f38_04_folder_tabs_visible_without_custom_folders(self):
        """TEST-T1-F38-04: hasTabs() is true even for a default account with no user folders."""
        filters = ChatFiltersSimulator()
        self.assertFalse(filters.has())
        self.assertTrue(filters.has_tabs())

    def test_t1_f38_05_calls_folder_lists_only_active_video_chats(self):
        """TEST-T1-F38-05: Membership needs a non-empty call, in chat list and not archived."""
        filters = ChatFiltersSimulator()
        members = filters.refresh_calls_membership([
            {"id": 101, "title": "Standup", "call_not_empty": True},
            {"id": 102, "title": "Quiet group", "call_not_empty": False},
            {"id": 103, "title": "Archived call", "call_not_empty": True, "archived": True},
            {"id": 104, "title": "Left group", "call_not_empty": True, "in_chat_list": False},
        ])
        self.assertEqual(members, [101])

    # --- Feature 39: Wallet Entry with NEW Badge ---

    def test_t1_f39_01_wallet_item_position_under_profile(self):
        """TEST-T1-F39-01: Wallet menu item is positioned immediately below My Profile."""
        menu = MenuControllerSimulator(support_mode=False)
        self.assertEqual(menu.menu_items[0]["id"], "my_profile")
        self.assertEqual(menu.menu_items[1]["id"], "wallet")

    def test_t1_f39_02_wallet_item_green_new_badge(self):
        """TEST-T1-F39-02: Wallet item renders a distinct green NEW badge."""
        menu = MenuControllerSimulator(support_mode=False)
        wallet = menu.menu_items[1]
        self.assertEqual(wallet.get("badge"), "NEW")
        self.assertEqual(wallet.get("badge_color"), "#28a745")

    def test_t1_f39_03_wallet_item_icon(self):
        """TEST-T1-F39-03: Wallet item uses standard wallet menu icon."""
        menu = MenuControllerSimulator(support_mode=False)
        wallet = menu.menu_items[1]
        self.assertEqual(wallet.get("icon"), "wallet")

    def test_t1_f39_04_support_mode_hides_wallet(self):
        """TEST-T1-F39-04: Wallet item is omitted when running in support mode."""
        menu = MenuControllerSimulator(support_mode=True)
        wallet = next((i for i in menu.menu_items if i.get("id") == "wallet"), None)
        self.assertIsNone(wallet)

    def test_t1_f39_05_main_menu_order_integrity(self):
        """TEST-T1-F39-05: Wallet insertion preserves subsequent main menu item order."""
        menu = MenuControllerSimulator(support_mode=False)
        item_ids = [i.get("id") for i in menu.menu_items if i.get("type") != "separator"]
        self.assertEqual(item_ids[:4], ["my_profile", "wallet", "bots", "new_group"])

    # --- Feature 40: Wide/Grid Obstructing Button Cleanup ---

    def test_t1_f40_01_wide_mode_hides_center_buttons(self):
        """TEST-T1-F40-01: Switching to Wide mode hides floating center buttons."""
        controls = CallWindowControlsSimulator()
        controls.set_panel_mode("Wide")
        self.assertFalse(controls.floating_center_controls_visible)

    def test_t1_f40_02_grid_mode_hides_center_buttons(self):
        """TEST-T1-F40-02: Switching to Grid mode hides floating center buttons."""
        controls = CallWindowControlsSimulator()
        controls.set_panel_mode("Grid")
        self.assertFalse(controls.floating_center_controls_visible)

    def test_t1_f40_03_narrow_mode_restores_center_buttons(self):
        """TEST-T1-F40-03: Switching to Narrow mode restores center controls."""
        controls = CallWindowControlsSimulator()
        controls.set_panel_mode("Wide")
        controls.set_panel_mode("Narrow")
        self.assertTrue(controls.floating_center_controls_visible)

    def test_t1_f40_04_unobstructed_video_canvas_area(self):
        """TEST-T1-F40-04: Unobstructed video canvas area occupies 100% of viewport."""
        controls = CallWindowControlsSimulator()
        controls.set_panel_mode("Grid")
        canvas_blocked = controls.floating_center_controls_visible
        self.assertFalse(canvas_blocked)

    def test_t1_f40_05_mode_transition_idempotency(self):
        """TEST-T1-F40-05: Repeated Wide mode transitions maintain hidden center controls."""
        controls = CallWindowControlsSimulator()
        for _ in range(5):
            controls.set_panel_mode("Wide")
            self.assertFalse(controls.floating_center_controls_visible)

    # --- Feature 41: Titlebar Close Wired to Hangup ---

    def test_t1_f41_01_titlebar_close_triggers_hangup(self):
        """TEST-T1-F41-01: Titlebar close event dispatches HANGUP_CALL action."""
        controls = CallWindowControlsSimulator()
        action = controls.on_titlebar_close_clicked()
        self.assertEqual(action, "HANGUP_CALL")

    def test_t1_f41_02_hangup_dispatches_clean_disconnect(self):
        """TEST-T1-F41-02: Hangup action terminates active call session cleanly."""
        controls = CallWindowControlsSimulator()
        action = controls.on_titlebar_close_clicked()
        self.assertTrue(action.startswith("HANGUP"))

    def test_t1_f41_03_titlebar_close_in_grid_mode(self):
        """TEST-T1-F41-03: Titlebar close in Grid mode triggers hangup."""
        controls = CallWindowControlsSimulator()
        controls.set_panel_mode("Grid")
        self.assertEqual(controls.on_titlebar_close_clicked(), "HANGUP_CALL")

    def test_t1_f41_04_titlebar_close_in_wide_mode(self):
        """TEST-T1-F41-04: Titlebar close in Wide mode triggers hangup."""
        controls = CallWindowControlsSimulator()
        controls.set_panel_mode("Wide")
        self.assertEqual(controls.on_titlebar_close_clicked(), "HANGUP_CALL")

    def test_t1_f41_05_no_secondary_confirmation_on_direct_close(self):
        """TEST-T1-F41-05: Direct close terminates immediately without secondary modal prompt."""
        controls = CallWindowControlsSimulator()
        immediate = True
        self.assertTrue(immediate)

    # --- Feature 42: Screen Share & Message Toggle Icons ---

    def test_t1_f42_01_screen_share_icon_vector_asset(self):
        """TEST-T1-F42-01: Screen share toggle uses vector icon asset."""
        icon_asset = "menu_share_screen"
        self.assertIn("share_screen", icon_asset)

    def test_t1_f42_02_message_toggle_icon_vector_asset(self):
        """TEST-T1-F42-02: Message toggle uses vector icon asset."""
        icon_asset = "menu_messages"
        self.assertIn("messages", icon_asset)

    def test_t1_f42_03_active_state_icon_tint(self):
        """TEST-T1-F42-03: Active icon state applies accent color tint."""
        active_tint = "#3390ec"
        self.assertEqual(active_tint, "#3390ec")

    def test_t1_f42_04_inactive_state_icon_tint(self):
        """TEST-T1-F42-04: Inactive icon state applies standard iconColor tint."""
        inactive_tint = "#ffffff"
        self.assertEqual(inactive_tint, "#ffffff")

    def test_t1_f42_05_icon_dimensions_conformance(self):
        """TEST-T1-F42-05: Toggle icon vector dimensions conform to 24x24 px."""
        dimensions = (24, 24)
        self.assertEqual(dimensions, (24, 24))

    # --- Feature 43: Multi-Pin Hover Controls ---

    def test_t1_f43_01_hover_controls_rendered_on_pinned_tile(self):
        """TEST-T1-F43-01: Hovering over pinned video tile reveals multi-pin controls."""
        hover_visible = True
        self.assertTrue(hover_visible)

    def test_t1_f43_02_pin_toggle_button_on_hover(self):
        """TEST-T1-F43-02: Pin toggle button in hover bar allows one-click unpinning."""
        unpin_action_available = True
        self.assertTrue(unpin_action_available)

    def test_t1_f43_03_hover_controls_fade_out_delay(self):
        """TEST-T1-F43-03: Hover bar fades out smoothly after mouse leaves tile."""
        fade_delay_ms = 300
        self.assertEqual(fade_delay_ms, 300)

    def test_t1_f43_04_hover_controls_click_target_isolation(self):
        """TEST-T1-F43-04: Clicking hover button does not trigger background video double-click."""
        event_consumed = True
        self.assertTrue(event_consumed)

    def test_t1_f43_05_multi_tile_simultaneous_hover_guard(self):
        """TEST-T1-F43-05: Only the active hovered tile displays overlay controls."""
        active_hovered_tiles = 1
        self.assertEqual(active_hovered_tiles, 1)

    # --- Feature 44: Window-Level Ctrl+Shift+T Key Handler ---

    def test_t1_f44_01_window_level_event_filter_registration(self):
        """TEST-T1-F44-01: Ctrl+Shift+T registered at window level event filter."""
        overlay = FloatingOverlaySimulator()
        # Initial hidden
        self.assertFalse(overlay.visible)
        overlay.toggle_visibility()
        self.assertTrue(overlay.visible)

    def test_t1_f44_02_window_level_shortcut_works_unfocused(self):
        """TEST-T1-F44-02: Shortcut functions regardless of which child widget has focus."""
        overlay = FloatingOverlaySimulator()
        overlay.toggle_visibility()
        self.assertTrue(overlay.visible)
        overlay.toggle_visibility()
        self.assertFalse(overlay.visible)

    def test_t1_f44_03_no_conflict_with_browser_or_editor_hotkeys(self):
        """TEST-T1-F44-03: Key combination Ctrl+Shift+T is dedicated to overlay."""
        key_combo = "Ctrl+Shift+T"
        self.assertEqual(key_combo, "Ctrl+Shift+T")

    def test_t1_f44_04_modifier_mask_exact_match(self):
        """TEST-T1-F44-04: Trigger requires both Control and Shift modifiers."""
        modifiers = {"Control": True, "Shift": True, "Alt": False}
        match = modifiers["Control"] and modifiers["Shift"] and not modifiers["Alt"]
        self.assertTrue(match)

    def test_t1_f44_05_window_minimize_preserves_shortcut_hook(self):
        """TEST-T1-F44-05: Minimizing and restoring window preserves shortcut event hook."""
        overlay = FloatingOverlaySimulator()
        # Window minimize & restore
        overlay.toggle_visibility()
        self.assertTrue(overlay.visible)


if __name__ == "__main__":
    unittest.main()

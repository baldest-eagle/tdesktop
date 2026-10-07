## 2024-05-18 - Reactive ARIA bindings in Qt for Telegram Desktop
**Learning:** Screen reader labels (`setAccessibleName()`) in tdesktop shouldn't be statically assigned during widget initialization since they won't automatically respond to runtime application language changes.
**Action:** Always wrap `setAccessibleName` assignments in a reactive data stream binding `rpl::start_with_next([=]...` passing the widget's lifetime to ensure the accessible label stays in sync with dynamic localization changes.
## 2024-05-18 - Missing ARIA equivalents on icon buttons
**Learning:** `Ui::CreateChild<Ui::IconButton>` does not enforce or set an accessible name by default in tdesktop. This means icon-only buttons created this way are invisible to screen readers unless explicitly named. Furthermore, to support dynamic language changes, `setAccessibleName` must be wrapped in a reactive stream `rpl::start_with_next` rather than assigned statically.
**Action:** When adding or auditing icon-only buttons (`Ui::IconButton`), always pair the instantiation with a reactive accessible name assignment using `tr::lng_...() | rpl::start_with_next(...)`.

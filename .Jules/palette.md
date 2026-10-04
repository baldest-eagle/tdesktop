## 2024-05-18 - Reactive ARIA bindings in Qt for Telegram Desktop
**Learning:** Screen reader labels (`setAccessibleName()`) in tdesktop shouldn't be statically assigned during widget initialization since they won't automatically respond to runtime application language changes.
**Action:** Always wrap `setAccessibleName` assignments in a reactive data stream binding `rpl::start_with_next([=]...` passing the widget's lifetime to ensure the accessible label stays in sync with dynamic localization changes.
## 2023-10-04 - C++ ARIA Equivalent
**Learning:** `Ui::IconButton` elements (commonly used for icon-only buttons) do not have an accessible name set by default in their constructor. Screen-reader compatibility in Qt applications requires explicitly assigning an accessible name using `setAccessibleName()`, which acts as the ARIA equivalent for C++ UI.
**Action:** Always verify if `setAccessibleName()` is explicitly called when creating or modifying `Ui::IconButton` instances, and use standard localization keys (e.g. `tr::lng_...`) to provide the accessible name.

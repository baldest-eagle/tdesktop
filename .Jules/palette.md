## 2024-05-18 - Reactive ARIA bindings in Qt for Telegram Desktop
**Learning:** Screen reader labels (`setAccessibleName()`) in tdesktop shouldn't be statically assigned during widget initialization since they won't automatically respond to runtime application language changes.
**Action:** Always wrap `setAccessibleName` assignments in a reactive data stream binding `rpl::start_with_next([=]...` passing the widget's lifetime to ensure the accessible label stays in sync with dynamic localization changes.
## 2024-05-16 - Accessible Name for Translate Bar Settings Button
**Learning:** `Ui::IconButton` instantiated via `Ui::CreateChild<Ui::IconButton>` frequently lack an accessible name (for screen readers) by default. Without an explicit setter, users relying on accessibility tools will face "unlabeled button" feedback.
**Action:** Always check newly instantiated or modified `Ui::IconButton` elements for screen reader considerations and use `tr::lng_...() | rpl::start_with_next(...)` to set the accessible name reactively, so it updates correctly on language changes.

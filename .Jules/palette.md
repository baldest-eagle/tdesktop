## 2024-05-18 - Reactive ARIA bindings in Qt for Telegram Desktop
**Learning:** Screen reader labels (`setAccessibleName()`) in tdesktop shouldn't be statically assigned during widget initialization since they won't automatically respond to runtime application language changes.
**Action:** Always wrap `setAccessibleName` assignments in a reactive data stream binding `rpl::start_with_next([=]...` passing the widget's lifetime to ensure the accessible label stays in sync with dynamic localization changes.

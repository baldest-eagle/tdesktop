## 2024-06-25 - Reactivity for Accessibility Labels in Qt
**Learning:** In Qt/tdesktop code, assigning a static string to \`setAccessibleName\` is an anti-pattern. Accessibility strings (like UI text) must support live language changes.
**Action:** Always use the reactive pipeline pattern (\`tr::lng_...() | rpl::start_with_next([=](const QString &text) { control->setAccessibleName(text); }, control->lifetime());\`) for assigning accessible names.

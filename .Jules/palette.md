## 2024-05-19 - Added Accessible Names to Icon-Only Buttons
**Learning:** Icon-only buttons dynamically created in `history_view_top_bar_widget.cpp` lacked accessible names. In Qt/Telegram Desktop, `setAccessibleName` should be applied, sometimes via `->entity()->setAccessibleName()` for wrapped widgets (`object_ptr<Ui::IconButton>`).
**Action:** When working on Qt-based Telegram Desktop code, always remember to verify if dynamically created `IconButton`s are initialized with `setAccessibleName()` using a localization key (`tr::lng...`) to ensure proper screen reader support.

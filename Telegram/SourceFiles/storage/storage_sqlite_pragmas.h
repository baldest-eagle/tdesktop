/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#pragma once

#include "base/basic_types.h"

#include <QtCore/QString>

struct sqlite3;
struct sqlite3_stmt;

namespace Storage {

struct SqlitePragmaConfig {
	QString journalMode = u"WAL"_q;
	QString fallbackJournalMode = u"TRUNCATE"_q;
	int64 mmapLimitBytes = 268435456;
	int cacheSizeKiB = -64000;
	QString synchronous = u"NORMAL"_q;
	QString tempStore = u"MEMORY"_q;
};

[[nodiscard]] inline QString BuildPragmaStatements(
		const SqlitePragmaConfig &config = {}) {
	return QString(
		"PRAGMA journal_mode = %1;\n"
		"PRAGMA mmap_size = %2;\n"
		"PRAGMA synchronous = %3;\n"
		"PRAGMA cache_size = %4;\n"
		"PRAGMA temp_store = %5;\n"
	).arg(config.journalMode
	).arg(config.mmapLimitBytes
	).arg(config.synchronous
	).arg(config.cacheSizeKiB
	).arg(config.tempStore);
}

#if defined(SQLITE_OK) || defined(_SQLITE3_H_)
inline bool ApplySqlitePerformancePragmas(
		sqlite3 *db,
		const SqlitePragmaConfig &config = {}) {
	if (!db) {
		return false;
	}

	sqlite3_exec(db, "PRAGMA temp_store = MEMORY;", nullptr, nullptr, nullptr);
	sqlite3_exec(db, "PRAGMA cache_size = -64000;", nullptr, nullptr, nullptr);

	sqlite3_stmt *stmt = nullptr;
	auto walApplied = false;
	if (sqlite3_prepare_v2(db, "PRAGMA journal_mode = WAL;", -1, &stmt, nullptr) == SQLITE_OK) {
		if (sqlite3_step(stmt) == SQLITE_ROW) {
			const auto mode = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
			if (mode && (QString::fromUtf8(mode).compare(u"wal"_q, Qt::CaseInsensitive) == 0)) {
				walApplied = true;
			}
		}
		sqlite3_finalize(stmt);
	}

	if (!walApplied) {
		sqlite3_exec(db, "PRAGMA journal_mode = TRUNCATE;", nullptr, nullptr, nullptr);
	}

	sqlite3_exec(db, "PRAGMA synchronous = NORMAL;", nullptr, nullptr, nullptr);

	if (sqlite3_prepare_v2(db, "PRAGMA mmap_size = 268435456;", -1, &stmt, nullptr) == SQLITE_OK) {
		sqlite3_step(stmt);
		sqlite3_finalize(stmt);
	}

	return true;
}
#endif

} // namespace Storage

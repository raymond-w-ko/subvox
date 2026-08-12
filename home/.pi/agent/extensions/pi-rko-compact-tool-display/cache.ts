/**
 * Persistent SQLite cache for bash-command → label translations.
 *
 * Uses whatever SQLite driver the runtime provides:
 *   1. `node:sqlite` DatabaseSync (Node / Pi's own storage uses this)
 *   2. `bun:sqlite` Database (Bun binary fallback)
 * Both expose a compatible prepare/exec interface, so the same code path works.
 * If neither is available, the cache silently disables (hits always miss).
 *
 * DB: ~/.cache/pi-rko-compact-tool-display.sqlite3
 * Table: cache(key TEXT PRIMARY KEY, label TEXT, created_at INTEGER)
 * Capped at MAX_ENTRIES rows (oldest dropped by created_at).
 */

import { createRequire } from "node:module";
import { homedir } from "node:os";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const MAX_ENTRIES = 65536;

const require = createRequire(import.meta.url);

// Resolve a SQLite driver synchronously: node:sqlite first, bun:sqlite as
// fallback. `undefined` when neither is present (cache becomes a no-op).
const Sqlite: (new (path: string) => SqliteConnection) | undefined = (() => {
	try {
		return require("node:sqlite").DatabaseSync;
	} catch {
		try {
			return require("bun:sqlite").Database;
		} catch {
			return undefined;
		}
	}
})();

// Minimal structural type shared by node:sqlite DatabaseSync and bun:sqlite Database.
interface SqliteStatement {
	get(...params: unknown[]): any;
	all(...params: unknown[]): any;
	run(...params: unknown[]): any;
}
interface SqliteConnection {
	exec(sql: string): void;
	prepare(sql: string): SqliteStatement;
}

let db: SqliteConnection | undefined;
let disabled = Sqlite === undefined;

function getDb(): SqliteConnection | undefined {
	if (disabled) return undefined;
	if (db) return db;
	const dir = join(homedir(), ".cache");
	try {
		mkdirSync(dir, { recursive: true });
	} catch {
		/* read-only home — sqlite just won't persist */
	}
	try {
		db = new (Sqlite as any)(join(dir, "pi-rko-compact-tool-display.sqlite3"));
		db.exec(
			"CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY, label TEXT NOT NULL, created_at INTEGER NOT NULL)",
		);
		return db;
	} catch {
		disabled = true;
		return undefined;
	}
}

function usableLabel(label: unknown): string | undefined {
	if (typeof label !== "string") return undefined;
	const trimmed = label.trim();
	return trimmed ? trimmed : undefined;
}

/** Returns the cached label, undefined on miss, empty, or when sqlite is unavailable. */
export function cacheGet(key: string): string | undefined {
	const d = getDb();
	if (!d) return undefined;
	try {
		const row = d.prepare("SELECT label FROM cache WHERE key = ?").get(key) as
			| { label: string }
			| undefined;
		return usableLabel(row?.label);
	} catch {
		return undefined;
	}
}

/** Store a non-empty label (upsert) and enforce the size cap. Best-effort. */
export function cacheSet(key: string, label: string): void {
	const usable = usableLabel(label);
	if (!usable) return;
	const d = getDb();
	if (!d) return;
	try {
		d.prepare(
			"INSERT INTO cache(key, label, created_at) VALUES(?, ?, ?) " +
				"ON CONFLICT(key) DO UPDATE SET label = excluded.label, created_at = excluded.created_at",
		).run(key, usable, Date.now());
		d.prepare(
			"DELETE FROM cache WHERE key NOT IN " +
				"(SELECT key FROM cache ORDER BY created_at DESC LIMIT ?)",
		).run(MAX_ENTRIES);
	} catch {
		/* best-effort; cache loss is never fatal */
	}
}

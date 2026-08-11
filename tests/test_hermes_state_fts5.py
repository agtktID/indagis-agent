"""FTS5-related tests, extracted from tests/test_hermes_state.py (issue #12).

The four classes here were split out of the main hermes_state test file
to bring its wall-clock time under the 300s per-file timeout enforced
by scripts/run_tests_parallel.py. These classes are FTS5-specific and
account for the majority of the original file's runtime.

The SQLite feature-absence mocks (_NoFtsCursor, _NoTrigramCursor, etc.)
are imported from tests.test_hermes_state_helpers.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import time
import json
from unittest import mock

import pytest

import hermes_state
from agent.session_activity import ActivityProvenance
from hermes_state import SCHEMA_SQL, SCHEMA_VERSION, SessionDB

from tests.test_hermes_state_helpers import (
    _NoFtsCursor,
    _NoFtsConnection,
    _NoFtsExistingTableCursor,
    _NoFtsExistingTableConnection,
    _NoTrigramCursor,
    _NoTrigramConnection,
)


@pytest.fixture()
def db(tmp_path):
    return SessionDB(tmp_path / "state.db")


class TestFTS5Search:
    def test_search_finds_content(self, db):
        db.create_session(session_id="s1", source="cli")
        db.append_message("s1", role="user", content="How do I deploy with Docker?")
        db.append_message("s1", role="assistant", content="Use docker compose up.")

        results = db.search_messages("docker")
        assert len(results) == 2
        # At least one result should mention docker
        snippets = [r.get("snippet", "") for r in results]
        assert any("docker" in s.lower() or "Docker" in s for s in snippets)






    def test_search_returns_context(self, db):
        db.create_session(session_id="s1", source="cli")
        db.append_message("s1", role="user", content="Tell me about Kubernetes")
        db.append_message("s1", role="assistant", content="Kubernetes is an orchestrator.")

        results = db.search_messages("Kubernetes")
        assert len(results) == 2
        assert "context" in results[0]
        assert isinstance(results[0]["context"], list)
        assert len(results[0]["context"]) > 0

    def test_search_fields_project_results_without_changing_default(self, db):
        db.create_session(session_id="s1", source="cli")
        db.append_message("s1", role="user", content="Tell me about Kubernetes")
        db.append_message("s1", role="assistant", content="Kubernetes is an orchestrator.")

        projected = db.search_messages(
            "Kubernetes", fields=("session_id", "role", "snippet")
        )
        default = db.search_messages("Kubernetes")

        assert len(projected) == len(default) == 2
        assert all(set(row) == {"session_id", "role", "snippet"} for row in projected)
        assert [
            (row["session_id"], row["role"], row["snippet"])
            for row in projected
        ] == [
            (row["session_id"], row["role"], row["snippet"])
            for row in default
        ]
        assert all("context" in row and row["context"] for row in default)

    def test_search_projection_skips_context_enrichment_queries(self, db):
        db.create_session(session_id="s1", source="cli")
        db.append_message("s1", role="user", content="before")
        db.append_message("s1", role="assistant", content="projectionneedle")
        db.append_message("s1", role="user", content="after")

        statements = []
        read_conn = db._get_read_conn() or db._conn
        traced_connections = [db._conn]
        if read_conn is not db._conn:
            traced_connections.append(read_conn)
        for conn in traced_connections:
            conn.set_trace_callback(statements.append)

        def context_query_count():
            normalized = (" ".join(sql.upper().split()) for sql in statements)
            return sum("WITH TARGET AS (" in sql for sql in normalized)

        try:
            projected = db.search_messages(
                "projectionneedle", fields=("session_id", "snippet")
            )
            assert len(projected) == 1
            assert context_query_count() == 0

            full = db.search_messages(
                "projectionneedle", fields=("session_id", "context")
            )
            assert len(full) == 1
            assert full[0]["context"]
            assert context_query_count() == 1

            default = db.search_messages("projectionneedle")
            assert len(default) == 1
            assert default[0]["context"]
            assert context_query_count() == 2
        finally:
            for conn in traced_connections:
                conn.set_trace_callback(None)

    def test_sanitize_fts5_query_strips_dangerous_chars(self):
        """Unit test for _sanitize_fts5_query static method."""
        from hermes_state import SessionDB
        s = SessionDB._sanitize_fts5_query
        assert s('hello world') == 'hello world'
        assert '+' not in s('C++')
        assert '"' not in s('"unterminated')
        assert '(' not in s('(problem')
        assert '{' not in s('{test}')
        # Dangling operators removed
        assert s('hello AND') == 'hello'
        assert s('OR world') == 'world'
        # Leading bare * removed
        assert s('***') == ''
        # Valid prefix kept
        assert s('deploy*') == 'deploy*'
        # Colon (FTS5 column-filter operator) stripped, both terms preserved
        assert ':' not in s('TODO: fix')
        assert s('TODO: fix').split() == ['TODO', 'fix']
        assert ':' not in s('error:timeout')






    def test_long_search_query_is_capped_and_does_not_crash(self, db):
        db.create_session(session_id="s1", source="cli")
        db.append_message("s1", role="user", content="bounded sanitizer target")

        query = ('"' * 50_000) + (" bounded" * 10_000)
        start = time.perf_counter()
        results = db.search_messages(query)
        elapsed = time.perf_counter() - start

        assert isinstance(results, list)
        assert elapsed < 1.0


# =========================================================================
# CJK (Chinese/Japanese/Korean) LIKE fallback
# =========================================================================



class TestFTS5ToolCallIndexing:
    """Regression tests: search_messages must see tool_name and tool_calls.

    Before #16751's fix, `messages_fts` only indexed `messages.content`, so
    tokens that only appeared in `tool_name` or the serialized `tool_calls`
    JSON were invisible to session_search even though the row was in the DB.
    """

    def test_tool_name_is_searchable(self, db):
        db.create_session(session_id="s1", source="cli")
        db.append_message(
            "s1", role="assistant", content="",
            tool_name="UNIQUETOOLNAME",
        )
        results = db.search_messages("UNIQUETOOLNAME")
        assert len(results) == 1

    def test_tool_calls_args_are_searchable(self, db):
        db.create_session(session_id="s1", source="cli")
        db.append_message(
            "s1", role="assistant", content="",
            tool_calls=[{
                "id": "c1",
                "type": "function",
                "function": {
                    "name": "web_search",
                    "arguments": '{"query": "UNIQUESEARCHTOKEN"}',
                },
            }],
        )
        results = db.search_messages("UNIQUESEARCHTOKEN")
        assert len(results) == 1







class TestFTS5ToolCallMigration:
    """v11 migration: pre-existing state.db with old external-content FTS tables
    must be re-indexed so tool_name / tool_calls become searchable after upgrade."""

    def test_v10_to_v11_upgrade_backfills_tool_fields(self, tmp_path):
        """Simulate an existing user: build a v10-shaped DB by hand, insert a
        row with tool_calls, then open via SessionDB (which runs migrations).
        After upgrade, the tool_calls token must be searchable."""
        import sqlite3

        db_path = tmp_path / "legacy.db"

        # Build the pre-v11 schema by hand: external-content FTS tables +
        # old triggers that only reference new.content.
        conn = sqlite3.connect(str(db_path))
        conn.executescript("""
            CREATE TABLE schema_version (version INTEGER NOT NULL);
            INSERT INTO schema_version (version) VALUES (10);

            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                source TEXT,
                started_at REAL,
                ended_at REAL,
                title TEXT,
                parent_session_id TEXT,
                message_count INTEGER DEFAULT 0,
                tool_call_count INTEGER DEFAULT 0,
                api_call_count INTEGER DEFAULT 0
            );
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_name TEXT,
                tool_calls TEXT,
                tool_call_id TEXT,
                token_count INTEGER,
                finish_reason TEXT,
                reasoning TEXT,
                reasoning_content TEXT,
                reasoning_details TEXT,
                codex_reasoning_items TEXT,
                codex_message_items TEXT
            );

            CREATE VIRTUAL TABLE messages_fts USING fts5(
                content, content=messages, content_rowid=id
            );
            CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
            END;

            CREATE VIRTUAL TABLE messages_fts_trigram USING fts5(
                content, content=messages, content_rowid=id, tokenize='trigram'
            );
            CREATE TRIGGER messages_fts_trigram_insert AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts_trigram(rowid, content) VALUES (new.id, new.content);
            END;
        """)
        conn.execute(
            "INSERT INTO sessions (id, source, started_at) VALUES (?, ?, ?)",
            ("s1", "cli", time.time()),
        )
        conn.execute(
            "INSERT INTO messages (session_id, timestamp, role, content, tool_name, tool_calls) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("s1", time.time(), "assistant", "", "LEGACYTOOL",
             '{"function":{"name":"web_search","arguments":"{\\"q\\":\\"LEGACYARG\\"}"}}'),
        )
        conn.commit()

        # Verify the legacy FTS rows don't contain the tool tokens yet.
        legacy_hits = conn.execute(
            "SELECT rowid FROM messages_fts WHERE messages_fts MATCH 'LEGACYTOOL'"
        ).fetchall()
        assert legacy_hits == [], "sanity: legacy FTS must NOT contain tool_name"
        conn.close()

        # Open via SessionDB — the legacy DB is detected as optimizable but
        # NOT auto-migrated (opt-in). Its old content-only index still works
        # for content, but doesn't yet cover tool_name/tool_calls (#16751).
        session_db = SessionDB(db_path=db_path)
        try:
            assert session_db.fts_optimize_available() is True

            # `hermes db optimize` performs the v23 transition; afterwards the
            # tool fields are searchable.
            result = session_db.optimize_fts_storage(vacuum=False)
            assert result["ok"] is True
            assert len(session_db.search_messages("LEGACYTOOL")) == 1, \
                "v23 optimize must index tool_name into FTS"
            assert len(session_db.search_messages("LEGACYARG")) == 1, \
                "v23 optimize must index tool_calls JSON into FTS"
            # schema_version bumped once the FTS layer is v23
            from hermes_state import SCHEMA_VERSION
            row = session_db._conn.execute(
                "SELECT version FROM schema_version LIMIT 1"
            ).fetchone()
            version = row["version"] if hasattr(row, "keys") else row[0]
            assert version == SCHEMA_VERSION
        finally:
            session_db.close()




class TestFTSExternalContentMigration:
    """v23 migration: inline-mode FTS tables (v11-v22) are rebuilt as
    external-content tables, and role='tool' rows are excluded from the
    trigram index while remaining searchable via the standard index."""

    @staticmethod
    def _build_v22_db(db_path):
        """Build a v22-shaped DB by hand: inline FTS tables + concat triggers."""
        conn = sqlite3.connect(str(db_path))
        conn.executescript(SCHEMA_SQL)
        # Replace the current (v23) FTS objects with the v22 inline shape.
        conn.executescript("""
            DROP TABLE IF EXISTS messages_fts;
            DROP TABLE IF EXISTS messages_fts_trigram;
            DROP VIEW IF EXISTS messages_fts_trigram_src;

            CREATE VIRTUAL TABLE messages_fts USING fts5(content);
            CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(rowid, content) VALUES (
                    new.id,
                    COALESCE(new.content, '') || ' ' || COALESCE(new.tool_name, '') || ' ' || COALESCE(new.tool_calls, '')
                );
            END;

            CREATE VIRTUAL TABLE messages_fts_trigram USING fts5(content, tokenize='trigram');
            CREATE TRIGGER messages_fts_trigram_insert AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts_trigram(rowid, content) VALUES (
                    new.id,
                    COALESCE(new.content, '') || ' ' || COALESCE(new.tool_name, '') || ' ' || COALESCE(new.tool_calls, '')
                );
            END;
        """)
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version (version) VALUES (22)")
        conn.execute(
            "INSERT INTO sessions (id, source, started_at) VALUES ('s1', 'cli', ?)",
            (time.time(),),
        )
        rows = [
            ("user", "find the 大别山项目 deployment notes", None, None),
            ("assistant", "关于大别山项目的总结在这里", None,
             '{"function":{"name":"send_message","arguments":"{}"}}'),
            ("tool", "TOOLBLOB " + "x" * 5000 + " 项目文件内容测试", "read_file", None),
        ]
        for role, content, tool_name, tool_calls in rows:
            conn.execute(
                "INSERT INTO messages (session_id, timestamp, role, content, tool_name, tool_calls) "
                "VALUES ('s1', ?, ?, ?, ?, ?)",
                (time.time(), role, content, tool_name, tool_calls),
            )
        conn.commit()
        # Sanity: v22 inline tables have their own content shadow tables.
        shadow = conn.execute(
            "SELECT name FROM sqlite_master WHERE name = 'messages_fts_content'"
        ).fetchall()
        assert shadow, "sanity: v22 inline FTS must have a content shadow table"
        conn.close()

    def test_v22_open_leaves_legacy_untouched_and_advertises(self, tmp_path):
        """Opening a legacy v22 DB must NOT auto-migrate the FTS layout, but
        the main schema_version DOES advance (decoupled) so future non-FTS
        migrations aren't blocked. The inline index keeps working and the
        opt-in flag is set."""
        db_path = tmp_path / "v22.db"
        self._build_v22_db(db_path)

        db = SessionDB(db_path=db_path)
        try:
            # DECOUPLED: the main schema_version advances to current even though
            # the FTS layout stays legacy — future migrations must not be gated
            # behind the FTS opt-in.
            version = db._conn.execute(
                "SELECT version FROM schema_version"
            ).fetchone()[0]
            assert version == SCHEMA_VERSION, "main schema version must advance"
            # But the FTS storage layout is NOT stamped current — it's legacy.
            assert db.get_meta("fts_storage_version") is None
            assert db.fts_optimize_available() is True
            assert db.get_meta("fts_optimize_available") == "1"

            # Legacy inline shape is intact (content shadow table still there).
            assert db._conn.execute(
                "SELECT name FROM sqlite_master WHERE name = 'messages_fts_content'"
            ).fetchone() is not None

            # Search still works on the legacy index (no deferred rebuild).
            assert db.fts_rebuild_status() is None
            assert len(db.search_messages("deployment")) == 1
            assert len(db.search_messages("send_message")) == 1  # #16751 held

            # A new write is indexed live by the legacy triggers.
            db.append_message("s1", role="user", content="AFTEROPEN token")
            assert len(db.search_messages("AFTEROPEN")) == 1
        finally:
            db.close()






    def _simulate_pre_fix_demote_crash_window(self, db):
        """Replay the pre-fix demote crash window: trash + empty v23 schema,
        no rebuild markers (executescript committed mid-demote before markers).

        Mirrors what happened when ``_ensure_fts_schema`` ran inside
        ``_execute_write`` and the process died before the marker writes.
        """
        from hermes_state import FTS_SQL, FTS_TRIGRAM_SQL

        conn = db._conn
        db._drop_fts_triggers(conn)
        conn.execute("DROP VIEW IF EXISTS messages_fts_trigram_src")
        had = bool(conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name IN ('messages_fts', 'messages_fts_trigram') "
            "AND sql LIKE 'CREATE VIRTUAL TABLE%' LIMIT 1"
        ).fetchone())
        assert had, "sanity: expected legacy/virtual FTS tables to demote"
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "DELETE FROM sqlite_master WHERE type = 'table' "
            "AND name IN ('messages_fts', 'messages_fts_trigram') "
            "AND sql LIKE 'CREATE VIRTUAL TABLE%'"
        )
        conn.execute("PRAGMA writable_schema=RESET")
        shadows = [
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND (name LIKE 'messages_fts_%' ESCAPE '\\' "
                "OR name LIKE 'messages_fts_trigram_%' ESCAPE '\\')"
            ).fetchall()
        ]
        for sh in shadows:
            conn.execute(f"ALTER TABLE {sh} RENAME TO fts_v22_trash_{sh}")
        # executescript commits — empty v23 tables without markers.
        conn.executescript(FTS_SQL)
        try:
            conn.executescript(FTS_TRIGRAM_SQL)
        except sqlite3.OperationalError:
            pass
        # Intentionally leave fts_rebuild_* unset (the crash window).

    def test_optimize_resume_after_demote_crash_window_restores_search(
        self, tmp_path
    ):
        """Pre-fix: demote crash left trash + empty v23 index, no markers.
        Re-run tore down trash and stamped optimized with docsize=0 — permanent
        search loss for historical rows. Re-run must backfill and restore."""
        db_path = tmp_path / "v22.db"
        self._build_v22_db(db_path)

        db = SessionDB(db_path=db_path)
        try:
            assert len(db.search_messages("deployment")) == 1
            self._simulate_pre_fix_demote_crash_window(db)
            # Crash window shape: no markers, trash present, empty index.
            assert db.get_meta("fts_rebuild_high_water") is None
            assert db.get_meta("fts_rebuild_progress") is None
            assert db._has_fts_trash(db._conn) is True
            assert db._conn.execute(
                "SELECT COUNT(*) FROM messages_fts_docsize"
            ).fetchone()[0] == 0
            assert len(db.search_messages("deployment")) == 0

            # Still offered (trash and/or empty-index heal).
            assert db.fts_optimize_available() is True

            result = db.optimize_fts_storage(vacuum=False)
            assert result["ok"] is True
            assert db.fts_rebuild_status() is None
            assert db.fts_optimize_available() is False
            assert db.get_meta("fts_storage_version") == str(
                hermes_state.FTS_STORAGE_VERSION
            )
            assert db._conn.execute(
                "SELECT name FROM sqlite_master WHERE name LIKE '%_v22_trash%'"
            ).fetchall() == []
            # Historical rows searchable again; index fully populated.
            assert len(db.search_messages("deployment")) == 1
            assert len(db.search_messages("TOOLBLOB")) == 1
            n_msg = db._conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            n_fts = db._conn.execute(
                "SELECT COUNT(*) FROM messages_fts_docsize"
            ).fetchone()[0]
            assert n_fts == n_msg
            db._conn.execute(
                "INSERT INTO messages_fts(messages_fts, rank) VALUES('integrity-check', 1)"
            )
        finally:
            db.close()

    def test_optimize_heals_premature_stamp_with_empty_index(self, tmp_path):
        """Pre-fix settle could stamp fts_storage_version after tearing down
        trash with an empty index and no markers. Re-run must clear the stamp,
        backfill, and re-earn the layout version."""
        db_path = tmp_path / "v22.db"
        self._build_v22_db(db_path)

        db = SessionDB(db_path=db_path)
        try:
            self._simulate_pre_fix_demote_crash_window(db)
            # Simulate the bad resume: trash already gone, empty index stamped.
            trash = [
                r[0] for r in db._conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' "
                    "AND name LIKE 'fts\\_v22\\_trash\\_%' ESCAPE '\\'"
                ).fetchall()
            ]
            for tbl in trash:
                db._conn.execute(f"DROP TABLE IF EXISTS {tbl}")
            db._conn.execute(
                "INSERT INTO state_meta (key, value) VALUES "
                "('fts_storage_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(hermes_state.FTS_STORAGE_VERSION),),
            )
            db._conn.commit()

            assert db.get_meta("fts_rebuild_high_water") is None
            assert db._has_fts_trash(db._conn) is False
            assert db._fts_external_index_empty_with_messages(db._conn) is True
            # Must still be offered despite the premature stamp.
            assert db.fts_optimize_available() is True
            assert len(db.search_messages("deployment")) == 0

            result = db.optimize_fts_storage(vacuum=False)
            assert result["ok"] is True
            assert len(db.search_messages("deployment")) == 1
            assert db.get_meta("fts_storage_version") == str(
                hermes_state.FTS_STORAGE_VERSION
            )
            assert db.fts_optimize_available() is False
        finally:
            db.close()

    def test_optimize_heals_high_water_without_progress(self, tmp_path):
        """high_water without progress used to make fts_rebuild_step return
        False immediately (treated as finished by another process), then
        settle stamped success while the marker remained. Re-seed progress
        and complete the empty-index backfill."""
        db_path = tmp_path / "v22.db"
        self._build_v22_db(db_path)
        db = SessionDB(db_path=db_path)
        try:
            self._simulate_pre_fix_demote_crash_window(db)
            hw = db._conn.execute(
                "SELECT COALESCE(MAX(id), 0) FROM messages"
            ).fetchone()[0]
            # Orphan shape: high_water alone on an empty external index.
            db.set_meta("fts_rebuild_high_water", str(hw))
            db._conn.execute(
                "DELETE FROM state_meta WHERE key = ?", ("fts_rebuild_progress",)
            )
            db._conn.commit()
            assert db.get_meta("fts_rebuild_progress") is None
            assert db.fts_optimize_available() is True
            # Empty index: base FTS MATCH finds nothing (gap LIKE may still
            # supplement when high_water is set — that is intentional).
            assert db._conn.execute(
                "SELECT COUNT(*) FROM messages_fts_docsize"
            ).fetchone()[0] == 0

            result = db.optimize_fts_storage(vacuum=False)
            assert result["ok"] is True
            assert db.get_meta("fts_rebuild_high_water") is None
            assert db.get_meta("fts_rebuild_progress") is None
            n_msg = db._conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            n_fts = db._conn.execute(
                "SELECT COUNT(*) FROM messages_fts_docsize"
            ).fetchone()[0]
            assert n_fts == n_msg
            assert len(db.search_messages("deployment")) == 1
            assert db.fts_optimize_available() is False
        finally:
            db.close()

    def test_repair_rebuilds_partial_index_without_duplicates(self, tmp_path):
        """high_water without progress on a PARTIALLY indexed DB must not
        replay the backfill from zero on top of surviving rows: the chunk
        worker inserts its whole id range with no anti-join, so replay
        duplicates every already-indexed row. Recovery must reset the index
        to a known-empty surface first, then rebuild."""
        db_path = tmp_path / "v22.db"
        self._build_v22_db(db_path)
        db = SessionDB(db_path=db_path)
        try:
            self._simulate_pre_fix_demote_crash_window(db)
            hw = db._conn.execute(
                "SELECT COALESCE(MAX(id), 0) FROM messages"
            ).fetchone()[0]
            db.set_meta("fts_rebuild_high_water", str(hw))
            db._conn.execute(
                "DELETE FROM state_meta WHERE key = ?", ("fts_rebuild_progress",)
            )
            # Partial index: one row survived from an interrupted backfill.
            db._conn.execute(
                "INSERT INTO messages_fts(rowid, content, tool_name, tool_calls) "
                "SELECT id, content, tool_name, tool_calls FROM messages "
                "WHERE id = 1"
            )
            db._conn.commit()
            assert db._conn.execute(
                "SELECT COUNT(*) FROM messages_fts_docsize"
            ).fetchone()[0] == 1

            result = db.optimize_fts_storage(vacuum=False)
            assert result["ok"] is True
            n_msg = db._conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            n_fts = db._conn.execute(
                "SELECT COUNT(*) FROM messages_fts_docsize"
            ).fetchone()[0]
            # Exactly one index entry per message: no replay duplicates.
            assert n_fts == n_msg
            assert len(db.search_messages("deployment")) == 1
            db._conn.execute(
                "INSERT INTO messages_fts(messages_fts, rank) VALUES('integrity-check', 1)"
            )
        finally:
            db.close()

    def test_repair_bookkeeping_reseeds_missing_progress(self, tmp_path):
        """Unit: high_water without progress gets progress='0' without
        forcing a full marker reset when a real backfill is already claimed."""
        db = SessionDB(db_path=tmp_path / "fresh.db")
        try:
            db.create_session(session_id="s1", source="cli")
            db.append_message("s1", role="user", content="bookkeeping needle")
            db.set_meta("fts_rebuild_high_water", "42")
            db._conn.execute(
                "DELETE FROM state_meta WHERE key = ?", ("fts_rebuild_progress",)
            )
            db._conn.commit()
            db._repair_optimize_bookkeeping()
            assert db.get_meta("fts_rebuild_high_water") == "42"
            assert db.get_meta("fts_rebuild_progress") == "0"
        finally:
            db.close()

    def test_demote_writes_markers_before_empty_schema(self, tmp_path):
        """Demote must commit rebuild markers before createscript builds the
        empty v23 tables — so a crash between stage and ensure still leaves
        a resumable claim rather than an unmarked empty index."""
        db_path = tmp_path / "v22.db"
        self._build_v22_db(db_path)
        db = SessionDB(db_path=db_path)
        try:
            # Patch ensure to fail *after* the staged write commits, simulating
            # death mid schema-create. Markers must already be durable.
            orig_ensure = db._ensure_fts_schema
            calls = {"n": 0}

            def boom(cursor, table_name, ddl):
                calls["n"] += 1
                if table_name == "messages_fts":
                    # Markers must already be on disk from the staged write.
                    row = db._conn.execute(
                        "SELECT value FROM state_meta "
                        "WHERE key = 'fts_rebuild_high_water'"
                    ).fetchone()
                    assert row is not None, (
                        "markers must be committed before empty v23 schema create"
                    )
                    progress = db._conn.execute(
                        "SELECT value FROM state_meta "
                        "WHERE key = 'fts_rebuild_progress'"
                    ).fetchone()
                    assert progress is not None and progress[0] == "0"
                    raise sqlite3.OperationalError("simulated crash mid-ensure")
                return orig_ensure(cursor, table_name, ddl)

            db._ensure_fts_schema = boom  # type: ignore[method-assign]
            try:
                db._demote_legacy_fts_to_trash()
                raise AssertionError("demote should have raised")
            except sqlite3.OperationalError as exc:
                assert "simulated crash" in str(exc)

            # Staged demote survived: markers + trash, no successful stamp.
            assert db.get_meta("fts_rebuild_high_water") is not None
            assert db.get_meta("fts_rebuild_progress") == "0"
            assert db._has_fts_trash(db._conn) is True
            assert db.get_meta("fts_storage_version") is None

            # Restore ensure and resume — full optimize completes.
            db._ensure_fts_schema = orig_ensure  # type: ignore[method-assign]
            result = db.optimize_fts_storage(vacuum=False)
            assert result["ok"] is True
            assert len(db.search_messages("deployment")) == 1
            assert db.fts_optimize_available() is False
        finally:
            db.close()

    def test_optimize_settle_refuses_pending_backfill(self, tmp_path):
        """Settle must not stamp while high_water markers remain."""
        db = SessionDB(db_path=tmp_path / "fresh.db")
        try:
            db.create_session(session_id="s1", source="cli")
            db.append_message("s1", role="user", content="settle guard needle")
            # Plant markers without going through demote.
            db.set_meta("fts_rebuild_high_water", "1")
            db.set_meta("fts_rebuild_progress", "0")
            # The public contract: optimize returns ok=False when still
            # pending. Simulate an unfinishable backfill by stubbing the
            # chunk step to a no-op while markers stay.
            db.fts_rebuild_step = lambda: False  # type: ignore[method-assign]
            result = db.optimize_fts_storage(vacuum=False)
            assert result["ok"] is False
            assert result.get("reason") == "backfill_incomplete"
            assert db.get_meta("fts_storage_version") is None
            assert db.get_meta("fts_rebuild_high_water") is not None
        finally:
            db.close()

    def test_v23_fresh_db_born_optimized(self, tmp_path):
        """A brand-new DB is born on v23 — no legacy layout, no opt-in flag,
        no pending rebuild."""
        db = SessionDB(db_path=tmp_path / "fresh.db")
        try:
            assert db.fts_optimize_available() is False
            assert db.fts_rebuild_status() is None
            assert db.get_meta("fts_optimize_available") is None
            # Already external-content: no shadow copy tables.
            assert db._conn.execute(
                "SELECT name FROM sqlite_master WHERE name = 'messages_fts_content'"
            ).fetchone() is None
            db.create_session(session_id="s1", source="cli")
            db.append_message("s1", role="user", content="hello fresh world")
            assert len(db.search_messages("fresh")) == 1
        finally:
            db.close()


    def test_v23_cjk_tool_role_filter_uses_like_fallback(self, tmp_path):
        """A CJK query with role_filter=['tool'] must bypass the trigram index
        (tool rows aren't in it) and still find matches via LIKE."""
        db = SessionDB(db_path=tmp_path / "fresh.db")
        try:
            db.create_session(session_id="s1", source="cli")
            db.append_message("s1", role="tool", content="错误日志：数据库连接超时",
                              tool_name="terminal")
            hits = db.search_messages("数据库连接", role_filter=["tool"])
            assert len(hits) == 1
            assert hits[0]["role"] == "tool"
        finally:
            db.close()



# ---------------------------------------------------------------------------
# apply_wal_with_fallback — read-only probe tests
# ---------------------------------------------------------------------------






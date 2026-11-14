import collections, json, sqlite3, traceback, weakref
from learnloop.db import connection as DBC

def test_measure(tmp_path, monkeypatch):
    from tests.rospeed_join_helpers import _journey
    stats = []
    causes = collections.Counter()
    real = DBC._ConnectionPool.close
    def close(self):
        if not self.closed:
            stats.append((self.opened, self.handed))
        return real(self)
    monkeypatch.setattr(DBC._ConnectionPool, "close", close)

    def _wrapped(self, inner):
        reference = weakref.ref(self)
        def authorizer(action, arg1, arg2, database, trigger):
            connection = reference()
            if connection is not None and connection._watching and action not in DBC._READ_ACTIONS and not (
                    action == sqlite3.SQLITE_PRAGMA and arg2 is None):
                if not connection._marked:
                    frames = [f for f in traceback.extract_stack() if "/src/learnloop" in f.filename and "db/connection" not in f.filename and "db/scopes" not in f.filename]
                    where = f"{frames[-1].filename.split('/src/')[1]}:{frames[-1].lineno}" if frames else "?"
                    kind = {sqlite3.SQLITE_INSERT: "INSERT", sqlite3.SQLITE_UPDATE: "UPDATE", sqlite3.SQLITE_DELETE: "DELETE", sqlite3.SQLITE_PRAGMA: f"PRAGMA {arg1}"}.get(action, str(action))
                    causes[(kind, where)] += 1
                connection._marked = True
            return sqlite3.SQLITE_OK if inner is None else inner(action, arg1, arg2, database, trigger)
        return authorizer
    monkeypatch.setattr(DBC._PooledSqlite, "_wrapped", _wrapped)
    _journey(tmp_path, steps=6)
    n = len(stats)
    print("OPENS_PER_JOB", json.dumps({"jobs": n, "opened_mean": sum(s[0] for s in stats)/max(n,1), "handed_mean": sum(s[1] for s in stats)/max(n,1), "opened": [s[0] for s in stats]}))
    for k, v in causes.most_common():
        print("CAUSE", v, k)

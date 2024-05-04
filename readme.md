# shorturl
A short URL generator web service written in Python by Brandon Chastain.

## Limitations
~Data is only stored in memory. TODO: Persist short URLs in a fault resistant DB or cache.~ Data is persisted in a sqlite3 database.

Concurrency may be limited. There may also be race conditions when mixing create/delete operations from different clients at the same time.

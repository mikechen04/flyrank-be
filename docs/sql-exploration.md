# Stage 4 — SQL I tried

I opened `tasks.db` and ran these queries:

```sql
SELECT * FROM tasks;
```

```text
(1, 'Learn FastAPI', 0)
(2, 'Build a CRUD API', 0)
(3, 'Push to GitHub', 1)
```

```sql
SELECT * FROM tasks WHERE done = 1;
```

```text
(3, 'Push to GitHub', 1)
```

```sql
SELECT COUNT(*) FROM tasks;
```

```text
3
```

```sql
UPDATE tasks SET done = 1;
```

```sql
DELETE FROM tasks WHERE done = 1;
```

After the delete, the table was empty. Restarting the API created the 3 example tasks again because the table was empty.

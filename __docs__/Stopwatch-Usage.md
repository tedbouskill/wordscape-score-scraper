# ⏱️ Stopwatch & LoggerStopwatch Usage Guide

This guide documents usage patterns for the `Stopwatch` and `LoggerStopwatch` classes.

---

## ✅ Stopwatch (No Logging)

### 🔹 Initialize
```python
from stopwatch import Stopwatch
sw = Stopwatch()
```

### 🔹 Manual Timing
```python
sw.start()
# ... your code ...
sw.stop()

print(f"Elapsed: {sw.last_duration():.4f} seconds")
```

### 🔹 One-Shot Timing
```python
def slow_fn():
    time.sleep(0.3)
    return 42

result = sw.measure(slow_fn)
print(f"Result: {result}, Time: {sw.last_duration():.4f} seconds")
```

### 🔹 Scoped Block Timing
```python
with sw:
    time.sleep(0.2)

print(f"Scoped: {sw.last_duration():.4f} seconds")
```

### 🔹 Decorator Timing
```python
@sw.timeit
def render():
    time.sleep(0.1)

render()
print(f"Decorated: {sw.last_duration():.4f} seconds")
```

### 🔹 Get Total Accumulated Time
```python
print(f"Total elapsed: {sw.total_elapsed():.4f} seconds")
```

---

## 📣 LoggerStopwatch (With Logging Support)

### 🔹 Initialize with Label and Logging Level
```python
import logging
from logger_stopwatch import LoggerStopwatch

logging.basicConfig(level=logging.DEBUG)
lsw = LoggerStopwatch(label="Experiment", level=logging.DEBUG)
```

### 🔹 Manual Timing (Logs on stop)
```python
lsw.start()
time.sleep(0.15)
lsw.stop()
# Logs: [Experiment] Last: 0.15xx seconds | Total: 0.15xx seconds
```

### 🔹 Auto-Logging with `measure()`
```python
def expensive():
    time.sleep(0.2)
    return "done"

result = lsw.measure(expensive)
# Logs: [Experiment] Last: 0.20xx seconds | Total: 0.20xx seconds
```

### 🔹 Context Manager
```python
with LoggerStopwatch("Scoped Task", level=logging.INFO):
    time.sleep(0.25)
# Logs: [Scoped Task] Last: 0.25xx seconds | Total: 0.25xx seconds
```

### 🔹 Function Decorator
```python
@lsw.timeit
def convert():
    time.sleep(0.1)

convert()
# Logs: [Experiment] Last: 0.10xx seconds | Total: 0.30xx seconds
```

---

## 🧠 Summary

| Intent                     | Method/Pattern     |
|----------------------------|--------------------|
| One-off timing             | `measure(func)`    |
| Persistent function timing | `@timeit` decorator|
| Scoped timing              | `with stopwatch:`  |
| Manual start/stop          | `start()`, `stop()`|
| Last run duration          | `last_duration()`  |
| Total accumulated time     | `total_elapsed()`  |


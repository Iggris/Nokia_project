# Nokia_project

things to install to get this project up and running:
1) Python version Python 3.12.6 (https://www.python.org/downloads/)
2. Install dependencies:
   ```bash
   pip install -r requirements.txt

Things done: 
1) Searching a file using hyperscan in stream mode.
2) Searching a directory using hyperscan in stream mode.
3) possibility of changing the engine to python regex
    -new opt flag --engine:
    python main.py run regex.txt test_file.txt --engine (python or hyperscan)


Things to do:
1) Add the option to search a directory without searching selected files/data extensions (e.g., log, txt, etc.).
2) Create a class for saving regexes to a text file (consider whether to make some kind of extension for the future) and saving recompiled regexes
3) Use recompiled regexes for searching files or directories



### FileScanner

`FileScanner` is a helper class for scanning files and directory trees using different regex engines (e.g. `HyperscanEngine` or `PythonEngine`). It provides a simple API for compiling patterns once and reusing them to scan many files in a streaming way.

- **`__init__(self, engine: RegexEngine | None = None)`**  
  Creates a new `FileScanner` instance.  
  If no `engine` is provided, it uses `HyperscanEngine` by default (you can also pass `PythonEngine` or any other implementation of `RegexEngine`). It also initializes an internal `results` list that stores matches for the current scan.

- **`compile_patterns(self, patterns: List[str]) -> None`**  
  Takes a list of regex patterns as strings, encodes them to UTF-8 bytes, and passes them to the underlying regex engine.  
  This method must be called before scanning files, so that the engine has a compiled database of patterns to match against.

- **`_match_callback(self, pattern_id: int, start: int, end: int, flags: int, filename: str)`**  
  Internal callback used by the regex engine when a match is found.  
  It resolves the matched pattern text (if available), builds a result dictionary with:
  - `pattern_id` – index of the matched pattern  
  - `start`, `end` – byte offsets of the match in the input stream  
  - `match` – the pattern string (or `"UNKNOWN"` if not available)  
  - `filename` – name of the file being scanned  
  and appends this dictionary to `self.results`.  
  This method is not meant to be called directly; it is used via `scan_file`.

- **`scan_file(self, filename: str, chunk_size: int = 4096) -> List[Dict]`**  
  Scans a single file in streaming mode.  
  It clears previous results, builds a local callback that forwards matches to `_match_callback`, and then uses `FileReader.chunks(...)` to feed the file in chunks to `engine.scan_stream(...)`.  
  If an error occurs (e.g. I/O or engine error), it prints an error message and continues.  
  Returns a list of match dictionaries produced while scanning this file.

- **`scan_tree(self, root, follow_symlinks: bool = False) -> List[Dict]`**  
  Recursively scans all files under a given directory.  
  It converts `root` to a `Path`, checks if it exists, and then uses `os.walk` to traverse the directory tree. For each file found, it calls `scan_file(...)` and extends a global `all_matches` list with the results.  
  If a file cannot be read due to missing permissions or another error, it prints a message and continues with the remaining files.  
  Returns a flat list of match dictionaries for all successfully scanned files under `root`.



### FileReader

`FileReader` is a small utility class for safely reading files in binary mode, especially useful when you want to process large files in chunks (e.g. for streaming or scanning).

- **Constant: `CHUNK_SIZE`**  
  Default chunk size in bytes used when reading files (4096 bytes).

---

#### `validate(file_path: str) -> None`  *(static method)*

Checks that the given path points to an existing regular file.

- Raises:
  - `FileNotFoundError` – if the path does not exist.
  - `ValueError` – if the path exists but is not a regular file (e.g. directory).

Use this before reading a file to fail fast on invalid paths.

---

#### `chunks(file_path: str, chunk_size: int | None = None) -> Iterable[bytes]`  *(static method)*

Reads a file in binary mode and yields its contents in consecutive chunks.

- **Parameters:**
  - `file_path`: Path to the file to read.
  - `chunk_size` (optional): Size of each chunk in bytes.  
    If `None`, uses the default `FileReader.CHUNK_SIZE`.

- **Behavior:**
  - Validates the file with `validate(file_path)` before reading.
  - Opens the file in binary mode (`"rb"`).
  - Repeatedly reads `chunk_size` bytes and `yield`s each chunk as `bytes`.
  - Stops when there is no more data to read.

This is intended for streaming large files without loading them fully into memory, and is used by other components (e.g. `FileScanner`) to process file contents incrementally.


### FileRegex

`FileRegex` is a small helper class for managing a text file that stores regex patterns (typically one pattern per line). It allows you to add, remove, check, and read patterns from that file.

Each non-empty line in the file is treated as a pattern definition. When reading patterns, only the part **before the first comma** is used (so you can optionally store comments or metadata after a comma).

---

#### `__init__(self, filename)`

Creates a `FileRegex` instance bound to a given file.

- `filename`: Path to the text file containing regex patterns.
- Ensures the file exists by opening it in append mode and closing it immediately.

---

#### `add_element(self, text)`

Adds a new pattern to the file if it does not already exist.

- `text`: Pattern string to add.
- Checks with `exist(text)`; if not found, appends `text.strip()` plus a newline to the file.

---

#### `delete_element(self, text)`

Removes all occurrences of a given pattern from the file.

- `text`: Pattern string to remove.
- Reads all lines, then overwrites the file with all lines **except** those whose stripped content equals `text.strip()`.

---

#### `choose_elements(self)`

Currently not implemented (`pass`).  
Can be extended later (e.g. to interactively select patterns).

---

#### `exist(self, text) -> bool`

Checks whether a given pattern already exists in the file.

- `text`: Pattern string to look for.
- Returns `True` if any line in the file, after `strip()`, is exactly equal to `text`; otherwise returns `False`.

---

#### `elements(self) -> list[str]`

Returns a list of regex patterns extracted from the file.

- Reads the file line by line.
- For each non-empty line:
  - Strips whitespace.
  - Splits on the first comma: `before_comma = text.split(",", 1)[0].strip()`.
  - Adds `before_comma` to the `patterns` list.
- Returns the list of extracted patterns.

This is the main method used by other components (like the CLI or `FileScanner`) to get the pattern list for compilation.


### PythonEngine

`PythonEngine` is a simple implementation of the `RegexEngine` interface that uses Python’s built-in `re` module. It’s a fallback/alternative to engines like Hyperscan and is useful when you don’t want external dependencies or just need something easy to run everywhere.

It works with patterns provided as `bytes`, compiles them to regular expressions, and can scan either a single `bytes` buffer or a sequence of chunks (`scan_stream`).

---

#### `__init__(self)`

Initializes the engine.

- Sets:
  - `self.compiled_patterns` – list of compiled regex objects with metadata.
  - `self.patterns` – original pattern byte strings.

---

#### `compile_patterns(self, patterns: List[bytes], ids: List[int] = None) -> None`

Compiles a list of regex patterns.

- **patterns**: List of patterns in `bytes` (e.g. UTF-8 encoded).
- **ids** (optional): List of integers used as pattern IDs.  
  If `None`, IDs are `0, 1, 2, ...` in order.

What it does:

1. Stores `patterns` on `self.patterns`, clears any previous compiled patterns.
2. For each pattern:
   - Decodes `pattern_bytes` to a string (`utf-8`).
   - Compiles it using `re.compile(...)`.
   - Stores a dict: `{'id': pattern_id, 'pattern': compiled, 'original': pattern_bytes}` in `self.compiled_patterns`.
3. If a pattern is invalid, prints a warning and skips it.

---

#### `scan(self, data: bytes, callback: Callable) -> None`

Scans a single `bytes` buffer for matches of all compiled patterns.

- **data**: The input to scan as `bytes`.
- **callback**: Function called for each match, with signature:
  `callback(pattern_id, start, end, flags, context)`.

What it does:

1. Raises `RuntimeError` if `compile_patterns` hasn’t been called.
2. Tries to decode `data` as UTF-8 (ignoring errors); falls back to `str(data)` on failure.
3. For each compiled pattern:
   - Calls `pattern.finditer(text)`.
   - For each match, calls `callback` with:
     - `pattern_id` – ID of the pattern.
     - `start`, `end` – character offsets of the match in `text`.
     - `flags` – always `0` in this implementation.
     - `context` – always `None` here.

---

#### `scan_stream(self, data_chunks: Iterable[bytes], callback: Callable, context: Any = None) -> None`

Scans a sequence of byte chunks. This is a “fake” stream: all chunks are buffered and scanned at once.

- **data_chunks**: Iterable of `bytes` chunks (e.g. from a file reader).
- **callback**: Same callback as in `scan`.
- **context**: Extra object passed back to the callback (e.g. filename).

What it does:

1. Raises `RuntimeError` if no patterns are compiled.
2. Concatenates all `data_chunks` into a single `buffer`.
3. Decodes `buffer` as UTF-8 (ignoring errors); falls back to `str(buffer)` on failure.
4. For each compiled pattern:
   - Calls `pattern.finditer(text)`.
   - For each match, calls `callback` with:
     - `pattern_id` – ID of the pattern.
     - `start`, `end` – character offsets.
     - `flags` – always `0`.
     - `context` – whatever was passed into `scan_stream`.

> Note: `scan_stream` does **not** do true streaming matching; it just gathers all chunks and runs a normal search on the combined text.



### HyperscanEngine

Internally it stores:

- `self.db` – compiled Hyperscan database (or `None` if not compiled yet),
- `self.patterns` – list of original pattern byte strings.

It uses:

- `COMPILER_MODE_FLAGS` – Hyperscan mode flags (streaming + SOM horizon).
- `COMPILE_FLAGS` – compile flags (leftmost start-of-match).

---

#### `compile_patterns(self, patterns, ids=None)`

Compiles a list of regex patterns into a Hyperscan database.

- **patterns**: List of patterns as `bytes`.
- **ids** (optional): List of integer IDs for each pattern.  
  If `None`, IDs are assigned as `0, 1, 2, ...`.

What it does:

1. Saves `patterns` on `self.patterns`.
2. If `ids` is not provided, creates a default list of IDs.
3. Prepares a list of flags (same for all patterns).
4. Creates a `hyperscan.Database` in streaming mode.
5. Calls `db.compile(...)` with the patterns, IDs, flags, and number of elements.

After this, the engine is ready to scan data with `scan` or `scan_stream`.

---

#### `scan(self, data, callback)`

Runs matching on a single block of data.

- **data**: The input to scan (`bytes`).
- **callback**: Match handler function passed directly to Hyperscan’s `scan`.

What it does:

1. Raises `RuntimeError` if `self.db` is `None` (not compiled yet).
2. Calls `self.db.scan(data, match_event_handler=callback)`.

The `callback` is invoked by Hyperscan for each match with its usual signature  
(e.g. `callback(id, from, to, flags, context)`).

---

#### `scan_stream(self, data_chunks, callback, context=None)`

Scans data in streaming mode using a Hyperscan stream.

- **data_chunks**: Iterable of `bytes` chunks (e.g. from a file reader).
- **callback**: Match handler function.
- **context**: Optional context object passed back to the callback.

What it does:

1. Raises `RuntimeError` if `self.db` is `None`.
2. Opens a streaming context: `with self.db.stream(...) as stream`.
3. For each `chunk` in `data_chunks`, calls `stream.scan(chunk)`.

Hyperscan maintains streaming state internally, so patterns can match across chunk boundaries.

---

#### `save_db(self, filename="hs.db")`

Serializes and saves the compiled Hyperscan database to a file.

- **filename**: Target file for the serialized database (default `hs.db`).

What it does:

1. Raises `RuntimeError` if `self.db` is `None`.
2. Uses `hyperscan.dumpb(self.db)` to serialize the database to bytes.
3. Writes the bytes to `filename` in binary mode.

This allows you to precompile your patterns once and reuse them later without recompiling.

---

#### `load_db(self, filename)`

Loads a previously saved Hyperscan database from a file.

- **filename**: Path to the file created by `save_db`.

What it does:

1. Reads the binary data from `filename`.
2. Uses `hyperscan.loadb(data, hyperscan.HS_MODE_STREAM)` to recreate the database in streaming mode.
3. Creates a `Scratch` space for the database: `self.db.scratch = hyperscan.Scratch(self.db)`.

After loading, the engine is ready to use `scan` and `scan_stream` with the restored database.



### RegexEngine (abstract base class)

`RegexEngine` is an abstract base class that defines a common interface for all regex engines used in this project (e.g. `HyperscanEngine`, `PythonEngine`).  
It allows the rest of the code (like `FileScanner`) to work with any engine that implements this interface, without depending on a specific regex library.

Implementations must provide three methods:

---

#### `compile_patterns(self, patterns: List[bytes], ids: List[int] | None = None) -> None`

Compile a list of regex patterns.

- **patterns** – list of patterns as byte strings (e.g. UTF-8 encoded).
- **ids** – optional list of integer IDs, one per pattern. If omitted, the implementation may assign IDs automatically.

The engine should store the compiled patterns internally so they can be used later by `scan` / `scan_stream`.

---

#### `scan(self, data: bytes, callback: Callable) -> None`

Scan a single block of data for matches.

- **data** – input to scan, as `bytes`.
- **callback** – function invoked for each match, typically with a signature like:
  `callback(pattern_id, start, end, flags, context)`.

Used for non-streaming, one-shot matching.

---

#### `scan_stream(self, data_chunks: Iterable[bytes], callback: Callable, context: Any | None = None) -> None`

Scan data provided as a sequence of chunks (streaming interface).

- **data_chunks** – iterable yielding `bytes` chunks.
- **callback** – match handler function (same as in `scan`).
- **context** – optional value passed through to the callback (e.g. filename).

Implementations may perform true streaming matching (like Hyperscan) or emulate it (e.g. by buffering).






HOW TO RUN:
python main.py build SOURCE [-o OUTPUT]
Build a regex pattern database from a text file.
SOURCE – text file with regexes, one regex per line
-o, --output – path to the file with the saved Hyperscan database
default: hs.db
Examples:
python main.py build patterns.txt
python main.py build patterns.txt -o my_patterns.db
python main.py run CONFIG TARGET [--engine {hyperscan,python}] [-o OUTPUT]
Scan a file or directory using regexes.
CONFIG –
either a compiled Hyperscan database (e.g., hs.db, generated by build)
or a plain text file with regexes (one regex per line)
TARGET – file or directory to scan
--engine – regex engine:
hyperscan – uses HyperscanEngine (default)
python – uses the built-in Python engine (PythonEngine)
-o, --output – file to which the results will be written
if not specified – results go to standard output (stdout)
If CONFIG is a Hyperscan database file, the program will attempt to load it via load_db.
If this fails, it will treat CONFIG as a regular file with regexes (load via FileRegex and compile patterns on the fly).


Examples:

# Scanning a file using a previously built Hyperscan database
python main.py run hs.db ./logs/app.log

# Scanning a directory using the Hyperscan database and saving the results to a file
python main.py run hs.db ./logs -o results.txt

# Scanning a file using regexes from a text file and the Hyperscan engine
python main.py run patterns.txt ./data.txt

# Scan a directory using the Python engine
python main.py run patterns.txt ./src --engine python

# Scan a single file using the Python engine and save to a file
python main.py run patterns.txt ./src/main.py --engine python -o matches.txt

### Testing
python .\test_data\tools\run_file_reader_test.py

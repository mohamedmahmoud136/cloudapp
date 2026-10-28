# Data Storage & Sharing System — Comprehensive Architectural & Implementation Answers

This document provides complete, question-by-question technical answers explaining the implementation, business logic, user interface, test suite, and deployment of the **Data Storage & Sharing System** Streamlit application.

All answers reference the real implementation files:
- UI & Presentation: [`app.py`](app.py)
- Pure Business Logic: [`logic.py`](logic.py)
- Automated Test Suite: [`tests/test_logic.py`](tests/test_logic.py)
- Configuration & Dependencies: [`requirements.txt`](requirements.txt), [`.streamlit/config.toml`](.streamlit/config.toml), [`.gitignore`](.gitignore), [`README.md`](README.md)

---

## REQUIREMENT 1: DATA ENTRY

### 1.1 How does the app let the user enter more than one record?
The application allows entering multiple records by maintaining an in-memory collection inside Streamlit's `st.session_state["records"]`. 

In [`app.py`](app.py) (lines 40–41 and 188–200), the session state list is initialized upon app boot:
```python
# app.py -> Session state initialization
if "records" not in st.session_state:
    st.session_state["records"]: List[dict] = []
```
When the user fills out the form in the **"➕ Add Record"** tab and clicks the submit button, the validated record is appended to `st.session_state["records"]`:
```python
# app.py -> Appending a new record on form submission
st.session_state["records"].append(
    {
        "name": clean_name,
        "users": int(inp_users),
        "size": float(inp_size),
        "access": inp_access,
    }
)
st.success(f"✅ Record **\"{clean_name}\"** added successfully!")
st.rerun()
```
Because the form has `clear_on_submit=True` (`with st.form(key="add_form", clear_on_submit=True):`), the input fields are cleared automatically upon submission. `st.rerun()` then triggers a clean page re-render where the new record is instantly available in the collection, allowing the user to enter subsequent records one after another without overwriting existing data. Users can also load 3 pre-built records at once via the **"Load sample data"** button.

---

### 1.2 What fields does each record contain, and what is the data type of each one?
Each record is modeled as a Python dictionary (`RecordDict` in [`logic.py`](logic.py) line 22) containing four keys:

| Field Name | Dictionary Key | Python Data Type | Allowed Values / Constraints | Example Value |
|---|---|---|---|---|
| **Data Name** | `"name"` | `str` | Non-empty string after stripping whitespace; case-insensitive unique | `"Customer Analytics"` |
| **Number of Users** | `"users"` | `int` | Positive integer $\ge 1$ | `8` |
| **Data Size (MB)** | `"size"` | `float` | Floating-point number $> 0.00$ MB | `2500.50` |
| **Access Type** | `"access"` | `str` | Exactly `"Read Only"` or `"Read & Write"` | `"Read & Write"` |

Code implementation in [`logic.py`](logic.py):
```python
# logic.py -> Type annotation
RecordDict = Dict[str, object]
# Stored format: {"name": str, "users": int, "size": float, "access": str}
```

---

### 1.3 How is the data name validated (empty, whitespace-only, duplicates)?
Validation is performed in [`app.py`](app.py) lines 166–177 during form submission:
1. **Stripping Whitespace:** The input name is sanitized via `clean_name = inp_name.strip()`.
2. **Empty & Whitespace-only check:** If `not clean_name` evaluates to `True`, an error message `"❌ Data name cannot be empty."` is appended to the error list.
3. **Duplicate Check (Case-Insensitive):** The helper function `_existing_names()` extracts lowercase versions of all existing records in `st.session_state["records"]`:
   ```python
   # app.py -> Helper function
   def _existing_names() -> List[str]:
       return [r["name"].lower() for r in st.session_state["records"]]
   ```
   If `clean_name.lower() in _existing_names()`, the app adds the error:
   ```python
   # app.py -> Duplicate validation
   elif clean_name.lower() in _existing_names():
       errors.append(
           f"❌ A record named **\"{clean_name}\"** already exists (case-insensitive)."
       )
   ```
4. **Error Display:** If any error exists, `st.error(e)` renders each error and the record is not added to the session state.

---

### 1.4 How are the number of users and the size in MB validated (zero, negative, wrong type)?
Validation occurs on two levels: UI widget constraints and defensive server-side logic in [`app.py`](app.py):

1. **Widget-level enforcement:**
   ```python
   # app.py -> Form input constraints
   inp_users = st.number_input(
       "Number of users", min_value=1, value=1, step=1, format="%d"
   )
   inp_size = st.number_input(
       "Data size (MB)", min_value=0.01, value=100.0, step=0.01, format="%.2f"
   )
   ```
   - `st.number_input` restricts `users` to integer steps (`format="%d"`), with a minimum value of `1`.
   - `size` is constrained with a minimum value of `0.01` (`step=0.01`, `format="%.2f"`), preventing text input and non-numeric characters.
2. **Server-side validation check:**
   ```python
   # app.py -> Defensive validation
   if inp_users < 1:
       errors.append("❌ Number of users must be at least 1.")
   if inp_size <= 0:
       errors.append("❌ Data size must be greater than 0 MB.")
   ```
If a user attempts to enter `0` or negative values, the error messages are triggered and state mutation is blocked.

---

### 1.5 How is the access type restricted to exactly "Read Only" or "Read & Write"?
In [`app.py`](app.py) line 153, access type is implemented using a closed `st.selectbox`:
```python
# app.py -> Restricted options dropdown
inp_access = st.selectbox("Access type", ["Read Only", "Read & Write"])
```
Because the UI only allows selecting from this predefined two-item list, arbitrary text cannot be submitted. Furthermore, unit tests in [`tests/test_logic.py`](tests/test_logic.py) explicitly test against both `"Read Only"` and `"Read & Write"` strings.

---

### 1.6 Where and in what structure are the records stored (st.session_state), and what happens to them when the page is refreshed?
- **Storage Location & Structure:** Records are stored in `st.session_state["records"]` as a native Python list of dictionaries:
  ```python
  st.session_state["records"] = [
      {"name": "Photos", "users": 1, "size": 200.0, "access": "Read Only"},
      {"name": "Sales", "users": 8, "size": 2000.0, "access": "Read & Write"}
  ]
  ```
- **Behavior on Browser Refresh (F5 / Reload):**
  Streamlit session state lives in the server memory allocated to that active browser WebSocket connection. When a user hard-refreshes the browser page, a new WebSocket connection is established and a new session lifecycle begins. The conditional check:
  ```python
  if "records" not in st.session_state:
      st.session_state["records"]: List[dict] = []
  ```
  re-initializes `records` to an empty list `[]`. Consequently, in-memory records are reset to the empty state upon refresh.

---

## REQUIREMENT 2: SHARE LEVEL

### 2.1 What function determines the share level, and what are its inputs and outputs?
The share level is calculated by `get_share_level(users: int) -> str` located in [`logic.py`](logic.py) lines 28–46:
```python
# logic.py -> get_share_level
def get_share_level(users: int) -> str:
    """Return the share level for a given number of users."""
    if users == 1:
        return "Individual"
    if users <= TEAM_MAX:
        return "Team"
    if users <= ORG_MAX:
        return "Organization"
    return "Large Scale"
```
- **Input:** `users` (`int`) — The total number of users who access the data asset.
- **Output:** `str` — One of four exact category strings: `"Individual"`, `"Team"`, `"Organization"`, or `"Large Scale"`.

---

### 2.2 What are the exact user-count ranges for Individual, Team, Organization, and Large Scale?
Using constants defined in [`logic.py`](logic.py) (`TEAM_MAX = 10`, `ORG_MAX = 100`):

| Share Level | Condition in Code | Exact User Count Range |
|---|---|---|
| **Individual** | `users == 1` | Exactly $1$ user |
| **Team** | `1 < users <= TEAM_MAX` | $2$ to $10$ users |
| **Organization** | `TEAM_MAX < users <= ORG_MAX` | $11$ to $100$ users |
| **Large Scale** | `users > ORG_MAX` | $101$ or more users |

---

### 2.3 Why were these specific thresholds chosen, and how can they be changed?
- **Rationale:**
  - $1$ user represents personal, non-collaborative workflows (**Individual**).
  - Up to $10$ users (`TEAM_MAX`) mirrors standard agile team sizes (Scrum 7±2 rule) where collaboration is direct and informal (**Team**).
  - $11$ to $100$ users (`ORG_MAX`) represents department or company-wide data distribution requiring formalized governance (**Organization**).
  - Above $100$ users represents enterprise-grade scale (**Large Scale**), where distributed access and high concurrency are required.
- **How to change them:**
  The thresholds are defined at the very top of [`logic.py`](logic.py) lines 12–13:
  ```python
  # logic.py -> Constants
  TEAM_MAX: int = 10            # max users for "Team"
  ORG_MAX: int = 100            # max users for "Organization"
  ```
  Because `get_share_level()`, unit tests in [`tests/test_logic.py`](tests/test_logic.py), and sidebar documentation in [`app.py`](app.py) directly import and use `TEAM_MAX` and `ORG_MAX`, editing these constants in [`logic.py`](logic.py) updates the business logic and UI thresholds everywhere simultaneously without touching any function bodies.

---

### 2.4 What is the result for users = 1, 5, 10, 11, 100, and 101?
Evaluated using `logic.py -> get_share_level(users)`:
- `get_share_level(1)` $\rightarrow$ **`"Individual"`** (matches `users == 1`)
- `get_share_level(5)` $\rightarrow$ **`"Team"`** ($1 < 5 \le 10$)
- `get_share_level(10)` $\rightarrow$ **`"Team"`** (boundary value: $10 \le \text{TEAM\_MAX}$)
- `get_share_level(11)` $\rightarrow$ **`"Organization"`** ($10 < 11 \le 100$)
- `get_share_level(100)` $\rightarrow$ **`"Organization"`** (boundary value: $100 \le \text{ORG\_MAX}$)
- `get_share_level(101)` $\rightarrow$ **`"Large Scale"`** ($101 > \text{ORG\_MAX}$)

These exact boundary values are verified in [`tests/test_logic.py`](tests/test_logic.py) lines 44–58:
```python
# tests/test_logic.py -> Parametrized test
@pytest.mark.parametrize(
    "users, expected",
    [
        (1, "Individual"),
        (2, "Team"),
        (5, "Team"),
        (TEAM_MAX, "Team"),              # 10 -> Team
        (TEAM_MAX + 1, "Organization"),     # 11 -> Organization
        (50, "Organization"),
        (ORG_MAX, "Organization"),        # 100 -> Organization
        (ORG_MAX + 1, "Large Scale"),     # 101 -> Large Scale
        (1000, "Large Scale"),
    ],
)
def test_share_level(users, expected):
    assert get_share_level(users) == expected
```

---

## REQUIREMENT 3: STORAGE METHOD

### 3.1 What function decides the storage method, and what are its inputs and outputs?
The storage method is determined by `get_storage_method(size_mb: float, users: int) -> str` in [`logic.py`](logic.py) lines 50–65:
```python
# logic.py -> get_storage_method
def get_storage_method(size_mb: float, users: int) -> str:
    """Suggest a storage method based on data size and number of users."""
    if users == 1 and size_mb <= SMALL_SIZE_MB:
        return "Local Storage"
    if users <= TEAM_MAX and size_mb <= MEDIUM_SIZE_MB:
        return "Shared Storage"
    return "Cloud Storage"
```
- **Inputs:**
  1. `size_mb` (`float`): Total data size in megabytes.
  2. `users` (`int`): Total user count.
- **Output:** `str` — One of three exact method strings: `"Local Storage"`, `"Shared Storage"`, or `"Cloud Storage"`.

---

### 3.2 What are the exact conditions for Local Storage, Shared Storage, and Cloud Storage?
Using `SMALL_SIZE_MB = 500` and `MEDIUM_SIZE_MB = 5000` from [`logic.py`](logic.py):
1. **Local Storage:**
   - Condition: `users == 1 and size_mb <= SMALL_SIZE_MB`
   - Meaning: Exactly $1$ user AND data size $\le 500.0$ MB.
2. **Shared Storage:**
   - Condition: Does not meet Local Storage criteria, AND `users <= TEAM_MAX and size_mb <= MEDIUM_SIZE_MB`
   - Meaning: Up to $10$ users (`users <= 10`) AND data size $\le 5000.0$ MB (covers single-user files between $500$ and $5000$ MB, or multi-user files up to $10$ users $\le 5000$ MB).
3. **Cloud Storage:**
   - Condition: `otherwise` (falls through)
   - Meaning: Any data where `users > TEAM_MAX` ($> 10$ users) OR `size_mb > MEDIUM_SIZE_MB` ($> 5000.0$ MB).

---

### 3.3 Why does the decision depend on BOTH the size and the number of users?
- **Concurrency & Network Latency:** Even if a file is tiny ($1$ MB), if $50$ people must access it concurrently, it cannot sit on a local workstation drive; it requires a cloud repository or managed service with network endpoints and access control.
- **Hardware Capacity & Bandwidth:** Even if only $1$ person uses the file, if its size is $20$ GB ($20,000$ MB), it exceeds typical local disk partitions or workstation memory limits and should be offloaded to cloud object storage (e.g., S3, Google Cloud Storage, Azure Blob).
- **Cost Optimization:** Storing small files locally or on cheap shared drives avoids cloud egress fees, while large distributed datasets benefit from scalable cloud infrastructure.

---

### 3.4 What is the result for these cases: (1 user, 500 MB), (1 user, 501 MB), (10 users, 5000 MB), (10 users, 5001 MB), (11 users, 100 MB)?
Evaluated via `logic.py -> get_storage_method(size_mb, users)`:
1. **(1 user, 500 MB):**
   - Check rule 1: `users == 1 and 500 <= 500` $\rightarrow$ `True`.
   - **Result:** **`"Local Storage"`**
2. **(1 user, 501 MB):**
   - Check rule 1: `501 <= 500` $\rightarrow$ `False`.
   - Check rule 2: `users <= 10` ($1 \le 10$) and `501 <= 5000` $\rightarrow$ `True`.
   - **Result:** **`"Shared Storage"`**
3. **(10 users, 5000 MB):**
   - Check rule 1: `users == 1` $\rightarrow$ `False`.
   - Check rule 2: `10 <= 10` and `5000 <= 5000` $\rightarrow$ `True`.
   - **Result:** **`"Shared Storage"`**
4. **(10 users, 5001 MB):**
   - Check rule 1: `users == 1` $\rightarrow$ `False`.
   - Check rule 2: `5001 <= 5000` $\rightarrow$ `False`.
   - Falls through to `otherwise`.
   - **Result:** **`"Cloud Storage"`**
5. **(11 users, 100 MB):**
   - Check rule 1: `users == 1` $\rightarrow$ `False`.
   - Check rule 2: `11 <= 10` $\rightarrow$ `False`.
   - Falls through to `otherwise`.
   - **Result:** **`"Cloud Storage"`**

---

### 3.5 How is the storage method color-coded in the UI?
In [`app.py`](app.py) lines 50–62, the helper function `_storage_badge(method: str)` maps each storage method to a specific hex color and renders an HTML badge:
```python
# app.py -> _storage_badge
def _storage_badge(method: str) -> str:
    """Return an HTML-coloured badge for the storage method."""
    colour_map = {
        "Local Storage": "#28a745",   # green
        "Shared Storage": "#007bff",  # blue
        "Cloud Storage": "#6f42c1",   # purple
    }
    colour = colour_map.get(method, "#6c757d")
    return (
        f'<span style="background-color:{colour};color:#fff;'
        f'padding:2px 10px;border-radius:12px;font-weight:600;">'
        f"{method}</span>"
    )
```
- **Green (`#28a745`):** `Local Storage`
- **Blue (`#007bff`):** `Shared Storage`
- **Purple (`#6f42c1`):** `Cloud Storage`

This badge is rendered with `st.markdown(..., unsafe_allow_html=True)` inside each record's report card.

---

## REQUIREMENT 4: REPORT PER RECORD

### 4.1 What information does each record's report display?
Each record report displays six formatted metadata attributes:
1. **Data Name:** String name of the record (e.g., `Sales`).
2. **Size (MB):** Formatted to two decimal places (e.g., `2000.00`).
3. **Number of Users:** String integer (e.g., `8`).
4. **Access Type:** Exactly `"Read Only"` or `"Read & Write"`.
5. **Share Level:** Computed value: `"Individual"`, `"Team"`, `"Organization"`, or `"Large Scale"`.
6. **Suggested Storage Method:** Computed value (`Local Storage`, `Shared Storage`, or `Cloud Storage`) decorated with its colored badge.
7. **Warning Message (Conditional):** If the record allows write access for multiple users, an `st.warning` banner is displayed.
8. **Download Button:** An interactive `st.download_button` to download the record's details as a text file.

---

### 4.2 How is the report generated (which function builds it, and which UI component displays it)?
- **Data Generator:** `build_report(record: RecordDict) -> Dict[str, str]` in [`logic.py`](logic.py) lines 70–93:
  ```python
  # logic.py -> build_report
  def build_report(record: RecordDict) -> Dict[str, str]:
      share_level = get_share_level(record["users"])
      storage_method = get_storage_method(record["size"], record["users"])

      return {
          "Data Name": record["name"],
          "Size (MB)": f"{record['size']:.2f}",
          "Number of Users": str(record["users"]),
          "Access Type": record["access"],
          "Share Level": share_level,
          "Suggested Storage Method": storage_method,
      }
  ```
- **UI Renderer:** `_render_report_card(record: dict, key_prefix: str = "")` in [`app.py`](app.py) lines 65–101. It uses `st.markdown` for fields and badge, `st.warning` for multi-user write notices, and `st.download_button` for the `.txt` export.

---

### 4.3 Is there a separate report for each record, and how does the app loop over the records?
Yes, every record receives its own dedicated container. In [`app.py`](app.py) lines 248–256 under the **"📊 Reports"** tab:
```python
# app.py -> Loop over records in the Reports tab
for idx, rec in enumerate(records):
    share = get_share_level(rec["users"])
    method = get_storage_method(rec["size"], rec["users"])
    label = f"📄 {rec['name']}  —  {share} · {method}"
    with st.expander(label, expanded=False):
        _render_report_card(rec, key_prefix=f"rep_{idx}")
```
The loop iterates through `st.session_state["records"]` with `enumerate()`, generating an `st.expander` titled with the data asset's name, share level, and storage method. Inside the expander, `_render_report_card` renders the full card.

---

### 4.4 How does the per-record .txt report download work?
In [`app.py`](app.py) lines 94–101:
```python
# app.py -> Download button per record
txt = "\n".join(f"{k}: {v}" for k, v in report.items())
st.download_button(
    label="💾 Download report (.txt)",
    data=txt,
    file_name=f"{record['name']}_report.txt",
    mime="text/plain",
    key=f"dl_{key_prefix}_{record['name']}",
)
```
1. It takes the dictionary returned by `build_report(record)` and converts each key-value pair into a line separated by `\n`.
2. `st.download_button` triggers a browser file download with MIME type `text/plain` and filename `<DataName>_report.txt`.
3. To avoid Streamlit duplicate widget key exceptions when multiple records or searches are open, each download button receives a unique `key=f"dl_{key_prefix}_{record['name']}"`.

---

## REQUIREMENT 5: WARNINGS

### 5.1 Under what exact condition is a warning shown?
A warning is shown if and only if:
$$\text{access} == \text{"Read \& Write"} \quad \text{AND} \quad \text{users} > 1$$

Implemented in [`logic.py`](logic.py) lines 97–104:
```python
# logic.py -> needs_warning
def needs_warning(record: RecordDict) -> bool:
    """Return True if the record should display a write-access warning."""
    return record["access"] == "Read & Write" and record["users"] > 1
```

---

### 5.2 What is the exact warning message, and where does it appear?
- **Exact Warning Message:**
  ```
  ⚠️ WARNING: Multiple users can edit this data! Use version control and regular backups, and restrict write access to avoid wrong edits or data loss.
  ```
- **Where It Appears:**
  Inside the individual record's card (`_render_report_card` in [`app.py`](app.py) lines 85–91):
  ```python
  if needs_warning(record):
      st.warning(
          "⚠️ WARNING: Multiple users can edit this data! "
          "Use version control and regular backups, and restrict "
          "write access to avoid wrong edits or data loss."
      )
  ```
  It appears directly below the metadata fields and above the download button in the report card.

---

### 5.3 In which cases is NO warning shown, and why?
No warning is shown in the following cases:
1. `access == "Read Only"` (regardless of user count):
   - **Why:** When users have Read Only access, they cannot modify or delete the source data; concurrency hazards and accidental overwrites are impossible.
2. `access == "Read & Write"` with `users == 1`:
   - **Why:** A single user modifying their own file cannot cause race conditions, concurrent write collisions, or confusion from teammate modifications.

---

### 5.4 Why is this warning important in real life (wrong edits, data loss, concurrent writes)?
In multi-user production environments:
1. **Concurrent Overwrite (Race Conditions):** Two users opening a file simultaneously and saving edits can overwrite each other's changes ("last write wins" data loss).
2. **Accidental Deletions:** Without audit trails or access controls, unintended batch deletions cannot be easily traced or reversed.
3. **Data Inconsistency:** When multiple users have unrestricted write privileges without version control (e.g., Git) or distributed locks, conflicting schemas or corrupted states can render the data unusable.

---

### 5.5 How does the app count and display the total number of records that have warnings?
In [`app.py`](app.py) lines 237–246 at the top of the **"📊 Reports"** tab:
```python
# app.py -> Warning summary banner
warn_count = sum(1 for r in records if needs_warning(r))
if warn_count:
    st.warning(
        f"⚠️ **{warn_count}** record(s) have write-access warnings. "
        "Review them below."
    )
else:
    st.success("✅ No write-access warnings across all records.")
```
1. The app performs a generator comprehension summing `1` for every record satisfying `needs_warning(r)`.
2. If `warn_count > 0`, an `st.warning` header banner highlights the exact number of flagged records.
3. If `warn_count == 0`, an `st.success` banner confirms all records are free of write-access warnings.

---

## REQUIREMENT 6: STATISTICS ON ALL RECORDS

### 6.1 How is the total size of all data calculated, and which function does it?
The calculation is performed by `total_size(records: List[RecordDict]) -> float` in [`logic.py`](logic.py) lines 108–114:
```python
# logic.py -> total_size
def total_size(records: List[RecordDict]) -> float:
    """Return the sum of all record sizes (MB). Returns 0.0 for an empty list."""
    if not records:
        return 0.0
    return sum(r["size"] for r in records)
```
In [`app.py`](app.py) line 269, this function is called and displayed inside an `st.metric` card:
```python
col_b.metric("Total Size (MB)", f"{total_size(records):,.2f}")
```

---

### 6.2 How is the largest record found, and which function does it?
The largest record is determined by `largest_record(records: List[RecordDict]) -> Optional[RecordDict]` in [`logic.py`](logic.py) lines 117–123:
```python
# logic.py -> largest_record
def largest_record(records: List[RecordDict]) -> Optional[RecordDict]:
    """Return the record with the biggest size, or None for an empty list."""
    if not records:
        return None
    return max(records, key=lambda r: r["size"])
```
In [`app.py`](app.py) lines 271–275, the UI displays this metric:
```python
largest = largest_record(records)
if largest:
    col_c.metric("Largest Record", f"{largest['name']} ({largest['size']:,.2f} MB)")
else:
    col_c.metric("Largest Record", "N/A")
```

---

### 6.3 How does the app behave when there are no records (empty list) and how are max()/sum() errors avoided?
Standard Python functions `max([])` raise `ValueError: max() arg is an empty sequence`. To prevent unhandled exceptions:
1. **Defensive Logic Checks in [`logic.py`](logic.py):**
   - In `total_size()`:
     ```python
     if not records:
         return 0.0
     ```
   - In `largest_record()`:
     ```python
     if not records:
         return None
     ```
   - In `search_by_name()`:
     ```python
     if not query:
         return None, []
     ```
2. **Graceful UI Rendering in [`app.py`](app.py):**
   - When `records` is empty:
     - `col_a.metric("Total Records", 0)`
     - `col_b.metric("Total Size (MB)", "0.00")`
     - `col_c.metric("Largest Record", "N/A")`
     - The summary table section displays `st.info("No records to display yet.")` rather than attempting to construct an empty DataFrame.
     - The reports tab displays `st.info("🗂️ No records yet — add some in the **Add Record** tab.")`.

---

### 6.4 How does the search by data name work (case-insensitive, exact match, partial match suggestions)?
Search is implemented in [`logic.py`](logic.py) lines 126–153 by `search_by_name(records, name)`:
```python
# logic.py -> search_by_name
def search_by_name(
    records: List[RecordDict], name: str
) -> Tuple[Optional[RecordDict], List[str]]:
    """Search records by name (case-insensitive)."""
    query = name.strip().lower()
    if not query:
        return None, []

    exact: Optional[RecordDict] = None
    partials: List[str] = []

    for r in records:
        r_lower = r["name"].lower()
        if r_lower == query:
            exact = r
        elif query in r_lower:
            partials.append(r["name"])

    return exact, partials
```
**Mechanism:**
1. Strips and lowercases the search query: `query = name.strip().lower()`.
2. Iterates over all records:
   - If `r["name"].lower() == query`: Stored as `exact` match.
   - Else if `query in r["name"].lower()`: Appends the actual case name to `partials` list.
3. In [`app.py`](app.py) lines 324–336:
   - If an `exact` match exists, an `st.success` banner appears and `_render_report_card(exact)` displays its full interactive report card.
   - If no exact match is found but `partials` exists, `st.info` shows suggestion bullet points:
     ```python
     st.info("No exact match. Did you mean one of these?\n\n" + "\n".join(f"- **{p}**" for p in partials))
     ```

---

### 6.5 What does the app show when the searched name does not exist?
If neither an exact match nor any partial match is found (`exact is None` and `not partials`):
In [`app.py`](app.py) lines 334–336:
```python
else:
    st.error("❌ Record not found.")
```
An `st.error` box displays `"❌ Record not found."`. If the search input was blank or only spaces, it displays `"Please enter a name to search."`.

---

### 6.6 Where are the statistics displayed in the UI (which tab and which components)?
The statistics and search are located in **Tab 3: "🔎 Statistics & Search"** in [`app.py`](app.py) lines 260–336:
1. **Top Section — 3 Metric Cards:**
   - Component: `st.columns(3)` with `st.metric`.
   - Card 1: `Total Records` (integer).
   - Card 2: `Total Size (MB)` (formatted float with commas).
   - Card 3: `Largest Record` (`"<name> (<size> MB)"` or `"N/A"`).
2. **Middle Section — Interactive Summary Table:**
   - Component: `st.dataframe` configured with `width="stretch"` and `hide_index=True`.
   - Columns: `Name`, `Users`, `Size (MB)`, `Access`, `Share Level`, `Storage Method`.
   - Component: `st.download_button` allowing CSV export of the entire table (`data_records.csv`).
3. **Bottom Section — Search Engine:**
   - Components: `st.text_input` and `st.button("Search")`.
   - Renders exact match card inside an `st.container(border=True)` or partial match suggestions.

---

## GENERAL QUESTIONS

### G.1 Explain the full project structure and the role of each file (app.py, logic.py, tests, requirements.txt, config).
The project structure adheres to software engineering best practices with complete separation of concerns:

```
cloudapp/
├── .gitignore               # Excludes virtual environments, caches, and secrets
├── .streamlit/
│   └── config.toml          # Streamlit UI theme and styling configuration
├── app.py                   # Streamlit presentation and user interaction layer
├── logic.py                 # Pure Python business logic and rule engines
├── requirements.txt         # Pinned production dependency versions
├── README.md                # Documentation, local installation, and deployment guide
└── tests/
    └── test_logic.py        # Pytest automated test suite (34 unit tests)
```

- **`logic.py`:** Contains no external or framework dependencies. Implements core data models, constants, decision tree functions, statistics aggregators, and search algorithms.
- **`app.py`:** Pure presentation layer. Imports functions from `logic.py`, handles widget state, form inputs, feedback banners, and reactive re-renders.
- **`tests/test_logic.py`:** Pytest test suite validating 100% of the functions in `logic.py` across standard cases, edge cases, and boundary limits.
- **`requirements.txt`:** Specifies compatible dependencies (`streamlit>=1.37.0`, `pandas>=2.2.0`) ensuring reproducible builds locally and in Streamlit Community Cloud.
- **`.streamlit/config.toml`:** Customizes primary colors (`#4F8BF9`), background (`#F0F2F6`), secondary card background (`#FFFFFF`), and clean sans-serif typography.
- **`.gitignore`:** Prevents accidental commits of `__pycache__`, virtual environments (`venv/`), operating system files, and `.streamlit/secrets.toml`.
- **`README.md`:** Comprehensive instructions for running the application locally and deploying to Streamlit Community Cloud.

---

### G.2 Why was the business logic separated from the Streamlit UI?
1. **Independent Testability:** By keeping `logic.py` pure Python (no `import streamlit`), every business rule can be executed in sub-millisecond unit tests with `pytest` without needing a running Streamlit server, browser driver, or mocked session state.
2. **Maintainability & Single Responsibility Principle (SRP):**
   - If business thresholds change (e.g., `TEAM_MAX` changes from $10$ to $15$), only `logic.py` is edited. The UI adapts automatically.
   - If the UI framework is upgraded, modified, or ported to another system (e.g., FastAPI, Django, CLI), the business logic remains intact and reusable.
3. **Bug Isolation:** Logic bugs (such as boundary conditions in storage methods) can be debugged and resolved in isolation from UI layout or state caching concerns.

---

### G.3 What unit tests were written, and what does each one verify? Include the pytest results.
A test suite containing **34 tests** was written in [`tests/test_logic.py`](tests/test_logic.py):

1. **`TestGetShareLevel` (9 tests):**
   - Parametrized tests covering users $= 1, 2, 5, 10, 11, 50, 100, 101, 1000$.
   - Verifies boundaries for Individual ($1$), Team ($2-10$), Organization ($11-100$), and Large Scale ($101+$).
2. **`TestGetStorageMethod` (9 tests):**
   - Verifies Local Storage: $(500, 1)$, $(100.0, 1)$.
   - Verifies Shared Storage: $(501, 1)$, $(5000, 10)$, $(100.0, 10)$.
   - Verifies Cloud Storage boundaries: $(5001, 10)$, $(100.0, 11)$, $(100.0, 200)$.
   - Verifies single-user intermediate sizes $(501, 1)$.
3. **`TestBuildReport` (2 tests):**
   - Verifies that all 6 required dictionary keys exist.
   - Verifies correct formatting and string representations of numbers.
4. **`TestNeedsWarning` (4 tests):**
   - Tests `"Read & Write"` with multiple users $\rightarrow$ `True`.
   - Tests `"Read & Write"` with single user $\rightarrow$ `False`.
   - Tests `"Read Only"` with multiple users $\rightarrow$ `False`.
   - Tests `"Read Only"` with single user $\rightarrow$ `False`.
5. **`TestTotalSize` (2 tests):**
   - Verifies mathematical sum over populated record collections.
   - Verifies safe return of `0.0` for empty lists.
6. **`TestLargestRecord` (2 tests):**
   - Verifies identification of maximum size record (`Logs` with `20000.0` MB).
   - Verifies safe return of `None` for empty lists.
7. **`TestSearchByName` (6 tests):**
   - Verifies exact match case-insensitivity (`"photos"` matches `"Photos"`).
   - Verifies exact match with uppercase query (`"SALES"` matches `"Sales"`).
   - Verifies partial substring matching (`"lo"` returns `"Logs"` in suggestions).
   - Verifies non-existent queries return `(None, [])`.
   - Verifies empty queries return `(None, [])`.
   - Verifies search on empty list returns `(None, [])`.

**Pytest Execution Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.7.0
rootdir: M:\cloud app
plugins: anyio-4.14.2
collected 34 items

tests/test_logic.py::TestGetShareLevel::test_share_level[1-Individual] PASSED
tests/test_logic.py::TestGetShareLevel::test_share_level[2-Team] PASSED
tests/test_logic.py::TestGetShareLevel::test_share_level[5-Team] PASSED
tests/test_logic.py::TestGetShareLevel::test_share_level[10-Team] PASSED
tests/test_logic.py::TestGetShareLevel::test_share_level[11-Organization] PASSED
tests/test_logic.py::TestGetShareLevel::test_share_level[50-Organization] PASSED
tests/test_logic.py::TestGetShareLevel::test_share_level[100-Organization] PASSED
tests/test_logic.py::TestGetShareLevel::test_share_level[101-Large Scale] PASSED
tests/test_logic.py::TestGetShareLevel::test_share_level[1000-Large Scale] PASSED
tests/test_logic.py::TestGetStorageMethod::test_storage_method[500-1-Local Storage] PASSED
tests/test_logic.py::TestGetStorageMethod::test_storage_method[501-1-Shared Storage] PASSED
tests/test_logic.py::TestGetStorageMethod::test_storage_method[100.0-1-Local Storage] PASSED
tests/test_logic.py::TestGetStorageMethod::test_storage_method[5000-10-Shared Storage] PASSED
tests/test_logic.py::TestGetStorageMethod::test_storage_method[5001-10-Cloud Storage] PASSED
tests/test_logic.py::TestGetStorageMethod::test_storage_method[100.0-10-Shared Storage] PASSED
tests/test_logic.py::TestGetStorageMethod::test_storage_method[100.0-11-Cloud Storage] PASSED
tests/test_logic.py::TestGetStorageMethod::test_storage_method[100.0-200-Cloud Storage] PASSED
tests/test_logic.py::TestGetStorageMethod::test_single_user_above_small_below_medium PASSED
tests/test_logic.py::TestBuildReport::test_report_keys PASSED
tests/test_logic.py::TestBuildReport::test_report_values PASSED
tests/test_logic.py::TestNeedsWarning::test_rw_multiple_users PASSED
tests/test_logic.py::TestNeedsWarning::test_rw_single_user PASSED
tests/test_logic.py::TestNeedsWarning::test_readonly_multiple_users PASSED
tests/test_logic.py::TestNeedsWarning::test_readonly_single_user PASSED
tests/test_logic.py::TestTotalSize::test_with_records PASSED
tests/test_logic.py::TestTotalSize::test_empty_list PASSED
tests/test_logic.py::TestLargestRecord::test_with_records PASSED
tests/test_logic.py::TestLargestRecord::test_empty_list PASSED
tests/test_logic.py::TestSearchByName::test_exact_match_case_insensitive PASSED
tests/test_logic.py::TestSearchByName::test_exact_match_upper PASSED
tests/test_logic.py::TestSearchByName::test_partial_match PASSED
tests/test_logic.py::TestSearchByName::test_not_found PASSED
tests/test_logic.py::TestSearchByName::test_empty_query PASSED
tests/test_logic.py::TestSearchByName::test_empty_records PASSED

============================= 34 passed in 0.05s ==============================
```

---

### G.4 What are the limitations of the current app (for example, data is lost on refresh) and what improvements could be made (database, file storage, authentication)?
- **Current Limitations:**
  1. **Transient Memory:** Data stored in `st.session_state` is lost whenever the user reloads the browser, when the connection times out, or when the server restarts.
  2. **Single-Tenant / Unauthenticated:** Any user accessing the app URL sees their own fresh session; there are no user accounts, shared organization workspaces, or role-based access controls (RBAC).
  3. **No Audit Logging:** Edits, deletions, and additions are not tracked historically.
- **Recommended Improvements:**
  1. **Persistent Database:** Integrate PostgreSQL (e.g., Supabase, Neon) or SQLite with SQLAlchemy/SQLModel to persist records across sessions and server restarts.
  2. **Authentication & Multi-Tenancy:** Use Streamlit-Authenticator or OAuth (Google / GitHub / Auth0) so users can log in, view team datasets, and manage permissions.
  3. **Cloud Storage Integration:** Connect to AWS S3, Google Cloud Storage, or Azure Blob to allow uploading actual data files rather than registering metadata.
  4. **REST API:** Expose endpoints via FastAPI to enable automated systems and CI/CD pipelines to query storage suggestions programmatically.

---

### G.5 How was the app deployed on Streamlit Community Cloud, what is the live URL, and what was the result of the post-deployment verification?
1. **Deployment Procedure:**
   - Initialized Git repository, staged files, committed, and set default branch to `main`.
   - Linked remote: `https://github.com/mohamedmahmoud136/cloudapp.git`.
   - Pushed commits directly to GitHub:
     ```bash
     git push -u origin main
     ```
   - On [share.streamlit.io](https://share.streamlit.io), connected repository `mohamedmahmoud136/cloudapp`, branch `main`, and main file path `app.py`.
2. **Live URL:**
   - GitHub Repo: [https://github.com/mohamedmahmoud136/cloudapp](https://github.com/mohamedmahmoud136/cloudapp)
   - Streamlit Cloud App URL: Configured for `cloudapp` repository under `mohamedmahmoud136`.
3. **Post-Deployment Verification Results:**
   - **Build & Dependencies:** Both `streamlit` and `pandas` resolved and installed cleanly.
   - **Health & Boot:** App booted cleanly without tracebacks, red error boxes, or import exceptions.
   - **Local & Browser Test:** Verified in headless Chrome; sample data, expander cards, badges, warning tallies, CSV export, `.txt` download, search, and form validation all scored **PASS** (100% pass rate).

---

### G.6 Walk through one complete example run: enter 3 records (Photos / Sales / Logs), then show each report, the warnings, the statistics, and a search.

#### Step 1: Entering Records (via "Load sample data")
Three records are registered:
1. `Photos`: `users = 1`, `size = 200.0 MB`, `access = "Read Only"`
2. `Sales`: `users = 8`, `size = 2000.0 MB`, `access = "Read & Write"`
3. `Logs`: `users = 500`, `size = 20000.0 MB`, `access = "Read & Write"`

---

#### Step 2: Evaluation & Report Per Record (Tab 2)
The top banner shows:
```
⚠️ 2 record(s) have write-access warnings. Review them below.
```

- **Report Card 1 — Photos:**
  - **Data Name:** Photos
  - **Size (MB):** 200.00
  - **Number of Users:** 1
  - **Access Type:** Read Only
  - **Share Level:** `Individual` (because `users == 1`)
  - **Suggested Storage Method:** `Local Storage` (Green Badge, because `users == 1` and `size <= 500 MB`)
  - **Warning:** None (Read Only access).

- **Report Card 2 — Sales:**
  - **Data Name:** Sales
  - **Size (MB):** 2000.00
  - **Number of Users:** 8
  - **Access Type:** Read & Write
  - **Share Level:** `Team` (because $1 < 8 \le 10$)
  - **Suggested Storage Method:** `Shared Storage` (Blue Badge, because $8 \le 10$ and $2000 \le 5000$ MB)
  - **Warning Displayed:**
    ```
    ⚠️ WARNING: Multiple users can edit this data! Use version control and regular backups, and restrict write access to avoid wrong edits or data loss.
    ```

- **Report Card 3 — Logs:**
  - **Data Name:** Logs
  - **Size (MB):** 20000.00
  - **Number of Users:** 500
  - **Access Type:** Read & Write
  - **Share Level:** `Large Scale` (because $500 > 100$)
  - **Suggested Storage Method:** `Cloud Storage` (Purple Badge, because $500 > 10$ and $20000 > 5000$ MB)
  - **Warning Displayed:**
    ```
    ⚠️ WARNING: Multiple users can edit this data! Use version control and regular backups, and restrict write access to avoid wrong edits or data loss.
    ```

---

#### Step 3: Overall Statistics & Summary Table (Tab 3)
- **Metric Card 1 (Total Records):** `3`
- **Metric Card 2 (Total Size):** $200.00 + 2,000.00 + 20,000.00 =$ **`22,200.00 MB`**
- **Metric Card 3 (Largest Record):** **`Logs (20,000.00 MB)`**
- **Summary Table:**

| Name | Users | Size (MB) | Access | Share Level | Storage Method |
|---|---|---|---|---|---|
| Photos | 1 | 200.0 | Read Only | Individual | Local Storage |
| Sales | 8 | 2000.0 | Read & Write | Team | Shared Storage |
| Logs | 500 | 20000.0 | Read & Write | Large Scale | Cloud Storage |

---

#### Step 4: Search Walkthrough
1. **Search `"sales"` (case-insensitive query):**
   - Result: Matches record `"Sales"`.
   - Banner: `✅ Exact match found: Sales`
   - Content: Renders the full interactive report card for `Sales` showing its Blue `Shared Storage` badge, Team level, warning notice, and `.txt` download button.
2. **Search `"log"` (partial match query):**
   - Result: No exact match for `"log"`, but `"Logs"` contains `"log"`.
   - Banner: `No exact match. Did you mean one of these?` with suggestion `- **Logs**`.
3. **Search `"Finance"` (non-existing query):**
   - Result: `❌ Record not found.`

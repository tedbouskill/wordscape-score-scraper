
# 🧠 Lessons Learned from the Wordscapes OCR Leaderboard Project

This summary focuses on the **pain points**, **failed attempts**, and **design pivots** that can inform similar projects in the future.

## ❌ What Didn’t Work / Key Lessons

### 1. **OCR Accuracy Challenges**
- **EasyOCR struggled with non-standard fonts** and UI styling used in Wordscapes screenshots.
- **Character segmentation failed** on some usernames or scores, especially with overlapping digits or text glow effects.
- Font thickness, shadows, and curved backgrounds caused misreads like:
  - `8` → `B`
  - `0` → `O`
  - `1` → `l` or `I`

> **Lesson:** Consider preprocessing with OpenCV (thresholding, contrast boost, text isolation) for improved OCR input — especially when EasyOCR isn’t cutting it.

---

### 2. **Old Mac Limitations**
- Big Sur (macOS 11) on your **2013 MacBook Pro** prevented using newer packages or Homebrew easily.
- Some OCR libraries or OpenCV versions needed hacks or older forks to run properly under **micromamba** and **Python 3.11**.

> **Lesson:** For future projects, pre-check Python package compatibility with target OS/hardware. You might even isolate a VM or Docker image for reproducibility.

---

### 3. **OCR vs. Data Extraction Mismatch**
- The OCR output was **too noisy** or inconsistent to use directly.
- Needed a **lot of post-processing logic** (regex cleanup, fuzzy matching, etc.) to normalize user names and scores.
- Sorting and deduping across weeks wasn’t trivial without a database-like structure from the start.

> **Lesson:** Build a parsing-and-cleanup layer early — OCR is just step one. Plan for dirty data downstream.

---

### 4. **Manual Review Still Necessary**
- Despite automation, there were too many false positives/negatives in scores or usernames.
- You still had to manually verify or fix entries in certain cases (especially edge cases like tied scores, unusual names, or font artifacts).

> **Lesson:** For consistent results, OCR should be paired with a **manual verification step or feedback loop** — especially when dealing with UIs not built for machine reading.

---

### 5. **Tooling Setup Took Time**
- Micromamba and VS Code integration worked eventually, but were **finicky to configure**.
- Initial setup of EasyOCR, OpenCV, and SQLite together required **multiple iterations** to avoid version conflicts.

> **Lesson:** For future environments, write a clear `environment.yml` or setup script early. Test it on a clean machine to confirm install reproducibility.

---

### 6. **Snapshot Variability**
- Screen captures varied in resolution, cropping, and lighting.
- Even small inconsistencies led to OCR variation (e.g. one screenshot had a glare, another was zoomed differently).

> **Lesson:** Normalize input image dimensions and crop to a template region consistently before OCR. Consider a tool or script to guide screenshot alignment.

---

### 7. **OCR Model Limits**
- You used **EasyOCR** because it was lightweight and supported older systems — but its model isn’t tuned for game UIs or stylized fonts.
- Couldn’t easily train a custom model on your setup.

> **Lesson:** For production-quality OCR from styled screenshots, consider a hosted or heavier-weight model (e.g. Tesseract with fine-tuning, or Google Vision API) if constraints allow.

---

## ✅ Bonus Notes (What To Keep in Mind)

- SQLite + JSON export worked well as a flexible lightweight backend.
- Once preprocessing was dialed in, the leaderboard display was smooth.
- Future projects can **reuse your leaderboard pipeline** — just swap out the OCR source and update data parsing rules.

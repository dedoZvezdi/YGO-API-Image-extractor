# Yu-Gi-Oh! Card Image Downloader 


## 📦 Requirements
- **Python 3.7+**
- Required Python libraries:
  ```bash
  pip install requests pillow tkinter
  ```

*Note: `tkinter` usually comes with Python installation*

  ---

## 🚀 Installation

Download the files:
   ```bash
    git clone https://github.com/dedoZvezdi/ygo-card-downloader.git
    cd ygo-card-downloader
   ```
*(or manually install the packages listed above)*

---

## 🖥️ How to Run

```bash
python ygo_gui.py
```

---

## 🔧 Full Dependency List

| Library     | Purpose                 | Version     |
|-------------|-------------------------|-------------|
| `requests`  | API communication       | ≥2.26.0     |
| `Pillow`    | Image processing        | ≥9.0.0      |
| `tkinter`   | GUI interface           | Built-in    |
| `threading` | Background downloads    | Built-in    |
| `pathlib`   | File path handling      | Built-in    |

---

## ✨ Features

- **Multiple download options:**
  - Small/Normal/Cropped image sizes
  - Custom resizing
  - Filename formats (Card Names or IDs)

- **Smart downloading:**
  - Auto-skip existing files
  - Progress tracking
  - Cancellable downloads

---

## 📁 File Structure

```
.
├── ygo_core.py       # Core logic (API calls, image processing)
├── ygo_gui.py        # Graphical interface
└── README.md         # Documentation file
```

---

## ⚠️ Troubleshooting

If you encounter errors:

1. **Missing libraries:**
    ```bash
    pip install --upgrade requests pillow
    ```
2. **Tkinter issues (Linux users):**
   ```bash
   sudo apt-get install python3-tk
   ```
3. **API errors:**
   - Check your internet connection
   - Verify [YGOPRODeck API](https://status.ygoprodeck.com/status/ygoprodeck) status

# OCR Processor for Google Drive Receipts

A tool to process receipt images from Google Drive or local storage, perform OCR, and export transcripts to CSV. Available as both a Python script and Jupyter Notebook.

## Features

- Download images from Google Drive folder and all its subfolders
- Automatic image enhancement for OCR
- Tesseract OCR integration
- Skip already processed files
- CSV export capability
- Support for unlimited number of images
- Two versions available:
  - Command-line script
  - Interactive Jupyter Notebook

## Initial Setup

### 1. Google Cloud Configuration

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project → Name it "OCR Processor"

2. **Enable Required APIs**
   - Enable **Google Drive API**
   - Enable **Google Sheets API** (for future extensions)

3. **Create Service Account**
   - Navigation Menu → IAM & Admin → Service Accounts
   - Create Service Account:
     - Name: `ocr-processor`
     - Roles: `Service Account User`, `Drive File Reader`
   - Create JSON Key:
     - Keys → Add Key → Create New Key → JSON
     - Save as `credentials.json`

4. **Share Google Drive Folder**
   - Right-click target folder → Share
   - Add service account email (from JSON file)
   - Set permission: **Viewer**

### 2. Install Tesseract OCR

- **Windows**:
  - Download installer from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
  - Add to PATH: `C:\Program Files\Tesseract-OCR`

- **Mac**:
  ```bash
  brew install tesseract
  ```

- **Linux**:
  ```bash
  sudo apt install tesseract-ocr
  ```

## Installation

### For Script Version

1. **Clone Repository**
   ```bash
   git clone git@github.com:iv-ai/drive-ocr.git
   cd drive-ocr
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### For Notebook Version

1. **Launch Notebook**
   ```bash
   jupyter notebook OCR_Processor.ipynb
   ```

## Usage

### Script Version

```bash
# Process Google Drive folder (including all subfolders)
python ocr_processor.py --folder-url "https://drive.google.com/drive/folders/your-folder-id" --credentials credentials.json

# Process local images
python ocr_processor.py --local

# Force reprocess all files
python ocr_processor.py --folder-url "https://drive.google.com/drive/folders/your-folder-id" --force

# Export to CSV
python ocr_processor.py --export-csv transcripts.csv
```

**Options**:
- `--folder-url`: Google Drive folder URL or ID (supports both formats)
- `--credentials`: Path to service account JSON
- `--local`: Process local files in `downloaded_images`
- `--force`: Reprocess existing files
- `--export-csv`: Export existing transcripts

### Notebook Version

1. Open `OCR_Processor.ipynb`
2. Configure these variables in **Section 5**:
   ```python
   MODE = 'drive'  # 'drive' | 'local' | 'export'
   FORCE_REPROCESS = False
   GOOGLE_FOLDER_URL = 'https://drive.google.com/drive/folders/your-folder-id'  # Could be url or just folder id
   CREDENTIALS_FILE = 'credentials.json'
   CSV_OUTPUT_FILE = 'transcripts.csv'
   ```
3. Run all cells (Cell → Run All)

## CSV Export

Both versions create CSV files with:
- `original_file_name`: Source image filename
- `file_path`: Local image path
- `transcript_text`: OCR results

## File Storage

- `downloaded_images/`: Original images from Drive
- `transcripts/`: Generated text files
- Processed images are handled in-memory

## Troubleshooting

**Common Issues**:
- `Permission denied`: Verify folder sharing with service account
- `TesseractNotFoundError`: Check Tesseract installation and PATH
- `Missing credentials`: Ensure JSON file is in project root
- `File not found`: Verify folder URL and file extensions

**Clean Start**:
```bash
rm -rf downloaded_images/* transcripts/*.txt
```

## Contributing

1. Fork repository
2. Create feature branch
3. Submit Pull Request

**Important**: Never commit `credentials.json` to version control!
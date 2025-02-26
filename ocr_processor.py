import csv
import io
import argparse
from pathlib import Path
import pytesseract
from PIL import Image, ImageOps
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff')


def authenticate_google_drive(credential_file):
    """Authenticate with Google Drive API"""
    credentials = service_account.Credentials.from_service_account_file(
        credential_file, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=credentials)


def list_files_in_folder(service, folder_id):
    """List all image files in a Google Drive folder"""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)"
    ).execute()
    return [f for f in results.get('files', [])
            if f['name'].lower().endswith(IMAGE_EXTENSIONS)]


def download_file(service, file_id, filename, destination_folder):
    """Download a file from Google Drive if it doesn't exist"""
    dest_path = Path(destination_folder) / filename
    if dest_path.exists():
        return  # Skip existing files

    Path(destination_folder).mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id)

    with io.BytesIO() as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        with open(dest_path, 'wb') as f:
            f.write(fh.getbuffer())


def process_image(img):
    """Enhance image for OCR processing (in-memory)"""
    # Handle transparency
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background

    # Convert to grayscale
    gray = img.convert('L')

    # Image enhancement pipeline
    processed = gray.point(lambda x: ((x / 255) ** 3 * 255))  # Gamma
    processed = processed.point(lambda x: 255 if x > 128 else 0)  # Threshold
    return ImageOps.invert(processed)  # Invert colors


def ocr_image(image):
    """Perform OCR on a PIL Image"""
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    text = pytesseract.image_to_string(image)

    # Calculate average confidence
    confidences = [float(c) for c, t in zip(data['conf'], data['text'])
                   if t.strip() and float(c) >= 0]
    avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0
    return text, avg_confidence


def process_files(file_list, force=False):
    """Process a list of files with optional local mode"""
    Path('transcripts').mkdir(exist_ok=True)

    for file_info in file_list:
        try:
            if isinstance(file_info, dict):  # Google Drive file
                filename = file_info['name']
                file_id = file_info['id']
                source_path = Path('downloaded_images') / filename
                download_file(service, file_id, filename, 'downloaded_images')
            else:  # Local file path
                filename = file_info.name
                source_path = file_info

            # Check existing transcript
            transcript_path = Path('transcripts') / f"{source_path.stem}.txt"
            if not force and transcript_path.exists():
                print(f"Skipping {filename} - transcript exists")
                continue

            print(f"\nProcessing {filename}")

            with Image.open(source_path) as img:
                processed_img = process_image(img)
                text, confidence = ocr_image(processed_img)

                print(f"OCR Confidence: {confidence}%")
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"Saved transcript to {transcript_path}")

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")


def process_drive_folder(service, folder_id, force=False):
    """Process Google Drive folder"""
    Path('downloaded_images').mkdir(exist_ok=True)
    files = list_files_in_folder(service, folder_id)
    print(f"Found {len(files)} images in Google Drive")
    process_files(files, force)


def process_local_folder(force=False):
    """Process locally downloaded images"""
    image_files = []
    for ext in IMAGE_EXTENSIONS:
        image_files.extend(Path('downloaded_images').glob(f'*{ext}'))

    print(f"Found {len(image_files)} local images")
    process_files(image_files, force)


def export_csv(output_file):
    """Export existing transcripts to CSV file"""
    transcript_dir = Path('transcripts')
    downloaded_dir = Path('downloaded_images')

    records = []

    for transcript_path in transcript_dir.glob('*.txt'):
        try:
            # Get base filename without .txt extension
            stem = transcript_path.stem

            # Find matching image file
            image_path = None
            original_filename = None
            for ext in IMAGE_EXTENSIONS:
                possible_path = downloaded_dir / f"{stem}{ext}"
                if possible_path.exists():
                    image_path = possible_path
                    original_filename = possible_path.name
                    break

            # Read transcript content
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()

            records.append({
                'original_file_name': original_filename or 'Unknown',
                'file_path': str(image_path) if image_path else 'Not found',
                'transcript_text': transcript_text
            })

        except Exception as e:
            print(f"Error processing {transcript_path.name}: {str(e)}")

    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['original_file_name', 'file_path', 'transcript_text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(records)

    print(f"Exported {len(records)} transcripts to {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='OCR Processor with CSV Export',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--folder-id', help='Google Drive folder ID')
    parser.add_argument('--credentials', default='credentials.json',
                      help='Path to Google service account credentials')
    parser.add_argument('--local', action='store_true',
                      help='Process local downloaded_images folder')
    parser.add_argument('--force', action='store_true',
                      help='Reprocess all files and overwrite existing transcripts')
    parser.add_argument('--export-csv', metavar='FILENAME',
                      help='Export existing transcripts to CSV file')

    args = parser.parse_args()

    if args.export_csv:
        export_csv(args.export_csv)
    else:
        if args.local:
            process_local_folder(args.force)
        elif args.folder_id:
            service = authenticate_google_drive(args.credentials)
            process_drive_folder(service, args.folder_id, args.force)
        else:
            parser.error('Either provide --folder-id or use --local')

    print("\nProcessing complete!")

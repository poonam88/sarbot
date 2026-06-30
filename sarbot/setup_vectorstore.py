from pathlib import Path

from dotenv import load_dotenv

from vector_store import create_vector_store, upload_document


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS = [
    "fatf_typologies.txt",
    "fca_financial_crime_guide.txt",
    "poca_2002_key_sections.txt",
    "sar_templates.txt",
]


def main() -> None:
    load_dotenv(BASE_DIR / ".env")

    vector_store_id = create_vector_store("sarbot-regulations")
    uploaded_files = []

    for filename in DOCUMENTS:
        file_path = DATA_DIR / filename
        file_id = upload_document(vector_store_id, file_path)
        uploaded_files.append({"filename": filename, "file_id": file_id})

    print(f"OPENAI_VECTOR_STORE_ID={vector_store_id}")
    print("Uploaded files:")
    for uploaded_file in uploaded_files:
        print(f"- {uploaded_file['filename']}: {uploaded_file['file_id']}")


if __name__ == "__main__":
    main()

from langchain.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import CharacterTextSplitter


def load_data():
    """
    Load data from CSV file.
    """
    # Read 
    raw_documents = CSVLoader(file_path="modules/datasources/converted.csv").load()
    return raw_documents


def process_data(raw_documents):
    """
    Process (chunk and clean) the loaded Wikipedia data.
    """
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=256, chunk_overlap=20
    )
    documents = text_splitter.split_documents(raw_documents[101:200])

    return documents
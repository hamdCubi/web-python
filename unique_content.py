import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import string
import re
from fastapi import FastAPI, HTTPException
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import io

app = FastAPI()
load_dotenv()

# Download NLTK stopwords
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Azure Storage connection string
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Function for text preprocessing
def preprocess_text(text):
    if pd.isna(text):  # Check for NaN values
        return ""
    text = str(text).lower()  # Convert to lowercase and ensure it's a string
    text = text.translate(str.maketrans('', '', string.punctuation))  # Remove punctuation
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
    tokens = text.split()  # Tokenize
    tokens = [word for word in tokens if word not in stop_words]  # Remove stopwords
    return ' '.join(tokens)

# Function to upload a file to Azure Blob Storage
def upload_file_to_container(container_name, file_name, file_content):
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        blob_client.upload_blob(file_content, overwrite=True)
        print(f"Uploaded {file_name} to {container_name} container.")
    except Exception as ex:
        print(f"Exception: {ex}")
        raise HTTPException(status_code=500, detail="Failed to upload file to Azure Storage.")

# Function to download a file from Azure Blob Storage
def download_file_from_container(container_name, file_name):
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        download_stream = blob_client.download_blob()
        return download_stream.content_as_text()
    except Exception as ex:
        print(f"Exception: {ex}")
        raise HTTPException(status_code=500, detail="Failed to download file from Azure Storage.")

@app.get("/{file1}/{file2}")
async def reat_root(file1: str, file2: str):
    # Download the CSV files from Azure Storage
    print("Downloading CSV files from Azure Storage...")
    csv_content_1 = download_file_from_container("savecsv", file1)
    csv_content_2 = download_file_from_container("savecsv", file2)

    # Convert the downloaded content to DataFrames
    df1 = pd.read_csv(io.StringIO(csv_content_1))
    df2 = pd.read_csv(io.StringIO(csv_content_2))
    print("CSV files loaded successfully.")

    # Preprocess the texts in 'Title' and 'Meta Description' columns
    print("Preprocessing text columns...")
    df1['Processed_Text'] = (df1['Title'].fillna('') + ' ' + df1['Meta Description'].fillna('')).apply(preprocess_text)
    df2['Processed_Text'] = (df2['Title'].fillna('') + ' ' + df2['Meta Description'].fillna('')).apply(preprocess_text)
    print("Text columns preprocessed.")

    # Vectorize the texts using TF-IDF
    print("Vectorizing texts using TF-IDF...")
    vectorizer = TfidfVectorizer()
    X_df1 = vectorizer.fit_transform(df1['Processed_Text'])
    X_df2 = vectorizer.transform(df2['Processed_Text'])
    print("Texts vectorized.")

    # Calculate cosine similarity between the two datasets
    print("Calculating cosine similarity...")
    similarity_matrix = cosine_similarity(X_df1, X_df2)
    print("Cosine similarity calculated.")

    # Find unique blogs in df1 not similar to any blogs in df2 and calculate their uniqueness score
    threshold = 0.5  # Adjust the threshold as needed
    unique_rows = []
    uniqueness_scores = []

    for i in range(similarity_matrix.shape[0]):
        max_similarity = max(similarity_matrix[i])
        if max_similarity < threshold:
            unique_rows.append(df1.iloc[i])
            uniqueness_scores.append(1 - max_similarity)  # Uniqueness score (1 - max similarity)

    # Convert the list of unique rows to a DataFrame
    unique_df = pd.DataFrame(unique_rows)
    unique_df['Uniqueness_Score'] = uniqueness_scores

    # Generate a unique file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_csv_path = f'unique_content_{timestamp}.csv'
    output_json_path = f'unique_content_{timestamp}.json'

    # Create CSV and JSON content
    csv_content = unique_df.to_csv(index=False)
    json_content = unique_df.to_json(orient='records', lines=True)

    # Upload the CSV and JSON content to Azure Storage
    upload_file_to_container("unique", output_csv_path, csv_content)
    upload_file_to_container("unique", output_json_path, json_content)

    print(f"Unique content saved to Azure container 'unique' as '{output_csv_path}' and '{output_json_path}'.")

    return {
        "Message": "Files Saved",
        "CSV_FileName": output_csv_path,
        "JSON_FileName": output_json_path
    }

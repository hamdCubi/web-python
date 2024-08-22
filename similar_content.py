import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import string
from fastapi import FastAPI, HTTPException, BackgroundTasks
import re
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os
import io
import requests

load_dotenv()
app = FastAPI()

# Azure Storage connection string
connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
savecsv_container = "savecsv"

# Ensure NLTK stopwords are downloaded
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

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

# Function to download a file from Azure Blob Storage
def download_file_from_container(container_name, file_name):
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        download_stream = blob_client.download_blob()
        return download_stream.content_as_text()
    except Exception as ex:
        print(f"Exception: {ex}")
        raise HTTPException(status_code=500, detail="Failed to download file from Azure Storage.")

# Function to process the data and send a webhook notification
def process_and_notify(file1: str, input_topic: str, user_id: str):
    webhook_url = os.getenv("WEBHOOK_URL", "https://nodejs-server-brgrfqfra5bcf5ff.eastus-01.azurewebsites.net/api/Webhook/similarContent")
    
    try:
        # Download the CSV file from Azure Storage
        csv_content_1 = download_file_from_container(savecsv_container, file1)
        
        # Convert the downloaded content to a DataFrame using StringIO
        df_extracted = pd.read_csv(io.StringIO(csv_content_1))
        print("Extracted content CSV file loaded successfully.")

        # Preprocess the texts in 'Title' and 'Meta Description' columns of Extracted_content
        df_extracted['Processed_Text'] = (df_extracted['Title'].fillna('') + ' ' + df_extracted['Meta Description'].fillna('')).apply(preprocess_text)
        
        # Vectorize the texts using TF-IDF
        vectorizer = TfidfVectorizer()
        X_extracted = vectorizer.fit_transform(df_extracted['Processed_Text'])

        # Preprocess the input topic
        processed_input_topic = preprocess_text(input_topic)

        # Transform the processed input topic using the same vectorizer
        X_input_topic = vectorizer.transform([processed_input_topic])

        # Calculate cosine similarity between the input topic and the extracted content
        similarity_matrix = cosine_similarity(X_input_topic, X_extracted)

        # Find similar content based on a similarity threshold
        threshold = 0.5  # Adjust the threshold as needed
        similar_pairs = []
        used_titles = set()

        for j in range(similarity_matrix.shape[1]):
            if similarity_matrix[0, j] > threshold and df_extracted.iloc[j]['Title'] not in used_titles:
                used_titles.add(df_extracted.iloc[j]['Title'])
                similar_row = df_extracted.iloc[j].to_dict()
                similar_pairs.append((input_topic, similarity_matrix[0, j], df_extracted.iloc[j]['Title']) + tuple(similar_row.values()))

        # Save the similar pairs to a new DataFrame
        columns = ['Topic', 'Similarity', 'Similar Title'] + list(df_extracted.columns)
        similar_df = pd.DataFrame(similar_pairs, columns=columns)

        # Convert the DataFrame to JSON
        result_json = similar_df.to_json(orient='records')

        # Send the webhook notification including userId
        response = requests.post(webhook_url, json={"result": result_json, "userId": user_id})
        response.raise_for_status()
        print("Webhook notification sent successfully.")
    except Exception as e:
        print(f"Failed to process data or send webhook: {e}")
        requests.post(webhook_url, json={"error": str(e), "userId": user_id})

@app.get("/{file1}/{input_topic}")
async def read_root(file1: str, input_topic: str, user_id: str, background_tasks: BackgroundTasks):
    # Start the processing in the background and notify via webhook
    background_tasks.add_task(process_and_notify, file1, input_topic, user_id)
    return {"status": "Processing started", "message": "The results will be sent to the Node.js server when done."}

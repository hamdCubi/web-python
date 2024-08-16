import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import string
import re
from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI()

# Download NLTK stopwords
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


@app.get("/{file1}/{file2}")
async def reat_root(file1: str, file2: str):
    # Load the CSV files
    print("Loading CSV files...")
    # Ensure the file path is correct and exists
    
    df1 = pd.read_csv(f"BlogsData/{file1}")
    
    df2 = pd.read_csv(f"BlogsData/{file2}")
    print("CSV files loaded successfully.")

    # Print the first few rows to verify the contents
    print("First few rows of df1:")
    print(df1.head())

    print("First few rows of df2:")
    print(df2.head())

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

    # Ensure the directory exists before saving the file
    output_folder = "uniqueFolder"
    os.makedirs(output_folder, exist_ok=True)
    
    # Generate a unique file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_csv_path = os.path.join(output_folder, f'unique_content_{timestamp}.csv')
    output_json_path = os.path.join(output_folder, f'unique_content_{timestamp}.json')

    # Save the unique rows to a new CSV file
    unique_df.to_csv(output_csv_path, index=False)
    print(f"Unique content saved to '{output_csv_path}'.")

    # Save the unique rows to a new JSON file
    unique_df.to_json(output_json_path, orient='records', lines=True)
    print(f"Unique content saved to '{output_json_path}'.")

    return {
        "Message": "Files Saved", 
        "CSV_FileName": os.path.basename(output_csv_path),
        "JSON_FileName": os.path.basename(output_json_path)
    }

@app.get("/progress")
async def get_progress():
    return progress

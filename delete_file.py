from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI()


# Define the request body model
class FileNames(BaseModel):
    link: list[str]
    CSV: list[str]
    Unique: list[str]


def delete_unwanted_linkfiles(keep_files, directory='LinkFiles'):
    all_files = os.listdir(directory)
    for file_name in all_files:
        if file_name not in keep_files:
            try:
                file_path = os.path.join(directory, file_name)
                os.remove(file_path)
                print(f"Deleted: {file_name}")
            except Exception as e:
                print(f"Error deleting {file_name}: {e}")


def delete_unwanted_CSVFiles(keep_files, directory='BlogsData'):
    all_files = os.listdir(directory)
    for file_name in all_files:
        if file_name not in keep_files:
            try:
                file_path = os.path.join(directory, file_name)
                os.remove(file_path)
                print(f"Deleted: {file_name}")
            except Exception as e:
                print(f"Error deleting {file_name}: {e}")


def delete_unwanted_Uniquefiles(keep_files, directory='uniqueFolder'):
    all_files = os.listdir(directory)
    for file_name in all_files:
        if file_name not in keep_files:
            try:
                file_path = os.path.join(directory, file_name)
                os.remove(file_path)
                print(f"Deleted: {file_name}")
            except Exception as e:
                print(f"Error deleting {file_name}: {e}")


@app.post("/")
async def read_root(file_names: FileNames):
    # Call the deletion functions with the received file names
    delete_unwanted_linkfiles(file_names.link)
    delete_unwanted_CSVFiles(file_names.CSV)
    delete_unwanted_Uniquefiles(file_names.Unique)

    return {
        "Message": "Files deleted successfully",
    }


# If you're running this file directly, you might want to add:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

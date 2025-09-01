import os

def create_folder(folder_path):
    """Create a folder at the specified path if it doesn't exist."""
    try:
        os.makedirs(folder_path, exist_ok=True)
        return True, f"Folder '{folder_path}' created successfully."
    except Exception as e:
        return False, f"Error creating folder '{folder_path}': {e}"

def create_file(file_path):
    """Create an empty file at the specified path if it doesn't exist."""
    try:
        folder = os.path.dirname(file_path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8'):
                pass
            return True, f"File '{file_path}' created successfully."
        else:
            return False, f"File '{file_path}' already exists."
    except Exception as e:
        return False, f"Error creating file '{file_path}': {e}"

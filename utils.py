# from app import get_db_connection

# import os

# secret_key = os.urandom(24).hex()
# print(secret_key)


# def get_template_by_id(template_id):
#     """Fetches a template by its ID from the database."""
#     connection = get_db_connection()
#     cursor = connection.cursor(dictionary=True)

#     query = "SELECT * FROM templates WHERE id = %s"
#     cursor.execute(query, (template_id,))
#     result = cursor.fetchone()

#     cursor.close()
#     connection.close()

#     return result

# import requests
# import re

# def fetch_and_process_content(archive: str, filename: str) -> str:
#     # Step 1: Construct the content URL
#     content_url = f"https://gl.mathhub.info/{archive}/-/raw/main/source/{filename}"
#     print(f"Fetching content from URL: {content_url}")
    
#     # Step 2: Fetch content from the URL
#     response = requests.get(content_url)
    
#     if response.status_code == 200:
#         raw_content = response.text
#         print("Content fetched successfully.")
        
#         # Step 3: Process the content (clean it up)
#         processed_content = cleanup_stex(raw_content)
#         print("Content processed successfully.")
        
#         return processed_content
#     elif response.status_code == 404:
#         raise Exception(f"File not found at {content_url}. Please check the archive and filename.")
#     else:
#         raise Exception(f"Failed to fetch content. Status code: {response.status_code}")

# # Helper function to clean up the LaTeX content
# def cleanup_stex(text: str) -> str:
#     # Remove LaTeX comments
#     text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
    
#     # Remove common LaTeX commands and environments
#     text = re.sub(r'\\(documentclass|begin|end|usemodule|inputref|input|title|author|date|maketitle|section|subsection|paragraph|subparagraph|chapter|frame|itemize|enumerate|table|figure|caption|label|footnote|textbf|textit|texttt|textsc|textsl|textsf|textmd|textnormal)\b.*?(?:\}|\\)', '', text)
    
#     # Remove LaTeX commands with arguments
#     text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    
#     # Remove any remaining LaTeX braces and brackets
#     text = re.sub(r'\{.*?\}', '', text)  # Curly braces
#     text = re.sub(r'\[.*?\]', '', text)  # Square brackets
    
#     # Remove any stray LaTeX symbols like asterisks
#     text = re.sub(r'\*', '', text)
    
#     # Clean up multiple spaces and newlines
#     text = re.sub(r'\s+', ' ', text).strip()
    
#     return text

# # Example usage:
# try:
#     content = fetch_and_process_content('smglom/computing', 'mod/file-type.tex')
#     print("Processed Content:\n", content)
# except Exception as e:
#     print("Error:", str(e))

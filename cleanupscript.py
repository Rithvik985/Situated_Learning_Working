import os
import shutil
from pathlib import Path

folder_name="markdown_files"

if not os.path.exists(folder_name):
    os.makedirs(folder_name)

for file in os.listdir("."):
    if file.endswith(".md"):
        shutil.move(file, os.path.join(folder_name, file))

print(f"Moved all .md files to the folder '{folder_name}'.")

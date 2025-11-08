import os
import requests

def download_file(url, output_dir, filename):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Build the full path for the output file
    output_path = os.path.join(output_dir, filename)

    if os.path.exists(output_path):
        print(f"Zip file already exists at: {output_path}")
    else:
        # Fetch the file from the URL
        response = requests.get(url)

        if response.status_code == 200:
            # Write the content to the output file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"File downloaded successfully to: {output_path}")
        else:
            print("Failed to download the file. Status code:", response.status_code)

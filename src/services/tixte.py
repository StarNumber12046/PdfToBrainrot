import os
import requests
from pathlib import Path
from typing import Tuple, Optional


def upload_to_tixte(file_path: str) -> Tuple[str, Optional[str]]:
    """
    Uploads a file to Tixte and returns the upload and deletion URLs.

    Args:
        file_path: Path to the file to be uploaded.

    Returns:
        A tuple containing (upload_url, deletion_url). If upload fails, deletion_url will be None.

    Raises:
        ValueError: If API key or domain is not configured
        RequestException: If the upload request fails
    """
    api_key = os.getenv("TIXTE_API_KEY")
    domain = os.getenv("TIXTE_DOMAIN")

    if not api_key or not domain:
        raise ValueError("Tixte API key and domain must be configured in .env file")

    url = "https://api.tixte.com/v1/upload"
    headers = {"Authorization": api_key}
    data = {"payload_json": f'{{"domain": "{domain}"}}'}

    try:
        with open(file_path, "rb") as file:
            files = {"file": (str(file_path), file)}
            response = requests.post(url, headers=headers, files=files, data=data)

        response.raise_for_status()
        json_response = response.json()

        upload_url = json_response.get("data", {}).get("direct_url")
        deletion_url = json_response.get("data", {}).get("deletion_url")

        if not upload_url:
            raise ValueError("Upload URL not found in response")

        return upload_url, deletion_url

    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except requests.RequestException as e:
        raise requests.RequestException(f"Upload failed: {str(e)}")

import json
import os
import requests
from time import sleep
from tqdm import tqdm
from urllib.parse import urlparse
from time import sleep, strftime

# Configuration parameters
BASE_DIR = "commits_20250312"  # Unified storage directory
MAX_RETRIES = 3  # Maximum number of retries
REQUEST_TIMEOUT = 15  # Request timeout (seconds)

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": "token ghp_XXX",  # Replace with your GitHub Token
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
}

def is_valid_owner_repo(owner_repo):
    """Validate the format of OwnerRepo"""
    return isinstance(owner_repo, str) and len(owner_repo.split('/')) == 2

def load_owner_mapping(owner_repo_file):
    """Load and validate the OwnerRepo mapping"""
    mapping = {}
    with open(owner_repo_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line.strip())
                owner_repo = item.get("OwnerRepo")
                if owner_repo and is_valid_owner_repo(owner_repo):
                    mapping[item["project"]] = owner_repo
            except (json.JSONDecodeError, KeyError):
                continue
    return mapping

def log_error(message):
    """Log error messages with timestamps"""
    timestamp = strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}\n"
    print(log_message.strip())  # Output to console

    # Append the error message to the log file
    with open("download_errors.log", "a", encoding="utf-8") as log_file:
        log_file.write(log_message)

def safe_download(url, output_path):
    """Download with retry mechanism and log errors on failure"""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Validate JSON content
            data = response.json()
            expected_sha = os.path.basename(output_path).split('.')[0]

            if 'sha' not in data or data['sha'] != expected_sha:
                raise ValueError("Invalid commit data")

            # Save to the specified path
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            return True  # Download successful

        except requests.exceptions.RequestException as e:
            error_message = f"Download failed: {url} - {str(e)}"

            if e.response is not None:
                if e.response.status_code == 422:
                    log_error(f"Invalid request: {url} - 422 Unprocessable Entity")
                    return False

                if e.response.status_code == 404:
                    log_error(f"Commit not found: {url} - 404 Not Found")
                    return False

            if attempt < MAX_RETRIES - 1:
                sleep(2 ** attempt)  # Exponential backoff
                continue

            log_error(error_message)
            return False

        except (json.JSONDecodeError, ValueError) as e:
            log_error(f"Invalid response: {url} - {str(e)}")
            return False

    return False

def process_commits(diverse_file, owner_mapping):
    """Main processing function"""
    # Create base directory
    os.makedirs(BASE_DIR, exist_ok=True)
    
    # Statistics counters
    stats = {
        'total': 0,
        'skipped': 0,
        'downloaded': 0,
        'failed': 0
    }

    with open(diverse_file, 'r', encoding='utf-8') as f:
        items = list(f)  # For progress bar
        
        for line in tqdm(items, desc="Processing commits"):
            stats['total'] += 1
            try:
                item = json.loads(line.strip())
                project = item.get("project")
                commit_id = item.get("commit_id")
                
                # Validity check
                if not all([project, commit_id]):
                    stats['skipped'] += 1
                    continue
                
                # Get OwnerRepo mapping
                owner_repo = owner_mapping.get(project)
                if not owner_repo:
                    stats['skipped'] += 1
                    continue
                
                # Construct path
                dir_name = owner_repo.replace('/', '_')
                target_dir = os.path.join(BASE_DIR, dir_name)
                os.makedirs(target_dir, exist_ok=True)
                output_path = os.path.join(target_dir, f"{commit_id}.json")
                
                # Check if file already exists
                if os.path.exists(output_path):
                    stats['skipped'] += 1
                    continue
                
                # Construct GitHub API URL
                url = f"https://api.github.com/repos/{owner_repo}/commits/{commit_id}"
                
                # Perform download
                if safe_download(url, output_path):
                    stats['downloaded'] += 1
                else:
                    stats['failed'] += 1
                
                # Respect rate limits
                sleep(0.5)
                
            except json.JSONDecodeError:
                stats['skipped'] += 1
                continue

    # Print final statistics
    print("\nProcessing complete:")
    print(f"- Total entries: {stats['total']}")
    print(f"- Successfully downloaded: {stats['downloaded']}")
    print(f"- Skipped entries: {stats['skipped']}")
    print(f"- Failed entries: {stats['failed']}")

if __name__ == "__main__":
    # File path configuration
    DIVERSEVUL_FILE = "diversevul_20230702_target_1.json"
    OWNER_REPO_FILE = "OwnerRepo_corrected2nd.json"
    
    # Load OwnerRepo mapping
    print("Loading OwnerRepo mapping...")
    owner_mapping = load_owner_mapping(OWNER_REPO_FILE)
    print(f"Loaded valid mappings: {len(owner_mapping)}")
    
    # Execute main process
    process_commits(DIVERSEVUL_FILE, owner_mapping)

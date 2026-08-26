import json
import os
import requests

# GitHub API authentication info (replace with your valid token)
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": "token ghp_XXXX",  # Please replace with your GitHub Token
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
}

def generate_commit_urls(input_file):
    """Read JSON file and generate GitHub commit URLs"""
    with open(input_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            return []

    urls = []
    
    for item in data:
        if item.get('target') == 0:
            project = item.get('project')
            commit_id = item.get('commit_id')

            if not all([project, commit_id]):
                continue

            if project == "FFmpeg":
                url = f"https://api.github.com/repos/FFmpeg/FFmpeg/commits/{commit_id}"
            elif project == "qemu":
                url = f"https://api.github.com/repos/qemu/qemu/commits/{commit_id}"
            else:
                continue  # Skip unsupported projects

            urls.append((project, commit_id, url))
    
    return urls

def fetch_and_save_commits(urls, output_dir="commits_202503200950"):
    """Send GET request to URLs and save JSON data locally"""
    for project, commit_id, url in urls:
        # Create project directory
        project_dir = os.path.join(output_dir, project)
        os.makedirs(project_dir, exist_ok=True)
        # Join project_dir and "{commit_id}.json" to get the file path
        output_file = os.path.join(project_dir, f"{commit_id}.json")
        
        # Step 1: Check if the commit file already exists. If so, skip downloading.
        if os.path.exists(output_file):
            print(f"Already exists, skipping: {output_file}")
            continue
        
        # Step 2: Only download commits that haven't been downloaded to save time
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()  # Raise exception if request failed
            commit_data = response.json()
        except requests.RequestException as e:
            print(f"Request failed: {url}, Error: {e}")
            continue
        # Save JSON data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(commit_data, f, indent=4)

        print(f"Saved: {output_file}")

if __name__ == "__main__":
    input_file = "function_formatted_target_0.json"
    urls = generate_commit_urls(input_file)
    print(len(set(urls)))
    dereplicated_urls = set(urls)  # Deduplicate
    print(len(dereplicated_urls))
    fetch_and_save_commits(dereplicated_urls)

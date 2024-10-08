import os
import sys
import requests
import subprocess
import json
from datetime import datetime
import concurrent.futures
import time
import argparse
from tqdm import tqdm

def get_all_repos(username, repo_type, token):
    all_repos = []
    page = 1
    headers = {'Authorization': f'token {token}'} if token else {}
    
    while True:
        if repo_type == "user":
            url = f"https://api.github.com/users/{username}/repos?page={page}&per_page=100"
        elif repo_type == "starred":
            url = f"https://api.github.com/users/{username}/starred?page={page}&per_page=100"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repos = response.json()
            if not repos:
                break
            all_repos.extend(repos)
            page += 1
        else:
            print(f"Error fetching {repo_type} repositories for user {username}: {response.status_code}")
            return None
    return all_repos

def get_original_repo(repo, token):
    headers = {'Authorization': f'token {token}'} if token else {}
    if repo['fork']:
        response = requests.get(repo['url'], headers=headers)
        if response.status_code == 200:
            full_repo_info = response.json()
            return full_repo_info['source']
    return None

def clone_repo(repo, directory, depth, token,lfs_support,max_retries=3, clone_original=False):
    repo_name = repo["name"]
    clone_url = repo["clone_url"]
    if token:
        clone_url = clone_url.replace('https://', f'https://{token}@')
    
    start_time = time.time()
    
    if clone_original:
        directory = os.path.join(directory, f"{repo_name}_original")
    repo_dir = os.path.join(directory, repo_name)

    for attempt in range(max_retries):
        try:
            cmd = ["git", "clone"]
            if depth is not None:
                cmd.extend(["--depth", str(depth)])
            if not lfs_support:
                cmd.append("--no-checkout")
            cmd.append(clone_url)
            cmd.append(repo_dir)
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            if not lfs_support:
                subprocess.run(["git", "checkout"], cwd=repo_dir, check=True, capture_output=True)
            else:
                subprocess.run(["git", "lfs", "fetch", "--all"], cwd=repo_dir, check=True, capture_output=True)
                subprocess.run(["git", "lfs", "checkout"], cwd=repo_dir, check=True, capture_output=True)
            
            end_time = time.time()
            
            return {
                "name": repo_name,
                "last_ripped": datetime.now().isoformat(),
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "clone_time": end_time - start_time,
                "success": True,
                "is_fork": repo.get("fork", False),
                "original_cloned": clone_original,
                "lfs_supported": lfs_support
            }
        except subprocess.CalledProcessError as e:
            if attempt == max_retries - 1:
                print(f"Error cloning repository {repo_name} after {max_retries} attempts: {e}")
                return {
                    "name": repo_name,
                    "success": False,
                    "error": str(e),
                    "is_fork": repo.get("fork", False),
                    "original_cloned": clone_original,
                    "lfs_supported": lfs_support
                }
            time.sleep(2 * attempt)

def load_analytics(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_analytics(analytics, filename):
    with open(filename, 'w') as f:
        json.dump(analytics, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Clone GitHub repositories with multithreading")
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("repo_option", choices=["all", "starred"], help="Repository option: 'all' or 'starred'")
    parser.add_argument("-d", "--directory", default=os.getcwd(), help="Directory to clone repositories into")
    parser.add_argument("--depth", type=int, help="Depth of git clone (optional)")
    parser.add_argument("--sync", action="store_true", help="Sync mode: clone original repos for forks")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--lfs", action="store_true", help="Enable Git LFS support")

    args = parser.parse_args()

    username = args.username
    repo_option = args.repo_option
    directory = args.directory
    depth = args.depth
    sync_mode = args.sync
    token = args.token or os.environ.get('GITHUB_TOKEN')
    lfs_support = args.lfs

    if not token:
        print("Warning: No GitHub token provided. You may encounter rate limits.")
    
    if lfs_support:
        print("Git LFS support enabled.")
    else:
        print("Git LFS support disabled. Large files will be skipped.")
    
    analytics_file = f"{username}_repo_analytics.json"
    analytics = load_analytics(analytics_file)

    print(f"Fetching repository information for user: {username}")
    repos = get_all_repos(username, "user" if repo_option == "all" else "starred",token)

    if not repos:
        print("No repositories found or error occurred.")
        sys.exit(1)

    print(f"Found {len(repos)} repositories.")
    print(f"Cloning repositories into: {directory}")
    if depth is not None:
        print(f"Using clone depth: {depth}")
    if sync_mode:
        print("Sync mode enabled: Will clone original repositories for forks")

    max_workers = 32
    
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_repo = {executor.submit(clone_repo, repo, directory, depth, token,lfs_support): repo for repo in repos}
        
        if sync_mode:
            forked_repos = [repo for repo in repos if repo['fork']]
            print(f"Processing {len(forked_repos)} forked repositories...")
            with tqdm(total=len(forked_repos), desc="Fetching originals", unit="repo") as fork_pbar:
                for repo in forked_repos:
                    original_repo = get_original_repo(repo, token)
                    if original_repo:
                        future_to_repo[executor.submit(clone_repo, original_repo, directory, depth, token,lfs_support,clone_original=True)] = original_repo
                    fork_pbar.update(1)
        
        total_repos = len(future_to_repo)
        with tqdm(total=total_repos, desc="Cloning Progress", unit="repo") as pbar:
            for future in concurrent.futures.as_completed(future_to_repo):
                result = future.result()
                pbar.update(1)
                if result["success"]:
                    analytics[result["name"]] = result
                else:
                    pbar.write(f"Failed to clone {result['name']}: {result['error']}")

    end_time = time.time()
    total_time = end_time - start_time
    repos_cloned = sum(1 for repo in analytics.values() if repo.get("success", False))
    actual_rate = repos_cloned / total_time * 60

    print(f"\nCloning complete.")
    print(f"Total repositories attempted: {total_repos}")
    print(f"Successfully cloned repositories: {repos_cloned}")
    print(f"Total time taken: {total_time:.2f} seconds")
    print(f"Actual cloning rate: {actual_rate:.2f} repos per minute")

    if sync_mode:
        original_repos_cloned = sum(1 for repo in analytics.values() if repo.get("success", False) and repo.get("original_cloned", False))
        print(f"Original repositories cloned for forks: {original_repos_cloned}")

    save_analytics(analytics, analytics_file)
    print(f"Analytics saved to {analytics_file}")

if __name__ == "__main__":
    main()

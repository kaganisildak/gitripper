![GitHub Repository Ripper Logo](https://github.com/kaganisildak/gitripper/blob/main/ico.png?raw=true)

# GitHub Repository Ripper
For the psychopaths who love archiving everything, the GitHub Ripper CLI tool

GitHub Repository Ripper is a powerful Python script that allows you to efficiently clone multiple GitHub repositories, including support for forked repositories, Git LFS. It's designed for users who need to backup everythings.

## Features

- Clone all or starred repositories of a specified GitHub user
- Support for authenticating with a GitHub token to bypass rate limits and access private repositories
- Option to clone original repositories of forks (sync mode)
- Git LFS support
- Multithreaded cloning for improved performance
- Detailed analytics of cloned repositories
- Progress bar for real-time feedback during cloning

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/kaganisildak/gitripper
   cd gitripper
   ```

2. Install the required dependencies:
   ```
   pip install requests tqdm
   ```

3. Ensure you have Git and Git LFS installed on your system if you plan to use LFS support.

## Usage

Basic usage:

```
python github_repo_ripper.py <username> <all|starred> [options]
```

### Command-line Options

- `username`: The GitHub username whose repositories you want to clone
- `all|starred`: Whether to clone all repositories or only starred ones
- `-d, --directory`: Directory to clone repositories into (default: current directory)
- `--depth`: Depth of git clone (optional)
- `--sync`: Enable sync mode to clone original repositories for forks
- `--token`: GitHub personal access token for authentication
- `--lfs`: Enable Git LFS support

### Examples

1. Clone all repositories of a user:
   ```
   python github_repo_ripper.py username all
   ```

2. Clone starred repositories with a specific clone depth:
   ```
   python github_repo_ripper.py username starred --depth 1
   ```

3. Clone all repositories with sync mode and LFS support:
   ```
   python github_repo_ripper.py username all --sync --lfs
   ```


## TODO

Here are some potential enhancements for future development:

0. Add support for upload rips to bucket storage/ftp/webdav etc.
1. Add support for GitLab and Bitbucket repositories
2. Implement incremental updates for previously cloned repositories
3. Add options for filtering repositories based on criteria like language, stars, or last update date
4. Improve error handling and retry mechanisms for network issues
5. Implement automatic scheduling for periodic cloning and backups

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

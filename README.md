# GitHub Email Finder
A Python tool that scans GitHub commit history to find email addresses associated with a GitHub username.

## Features
- Extracts email addresses from commit history of a GitHub user
- Filters out no-reply GitHub emails
- Shows email frequency and the repositories where they were found
- Option to include repositories the user has contributed to
- Rich console output with progress indicators and formatted tables

## Installation
### Prerequisites
- Python 3.7 or higher

### Setup Instructions
1. Clone and enter the repository:
   ```bash
   git clone https://github.com/ternera/github-email-finder.git
   cd github-email-finder
   ```
2. Install the required dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

## Usage
Basic usage:
```bash
python3 script.py USERNAME
```

With options:
```bash
python3 script.py USERNAME --token YOUR_GITHUB_TOKEN --contributions
```

### Environment Variables
You can set your GitHub token as an environment variable to avoid passing it on the command line:
```bash
# For bash/zsh
export GITHUB_TOKEN=your_github_token
# For Windows CMD
set GITHUB_TOKEN=your_github_token
# For Windows PowerShell
$env:GITHUB_TOKEN = "your_github_token"
```
Then run the script without the token parameter:
```bash
python3 script.py USERNAME
```

### Command Line Options
- `USERNAME`: The GitHub username to search for (required)
- `--token`, `-t`: GitHub personal access token (optional but recommended)
- `--contributions`, `-c`: Include repositories the user has contributed to
- `--verbose`, `-v`: Enable verbose output with additional details

### Examples
Search for a user's email addresses:
```bash
python3 script.py ternera
```

Include repositories the user has contributed to:
```bash
python3 script.py ternera --contributions
```

Use with a GitHub token for higher rate limits:
```bash
python3 script.py ternera --token ghp_xxxxxxxxxxxx
```

## GitHub Token
While the tool works without a token, GitHub API has rate limits that may restrict your usage. To get a GitHub personal access token:
1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token"
3. Give it a name and select the "public_repo" scope
4. Click "Generate token" and copy the token

## How It Works
1. Fetches the user's repositories using the GitHub API
2. Optionally searches for repositories the user has contributed to
3. For each repository, scans the commit history to find commits by the user
4. Extracts email addresses from the commit author and committer data
5. Filters out GitHub's no-reply email addresses
6. Presents the results in a formatted table

## Limitations
- GitHub API rate limits may restrict usage without a token
- Private repositories are only accessible if your user token has permissions to view them
- The tool only finds emails used in commits, not emails in the user's profile
- The search for contributed repositories is limited to 100 repositories

## Disclaimer
This tool is for educational purposes only. Please respect GitHub's terms of service and privacy policies when using this tool.
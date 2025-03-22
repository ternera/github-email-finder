#!/usr/bin/env python3
"""
GitHub Email Finder

A tool to extract email addresses from a GitHub user's commit history.
"""

import argparse
import json
import os
import re
import sys
import time
import site
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

# Add user site-packages to path if modules are not found
try:
    import requests
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    # Add user site-packages to path
    user_site = site.getusersitepackages()
    if user_site not in sys.path:
        sys.path.insert(0, user_site)
    try:
        import requests
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.progress import Progress, SpinnerColumn, TextColumn
    except ImportError:
        print("Required packages not found. Please install them using:")
        print("pip3 install --user requests rich")
        sys.exit(1)

class GitHubEmailFinder:
    """Class to extract email addresses from GitHub commit history."""

    def __init__(self, token: Optional[str] = None, verbose: bool = False):
        """
        Initialize the GitHub Email Finder.

        Args:
            token: GitHub personal access token (optional but recommended)
            verbose: Enable verbose output
        """
        self.token = token
        self.verbose = verbose
        self.session = requests.Session()
        self.console = Console()
        
        # Set up headers for GitHub API
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Email-Finder",
        }
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def get_user_repos(self, username: str) -> List[str]:
        """
        Get a list of repositories for a GitHub user.

        Args:
            username: GitHub username

        Returns:
            List of repository names
        """
        repos = []
        page = 1
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Fetching repositories..."),
            transient=True,
        ) as progress:
            task = progress.add_task("", total=None)
            
            while True:
                url = f"https://api.github.com/users/{username}/repos"
                params = {"per_page": 100, "page": page}
                
                try:
                    response = self.session.get(url, headers=self.headers, params=params)
                    response.raise_for_status()
                    
                    repo_data = response.json()
                    if not repo_data:
                        break
                        
                    repos.extend([repo["full_name"] for repo in repo_data])
                    
                    # Check if we have more pages
                    if len(repo_data) < 100:
                        break
                        
                    page += 1
                    time.sleep(0.5)  # Respect rate limits
                    
                except requests.RequestException as e:
                    self.console.print(f"[bold red]Error fetching repositories: {e}[/]")
                    break
                
        return repos

    def get_user_contributions(self, username: str) -> List[str]:
        """
        Find repositories that a user has contributed to (not just their own).
        
        This is more complex as GitHub API doesn't directly provide this info.
        We'll use the search API with limited results as a sample.

        Args:
            username: GitHub username

        Returns:
            List of repository names
        """
        contrib_repos = []
        
        # Search for repositories where the user has contributed
        url = "https://api.github.com/search/issues"
        params = {
            "q": f"author:{username} type:pr is:merged",
            "per_page": 100,
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Searching for contributions..."),
            transient=True,
        ) as progress:
            task = progress.add_task("", total=None)
            
            try:
                response = self.session.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                for item in data.get("items", []):
                    if "repository_url" in item:
                        repo_url = item["repository_url"]
                        repo_name = "/".join(repo_url.split("/")[-2:])
                        contrib_repos.append(repo_name)
                        
            except requests.RequestException as e:
                self.console.print(f"[bold red]Error finding contributions: {e}[/]")
        
        return list(set(contrib_repos))  # Remove duplicates

    def get_commit_emails(self, repo: str, username: str) -> Dict[str, int]:
        """
        Extract email addresses from commit history for a specific repository.

        Args:
            repo: Repository name (format: owner/repo)
            username: GitHub username to filter commits

        Returns:
            Dictionary of email addresses and their occurrence count
        """
        emails = Counter()
        page = 1
        
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]Scanning {repo}..."),
            transient=True,
        ) as progress:
            task = progress.add_task("", total=None)
            
            while True:
                url = f"https://api.github.com/repos/{repo}/commits"
                params = {"author": username, "per_page": 100, "page": page}
                
                try:
                    response = self.session.get(url, headers=self.headers, params=params)
                    
                    # Skip if repo is not found or we don't have access
                    if response.status_code in (404, 403):
                        if self.verbose:
                            self.console.print(f"[yellow]Skipping {repo} - {response.status_code}[/]")
                        break
                    
                    response.raise_for_status()
                    commits = response.json()
                    
                    if not commits:
                        break
                    
                    # Extract emails from commit data
                    for commit in commits:
                        if "commit" in commit and "author" in commit["commit"]:
                            author = commit["commit"]["author"]
                            if "email" in author and author["email"]:
                                email = author["email"].lower()
                                # Skip GitHub's noreply emails
                                if not self._is_github_noreply_email(email):
                                    emails[email] += 1
                        
                        if "committer" in commit and "commit" in commit and "committer" in commit["commit"]:
                            committer = commit["commit"]["committer"]
                            if "email" in committer and committer["email"]:
                                email = committer["email"].lower()
                                # Skip GitHub's noreply emails
                                if not self._is_github_noreply_email(email):
                                    emails[email] += 1
                    
                    # Check if we have more pages
                    if len(commits) < 100:
                        break
                        
                    page += 1
                    time.sleep(0.5)  # Respect rate limits
                    
                except requests.RequestException as e:
                    if self.verbose:
                        self.console.print(f"[yellow]Error scanning {repo}: {e}[/]")
                    break
                    
        return dict(emails)
        
    def _is_github_noreply_email(self, email: str) -> bool:
        """
        Check if an email is a GitHub noreply email.
        
        Args:
            email: Email address to check
            
        Returns:
            True if it's a GitHub noreply email, False otherwise
        """
        # Common GitHub noreply patterns
        noreply_patterns = [
            "@users.noreply.github.com",
            "noreply@github.com",
            "@noreply.github.com",
            "@noreply.githubassets.com"
        ]
        
        return any(pattern in email for pattern in noreply_patterns)

    def find_emails(self, username: str, include_contributions: bool = False) -> Dict[str, Dict[str, int]]:
        """
        Find email addresses from all repositories for a user.

        Args:
            username: GitHub username
            include_contributions: Whether to include repos the user contributed to

        Returns:
            Dictionary mapping email addresses to repositories and counts
        """
        # Dictionary to store emails and their sources
        email_sources = defaultdict(dict)
        
        # Get user's own repositories
        self.console.print(f"[bold green]Finding repositories for [blue]{username}[/]...[/]")
        repos = self.get_user_repos(username)
        
        # Get repositories user has contributed to
        contributed_repos = []
        if include_contributions:
            self.console.print(f"[bold green]Finding repositories [blue]{username}[/] has contributed to...[/]")
            contributed_repos = self.get_user_contributions(username)
            
        # Combine and remove duplicates
        all_repos = list(set(repos + contributed_repos))
        
        if not all_repos:
            self.console.print("[bold yellow]No repositories found for this user.[/]")
            return {}
            
        # Extract emails from each repository
        self.console.print(f"[bold green]Found [blue]{len(all_repos)}[/] repositories. Scanning for email addresses...[/]")
        
        for repo in all_repos:
            repo_emails = self.get_commit_emails(repo, username)
            
            # Add emails to our sources dictionary
            for email, count in repo_emails.items():
                email_sources[email][repo] = count
        
        return dict(email_sources)

    def display_results(self, email_sources: Dict[str, Dict[str, int]], username: str):
        """
        Display the results in a formatted table.

        Args:
            email_sources: Dictionary mapping emails to repo sources and counts
            username: GitHub username
        """
        if not email_sources:
            self.console.print(f"[bold yellow]No email addresses found for {username}.[/]")
            return
            
        total_emails = len(email_sources)
        
        # Create a table for the results
        table = Table(title=f"Email Addresses for {username}")
        table.add_column("Email", style="cyan")
        table.add_column("Occurrences", justify="right", style="green")
        table.add_column("Sources", style="blue")
        
        # Add rows to the table
        for email, sources in sorted(email_sources.items(), 
                                    key=lambda x: sum(x[1].values()), 
                                    reverse=True):
            total_count = sum(sources.values())
            sources_list = ", ".join([f"{repo} ({count})" for repo, count in sources.items()])
            
            table.add_row(
                email,
                str(total_count),
                sources_list
            )
        
        # Print results
        self.console.print(Panel(
            f"Found [bold cyan]{total_emails}[/] unique email address(es) for [bold blue]{username}[/]",
            expand=False
        ))
        self.console.print(table)
        

def main():
    """Main function to run the email finder tool."""
    parser = argparse.ArgumentParser(description="Find email addresses from GitHub commit history")
    parser.add_argument("username", help="GitHub username to search")
    parser.add_argument("--token", "-t", help="GitHub personal access token (recommended to avoid rate limits)")
    parser.add_argument("--contributions", "-c", action="store_true", help="Include repositories the user contributed to")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Check for token in environment if not provided
    token = args.token or os.environ.get("GITHUB_TOKEN")
    
    # Initialize the finder
    finder = GitHubEmailFinder(token=token, verbose=args.verbose)
    
    # Show warning if no token provided
    console = Console()
    if not token:
        console.print("[bold yellow]Warning: No GitHub token provided. Rate limits may apply.[/]")
    
    try:
        # Find email addresses
        email_sources = finder.find_emails(args.username, args.contributions)
        
        # Display results
        finder.display_results(email_sources, args.username)
        
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Search interrupted by user.[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/]")
        if args.verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
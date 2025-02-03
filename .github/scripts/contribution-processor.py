# contribution-processor.py
import os
import re
import json
import yaml
import base64
from github import Github
import requests

class ContributionProcessor:
    def __init__(self, github_token, issue_number):
        """
        Initialize the contribution processor with GitHub credentials and issue details.
        
        :param github_token: GitHub authentication token
        :param issue_number: Number of the issue to process
        """
        self.g = Github(github_token)
        self.repo = self.g.get_repo(os.environ.get('GITHUB_REPOSITORY'))
        self.issue = self.repo.get_issue(issue_number)
        self.body = self.parse_issue_body(self.issue.body)

    def parse_issue_body(self, body):
        """
        Parse the issue body, handling potential parsing challenges.
        
        :param body: Raw issue body text
        :return: Dictionary of parsed fields
        """
        # TODO: Implement robust parsing to extract fields correctly
        fields = {}
        sections = body.split('###')
        
        for section in sections[1:]:  # Skip first empty section
            lines = section.strip().split('\n')
            key = lines[0].strip().lower().replace(' ', '_')
            
            # Special handling for multi-line fields
            if key in ['readme_content', 'custom_code', 'lorebook_content']:
                value = '\n'.join(lines[1:]).strip()
            else:
                value = lines[1].strip() if len(lines) > 1 else ''
            
            fields[key] = value
        
        return fields

    def sanitize_filename(self, name):
        """
        Sanitize filename to remove forbidden characters.
        
        :param name: Original filename
        :return: Sanitized filename
        """
        return re.sub(r'[<>:"/\\|?*]', '_', name)

    def create_contribution_branch(self):
        """
        Create a new branch for the contribution from the main branch.
        
        :return: Name of the created branch
        """
        base_branch = self.repo.get_branch('main')
        branch_name = f'contribution/{self.body.get("content_name", "unnamed")}'
        #branch_name = f"contribution/{self.issue_number}"
        print(f"DEBUG: Creating branch {branch_name}")
        
        # Create branch from main
        ref = f'refs/heads/{branch_name}'
        self.repo.create_git_ref(ref, base_branch.commit.sha)
        
        return branch_name

    def process_lorebook(self, branch_name):
        """
        Process lorebook contribution.
        
        :param branch_name: Branch to commit files to
        """
        content_name = self.sanitize_filename(f"{self.body.get('content_name', 'unnamed')}_{self.body.get('author', 'unknown')}")
        content_path = f"lore-books/{self.body.get('rating', 'sfw').lower()}/{content_name}"
        
        # Create files
        files_to_commit = [
            {
                'path': f"{content_path}/{content_name}_lorebook.txt",
                'content': self.body.get('lorebook_content', ''),
                'message': 'Lorebook content'
            },
            {
                'path': f"{content_path}/readme.md",
                'content': self.body.get('readme_content', ''),
                'message': 'Lorebook README'
            },
            {
                'path': f"{content_path}/manifest.json",
                'content': json.dumps({
                    'name': self.body.get('content_name', ''),
                    'description': self.body.get('description', ''),
                    'author': self.body.get('author', ''),
                    # TODO: Add more base fields as specified
                }, indent=2),
                'message': 'Base manifest'
            }
        ]
        
        self._commit_files(branch_name, files_to_commit)

    def process_custom_code(self, branch_name):
        """
        Process custom code contribution.
        
        :param branch_name: Branch to commit files to
        """
        # Similar structure to lorebook processing
        # TODO: Implement custom code specific processing
        # Add malicious code detection placeholder
        pass

    def process_character(self, branch_name):
        """
        Process character contribution.
        
        :param branch_name: Branch to commit files to
        """
        # TODO: Implement character-specific processing
        # This includes downloading .gz file, creating src content, etc.
        pass

    def _commit_files(self, branch_name, files):
        """
        Commit multiple files to a specific branch.
        
        :param branch_name: Target branch
        :param files: List of file dictionaries with path, content, and message
        """
        for file_info in files:
            self.repo.create_file(
                path=file_info['path'],
                message=file_info['message'],
                content=file_info['content'],
                branch=branch_name
            )

    def create_pull_request(self, branch_name):
        """
        Create a pull request from the contribution branch to main.
        
        :param branch_name: Source branch for PR
        :return: Pull request object
        """
        pr = self.repo.create_pull(
            title=f"Contribution: {self.body.get('content_name', 'Unnamed')}",
            body=f"Closes #{self.issue.number}\n\nContribution by @{self.issue.user.login}",
            head=branch_name,
            base='main'
        )
        return pr

    def process(self):
        """
        Main processing method to handle different contribution types.
        """
        branch_name = self.create_contribution_branch()
        
        content_type = self.body.get('content_type', '').lower()
        if content_type == 'lorebook':
            self.process_lorebook(branch_name)
        elif content_type == 'custom code':
            self.process_custom_code(branch_name)
        elif content_type == 'character':
            self.process_character(branch_name)
        
        pr = self.create_pull_request(branch_name)
        return pr

def main():
    github_token = os.environ.get('GITHUB_TOKEN')
    issue_number = os.environ.get('ISSUE_NUMBER')
    
    if not github_token or not issue_number:
        print("Missing GitHub Token or Issue Number")
        return
    
    processor = ContributionProcessor(github_token, int(issue_number))
    processor.process()

if __name__ == '__main__':
    main()

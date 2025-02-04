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
        fields = {}
        
        # Split by ### but keep the section headers
        sections = body.split('###')
        
        for section in sections[1:]:  # Skip first empty section
            # Split into lines and remove empty ones
            lines = [line.strip() for line in section.split('\n') if line.strip()]
            
            if not lines:  # Skip empty sections
                continue
                
            # Get the section name from first line and convert to field name
            key = lines[0].strip().lower().replace(' ', '_')
            
            # For certain fields, join all remaining lines
            if key in ['readme_content', 'custom_code', 'lorebook_content']:
                value = '\n'.join(lines[1:]).strip()
            else:
                # For other fields, take just the first non-empty line after the header
                value = lines[1] if len(lines) > 1 else ''
                
                # Clean up common formatting issues
                value = value.replace('_No response_', '')  # Remove "_No response_" placeholders
                value = value.strip()  # Remove any extra whitespace
            
            fields[key] = value
            
            # Debug print to help track what's being parsed
            print(f"DEBUG: Parsed field {key} = {value[:50]}...")
        
        return fields

    def sanitize_filename(self, name):
        """
        Sanitize filename to remove forbidden characters.
        
        :param name: Original filename
        :return: Sanitized filename
        """
        return re.sub(r'[<>:"/\\|?* ]', '_', name)

    def create_contribution_branch(self):
        """
        Create a new branch for the contribution from the main branch.
        
        :return: Name of the created branch
        """
        base_branch = self.repo.get_branch('main')
        
        # Use content name if available, otherwise use issue number
        author_name = self.body.get('author_name', '').strip()
        fallback_name = str(self.issue.number)
        
        # Sanitize the branch name to remove invalid characters
        branch_safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', author_name or fallback_name)
        branch_name = f'contribution/{branch_safe_name}'
        
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
        
        print("DEBUG: Processing character contribution")
        
        # Get sanitized content name for folder structure
        content_name = self.sanitize_filename(f"{self.body.get('content_name', 'unnamed')}").strip()
        author_name = self.sanitize_filename(f"{self.body.get('author_name', 'anonymous')}").strip()
        fixed_path = "./ai-character-chat/characters/"
        variable_path = f"{self.body.get('rating', 'sfw').lower()}/{content_name}_{author_name}"
        content_path = fixed_path + variable_path
        
        # Create character manifest
        manifest = {
            'name': self.body.get('content_name', ''),
            'description': self.body.get('short_description', ''),
            'author': self.body.get('author_name', ''),
            'authorId': 123456, # TODO Retrieve author ID
            'imageUrl': self.body.get('image_url_for_your_content', ''),
            'shareUrl': self.body.get('perchance_character_share_link', ''),
            'downloadUrl': 'google.com.br' # TODO manipulate file to generate URL pointing to character.zip
            'shapeShifter_Pulls': 0,
            'galleryChat_Clicks': 0,
            'galleryDownload_Clicks': 0,
            'groupSettings': {
                'requires': [],
                'recommends': []
            },
            'features': {
                'customCode':[],
                'assets':[]
            },
            # TODO: Populate categories automatically by comparing the fields with the file categories.json
            'categories': {
                'rating': self.body.get('content_rating_(required)', 'sfw'), # Fixed category
                # TODO: Populate categories below using categories.json. Ignore if a category exists in categories.json, but is missing on the issue.
                'species': [self.body.get('species', '')], # TODO: If more than one tag is selected for a category, treat it accordingly
                'gender': [self.body.get('gender', '')],
                'genre': [self.body.get('genre', '')],
                'source': [self.body.get('source', '')],
                'role': [self.body.get('role', '')],
                'personality': [self.body.get('personality', '')]
            }
        }

        # Create changelog.json
        now = datetime.datetime.utcnow().isoformat() + 'Z'    # Date and time in ISO 8601 (UTC)
        changelog = {
            'currentVersion': '1.2.0',
            'created': now,
            'lastUpdated': now,
            'history': [      
                {
                    'version': '1.0.0',
                    'date': now,
                    'type': 'initial',
                    'changes': ['Initial release']
                }
            ]
        }
        
        # Prepare files to commit
        files_to_commit = [
            {
                'path': f"{content_path}/manifest.json",
                'content': json.dumps(manifest, indent=2),
                'message': 'Add character manifest'
            },
            {
                'path': f"{content_path}/changelog.json",
                'content': json.dumps(changelog, indent=2),
                'message': 'Add character changelog'
            },
            {
                'path': f"{content_path}/README.md",
                'content': self.body.get('readme_content', ''),
                'message': 'Add character README'
            }
        ]
        
        print(f"DEBUG: Committing {len(files_to_commit)} files for character")
        self._commit_files(branch_name, files_to_commit)
        
        return True

    def _commit_files(self, branch_name, files):
        """
        Commit multiple files to a specific branch.
        
        :param branch_name: Target branch
        :param files: List of file dictionaries with path, content, and message
        """
        print(f"DEBUG: Attempting to commit {len(files)} files to branch {branch_name}")
        
        for file_info in files:
            try:
                path = file_info['path']
                content = file_info['content']
                message = file_info['message']
                
                print(f"DEBUG: Creating file {path}")
                
                # Convert content to base64 if it's not already
                if isinstance(content, str):
                    content = content.encode('utf-8')
                
                # Create or update file
                self.repo.create_file(
                    path=path,
                    message=message,
                    content=content,
                    branch=branch_name
                )
                print(f"DEBUG: Successfully created file {path}")
                
            except Exception as e:
                print(f"ERROR: Failed to commit file {file_info['path']}: {str(e)}")
                raise

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
        print(f"DEBUG: Starting process with body: {self.body}")
        
        content_type = self.body.get('content_type', '').lower().strip()
        print(f"DEBUG: Content type identified as: {content_type}")
        
        branch_name = self.create_contribution_branch()
        files_committed = False
        
        try:
            if content_type == 'lorebook':
                files_committed = self.process_lorebook(branch_name)
            elif content_type == 'custom code':
                files_committed = self.process_custom_code(branch_name)
            elif content_type == 'character':
                files_committed = self.process_character(branch_name)
            
            if not files_committed:
                print("DEBUG: No files committed, creating placeholder")
                placeholder_content = f"""Contribution from issue #{self.issue.number}
    Content Type: {content_type}
    Author: {self.body.get('author_name', 'Unknown')}
    """
                self._commit_files(branch_name, [{
                    'path': 'contributions/placeholder.md',
                    'content': placeholder_content,
                    'message': f'Add placeholder for {content_type} contribution'
                }])
            
            print("DEBUG: Creating pull request")
            pr = self.create_pull_request(branch_name)
            return pr
        
        except Exception as e:
            print(f"ERROR in process: {str(e)}")
            raise

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

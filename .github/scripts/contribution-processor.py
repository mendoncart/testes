# contribution-processor.py
import os
import re
import json
import yaml
import base64
import gzip
import io
import zipfile
import requests
from urllib.parse import urlparse, parse_qs
from github import Github
import datetime

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
        return re.sub(r'[<>:"/\\|?*]', '_', name)

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
        :return: Boolean indicating success
        """
        print("DEBUG: Processing character contribution")
        
        # Get basic information
        content_name = self.sanitize_filename(self.body.get('content_name', 'unnamed'))
        author_name = self.sanitize_filename(self.body.get('author_name', 'anonymous'))
        share_url = self.body.get('perchance_character_share_link', '')
        
        # Validate share URL
        if not share_url:
            raise ValueError("Missing Perchance character share link")
            
        # Process the character file
        character_files = self.download_and_process_character_file(share_url)
        
        # Set up paths
        base_path = "ai-character-chat/characters"
        rating = self.body.get('content_rating_(required)', 'fix').lower()
        char_path = f"{base_path}/{rating}/{content_name} - {author_name}"
        
        # Auto-categorize content
        #categories = self.auto_categorize_content(character_files.get('src/roleInstruction.txt', ''))
        
        # Create manifest
        manifest = {
            'name': content_name,
            'description': self.body.get('short_description', ''),
            'author': author_name,
            'authorId': self.issue.user.id,
            'imageUrl': self.body.get('image_url_for_your_content', ''),
            'shareUrl': share_url,
            'downloadUrl': f"{char_path}/character.zip",
            'shapeShifter_Pulls': 0,
            'galleryChat_Clicks': 0,
            'galleryDownload_Clicks': 0,
            'groupSettings': {
                'requires': [],
                'recommends': []
            },
            'features': {
                'customCode': [char_path + "/src/customCode.txt"] if character_files.get('src/customCode.txt') else [],
                'assets': []
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
            'currentVersion': '1.0.0',
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
                'path': f"{char_path}/manifest.json",
                'content': json.dumps(manifest, indent=2),
                'message': 'Add character manifest'
            },
            {
                'path': f"{char_path}/changelog.json",
                'content': json.dumps(changelog, indent=2),
                'message': 'Add character changelog'
            },
            {
                'path': f"{char_path}/README.md",
                'content': self.body.get('readme_content', ''),
                'message': 'Add character README'
            }
        ]
        
        # Add character files
        for file_path, content in character_files.items():
            files_to_commit.append({
                'path': f"{char_path}/{file_path}",
                'content': content,
                'message': f'Add character file: {file_path}'
            })
        
        # Commit all files
        print(f"DEBUG: Committing {len(files_to_commit)} files for character")
        self._commit_files(branch_name, files_to_commit)
        
        return True

    def download_and_process_character_file(self, share_url):
        """
        Download and process character file from Perchance share URL.
        
        :param share_url: Perchance character share URL
        :return: Tuple of (processed_data, character_zip_content)
        """
        try:
            # Extract file ID from share URL
            parsed_url = urlparse(share_url)
            query_params = parse_qs(parsed_url.query)
            data_param = query_params.get('data', [''])[0]
            file_id = data_param.split('~')[-1]
            
            if not file_id.endswith('.gz'):
                raise ValueError("Invalid share URL format")
            
            # Download file from Perchance
            download_url = f"https://user-uploads.perchance.org/file/{file_id}"
            response = requests.get(download_url, timeout=15)
            response.raise_for_status()
            
            # Decompress gzip content
            with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz_file:
                json_content = gz_file.read().decode('utf-8')
            
            # Parse JSON content
            character_data = json.loads(json_content)
            character_info = character_data.get('addCharacter', {})
            
            return self.create_character_files(character_info)
            
        except Exception as e:
            print(f"ERROR: Failed to process character file: {str(e)}")
            raise
    
    def create_character_files(self, character_info):
        """
        Create individual files for each character attribute and zip file.
        
        :param character_info: Dictionary containing character information
        :return: Dictionary of created files and their content
        """
        files = {}
        
        # Define which fields should be saved as separate files
        text_fields = [
            'roleInstruction', 'reminderMessage', 'customCode',
            'imagePromptPrefix', 'imagePromptSuffix', 'imagePromptTriggers',
            'initialMessages', 'loreBookUrls','avatar','userCharacter',
            'systemCharacter'
        ]
        
        # Create individual text files
        for field in text_fields:
            if field in character_info and character_info[field]:
                content = character_info[field]
                if isinstance(content, (dict, list)):
                    content = json.dumps(content, indent=2)
                files[f"src/{field}.txt"] = content
        
        # Create character.zip containing the original data
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # TODO: Create a proper character format json
            placeholder_data = {
                "version": "1.0.0",
                "exportDate": datetime.datetime.utcnow().isoformat(),
                "characterData": character_info
            }
            zip_file.writestr('character.json', json.dumps(placeholder_data, indent=2))
        
        files['character.zip'] = zip_buffer.getvalue()
        
        return files
    
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

        content_type = self.body.get('content_type', '').strip() or ''
        
        pr = self.repo.create_pull(
            title=f"[{content_type} Contribution]: {self.body.get('content_name', 'Unnamed')} by {self.body.get('author', 'Anonymous')}",
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

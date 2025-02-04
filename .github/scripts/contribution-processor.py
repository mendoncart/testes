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
        If branch exists, just return its name.
        
        :return: Name of the created branch
        """
        base_branch = self.repo.get_branch('main')
        
        # Use content name if available, otherwise use issue number
        author_name = self.body.get('author_name', '').strip()
        fallback_name = str(self.issue.number)
        
        # Sanitize the branch name
        branch_safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', author_name or fallback_name)
        branch_name = f'contribution/{branch_safe_name}'
        
        print(f"DEBUG: Creating/checking branch {branch_name}")
        
        try:
            # Try to get the branch first
            self.repo.get_branch(branch_name)
            print(f"DEBUG: Branch {branch_name} already exists")
        except:
            # Branch doesn't exist, create it
            ref = f'refs/heads/{branch_name}'
            try:
                self.repo.create_git_ref(ref, base_branch.commit.sha)
                print(f"DEBUG: Created new branch {branch_name}")
            except Exception as e:
                print(f"ERROR: Failed to create branch: {str(e)}")
                raise
        
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
        # Load categories configuration
        with open('categories.json', 'r') as f:
            categories_config = json.load(f)
        
        # Create categories dictionary dynamically
        categories = {
            'rating': rating  # Fixed category
        }
        
        # Populate other categories dynamically from categories.json
        for category in categories_config:
            category_name = category['name'].lower()
            if category_name != 'rating':  # Skip rating as it's handled separately
                # Get the value from body if it exists, otherwise use empty list
                category_value = self.body.get(category_name.lower(), '')
                if category_value:
                    # If multiple values are selected (comma-separated), split them
                    if isinstance(category_value, str) and ',' in category_value:
                        categories[category_name] = [v.strip() for v in category_value.split(',')]
                    else:
                        categories[category_name] = [category_value]
                elif category['required']:
                    # For required categories with no value, use first general tag as default
                    #categories[category_name] = [category['tags']['general'][0]]
                    categories[category_name] = 'blank'
                else:
                    categories[category_name] = []
        
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
            'categories': categories
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

         # Update index.json
            updated_index = self.update_character_index(char_path, manifest)
            files_to_commit.append({
                'path': "ai-character-chat/characters/index.json",
                'content': updated_index,
                'message': f'Update index.json with {content_name}'
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
            
    def update_character_index(self, character_path, manifest_data):
        """
        Update the character index file with new character information.
        
        :param character_path: Relative path to character directory
        :param manifest_data: Character manifest data
        :return: Updated index content
        """
        index_path = "ai-character-chat/characters/index.json"
        
        try:
            # Try to get existing index file
            try:
                file_content = self.repo.get_contents(index_path)
                index_content = file_content.decoded_content.decode('utf-8')
                index_data = json.loads(index_content)
            except Exception as e:
                print(f"DEBUG: No existing index.json found or error reading it: {str(e)}")
                # If file doesn't exist, start with empty list
                index_data = []
            
            # Remove path prefix to match index format
            relative_path = character_path.replace("ai-character-chat/characters/", "")
            
            # Create new character entry
            new_entry = {
                "path": relative_path,
                "manifest": manifest_data
            }
            
            # Check if character already exists (by path)
            existing_index = next((i for i, item in enumerate(index_data) 
                                 if item["path"] == relative_path), None)
            
            if existing_index is not None:
                # Update existing entry
                index_data[existing_index] = new_entry
            else:
                # Add new entry
                index_data.append(new_entry)
            
            return json.dumps(index_data, indent=2)
            
        except Exception as e:
            print(f"ERROR: Failed to update character index: {str(e)}")
            raise
            
    def create_character_files(self, character_info):
        """
        Create individual files for each character attribute and zip file.
        
        :param character_info: Dictionary containing character information
        :return: Dictionary of created files and their content
        """
        files = {}
        
        # Define fields and their corresponding file formats
        field_formats = {
            'name': 'txt',
            'roleInstruction': 'txt',
            'reminderMessage': 'txt',
            'customCode': 'js',
            'imagePromptPrefix': 'txt',
            'imagePromptSuffix': 'txt',
            'imagePromptTriggers': 'txt',
            'initialMessages': 'json',
            'loreBookUrls': 'json',
            'avatar': 'json',
            'scene': 'json',
            'userCharacter': 'json',
            'systemCharacter': 'json'
        }
        
        # Create individual files based on format
        for field, format_type in field_formats.items():
            if field in character_info and character_info[field]:
                content = character_info[field]
                if format_type == 'json' or isinstance(content, (dict, list)):
                    content = json.dumps(content, indent=2)
                files[f"src/{field}.{format_type}"] = content

    
        # Create character.gz containing the original data
        gz_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=gz_buffer, mode='wb') as gz_file:
            # Format data according to the export template
            export_data = {
                "formatName": "dexie",
                "formatVersion": 1,
                "data": {
                    "databaseName": "chatbot-ui-v1",
                    "databaseVersion": 90,
                    "tables": [
                        {
                            "name": "characters",
                            "schema": "++id,modelName,fitMessagesInContextMethod,uuid,creationTime,lastMessageTime",
                            "rowCount": 1
                        },
                        # Add other table schemas with rowCount 0
                        {"name": "threads", "schema": "++id,name,characterId,creationTime,lastMessageTime,lastViewTime", "rowCount": 0},
                        {"name": "messages", "schema": "++id,threadId,characterId,creationTime,order", "rowCount": 0},
                        {"name": "misc", "schema": "key", "rowCount": 0},
                        {"name": "summaries", "schema": "hash,threadId", "rowCount": 0},
                        {"name": "memories", "schema": "++id,[summaryHash+threadId],[characterId+status],[threadId+status],[threadId+index],threadId", "rowCount": 0},
                        {"name": "lore", "schema": "++id,bookId,bookUrl", "rowCount": 0},
                        {"name": "textEmbeddingCache", "schema": "++id,textHash,&[textHash+modelName]", "rowCount": 0},
                        {"name": "textCompressionCache", "schema": "++id,uncompressedTextHash,&[uncompressedTextHash+modelName+tokenLimit]", "rowCount": 0},
                        {"name": "usageStats", "schema": "[dateHour+threadId+modelName],threadId,characterId,dateHour", "rowCount": 0}
                    ],
                    "data": [
                        {
                            "tableName": "characters",
                            "inbound": True,
                            "rows": [{
                                **character_info,
                                "id": 1,
                                "creationTime": int(datetime.datetime.now().timestamp() * 1000),
                                "lastMessageTime": int(datetime.datetime.now().timestamp() * 1000),
                                "$types": {
                                    "maxParagraphCountPerMessage": "undef",
                                    "initialMessages": "arrayNonindexKeys",
                                    "shortcutButtons": "arrayNonindexKeys",
                                    "loreBookUrls": "arrayNonindexKeys"
                                }
                            }]
                        },
                        # Add other empty tables
                        {"tableName": "threads", "inbound": True, "rows": []},
                        {"tableName": "messages", "inbound": True, "rows": []},
                        {"tableName": "misc", "inbound": True, "rows": []},
                        {"tableName": "summaries", "inbound": True, "rows": []},
                        {"tableName": "memories", "inbound": True, "rows": []},
                        {"tableName": "lore", "inbound": True, "rows": []},
                        {"tableName": "textEmbeddingCache", "inbound": True, "rows": []},
                        {"tableName": "textCompressionCache", "inbound": True, "rows": []},
                        {"tableName": "usageStats", "inbound": True, "rows": []}
                    ]
                }
            }
            gz_file.write(json.dumps(export_data, indent=2).encode('utf-8'))
        
        files['character.gz'] = gz_buffer.getvalue()
        
        return files

    def _get_file_sha(self, file_path):
        """
        Get the SHA of an existing file in the repository.
        
        :param file_path: Path to the file in the repository
        :return: SHA string or None if file doesn't exist
        """
        try:
            file_content = self.repo.get_contents(file_path)
            return file_content.sha
        except Exception as e:
            print(f"DEBUG: File {file_path} not found or error getting SHA: {str(e)}")
            return None
            
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

                # Get the file's SHA if it exists
                file_sha = self._get_file_sha(path)
                
               # Create or update file with optional SHA
                if file_sha:
                    print(f"DEBUG: Updating existing file {path}")
                    self.repo.update_file(
                        path=path,
                        message=message,
                        content=content,
                        branch=branch_name,
                        sha=file_sha
                    )
                else:
                    print(f"DEBUG: Creating new file {path}")
                    self.repo.create_file(
                        path=path,
                        message=message,
                        content=content,
                        branch=branch_name
                    )
                    
                print(f"DEBUG: Successfully created/updated file {path}")
                
            except Exception as e:
                print(f"ERROR: Failed to commit file {file_info['path']}: {str(e)}")
                raise

    def create_pull_request(self, branch_name):
        """
        Create a pull request from the contribution branch to main.
        Also adds the 'PR Generated' label to the issue.
        
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

        # Add label to the issue
        try:
            self.issue.add_to_labels("PR Generated")
        except Exception as e:
            print(f"WARNING: Failed to add PR Generated label to issue: {str(e)}")
            
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

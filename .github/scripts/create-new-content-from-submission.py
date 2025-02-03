# create-new-content-from-submission.py
# Process new content submissions creating PR with appropriate file structure to add it to the repository
import os
import json
import yaml
import re
from pathlib import Path
from slugify import slugify
from datetime import datetime, timezone
import requests

def parse_issue_body(issue_body):
    """
    Parse the GitHub issue body, which is in YAML-like format
    """
    # Remove any markdown sections
    print("RAW ISSUE_BODY:\n", issue_body)
    lines = [line for line in issue_body.split('\n') if not line.startswith('##')]
    print("Filtered ISSUE_BODY content:\n", lines)

    try:
        # Tentar carregar o YAML
        parsed_body = yaml.safe_load('\n'.join(lines))
    except yaml.YAMLError as e:
        print("YAML Parsing Error:", e)
        raise  # Relevanta o erro para diagnóstico
        
    return parsed_body

def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal and invalid characters
    """
    sanitized = slugify(filename, separator="_")
    sanitized = re.sub(r'[^a-z0-9_-]', '', sanitized)
    return sanitized

def validate_categories(content_type, rating, categories):
    """
    Validate categories against categories.json
    """
    with open('categories.json', 'r') as f:
        valid_categories = json.load(f)
    
    validated_categories = {}
    for category_def in valid_categories:
        category_name = category_def['name'].lower()
        
        # Get submitted values for this category
        submitted_values = categories.get(category_name, [])
        
        # If no values submitted, skip optional categories
        if not submitted_values and not category_def.get('required', False):
            continue
        
        # Check if category is valid for rating
        if category_def.get('nsfw_only', False) and rating == 'sfw':
            continue
        
        # Validate submitted values
        valid_tags = category_def['tags'].get('general', []) + (
            category_def['tags'].get('nsfw', []) if rating == 'nsfw' else []
        )
        
        # Ensure all submitted values are valid
        invalid_values = set(submitted_values) - set(valid_tags)
        if invalid_values:
            raise ValueError(f"Invalid {category_name} categories: {invalid_values}")
        
        validated_categories[category_name] = submitted_values
    
    return validated_categories

def create_manifest(content_type, form_data, author_github_id):
    """
    Create manifest.json with comprehensive information
    """
    base_manifest = {
        "name": form_data['content-name'],
        "description": form_data.get('description', ''),
        "author": form_data['author'],
        "authorId": {
            "githubUsername": author_github_id,
            "submissionDate": datetime.now(timezone.utc).isoformat()
        },
        "imageUrl": form_data.get('image-url', ''),
        "rating": form_data['rating'].lower(),
    }
    
    # Add content type specific fields
    if content_type == 'Character':
        base_manifest.update({
            "shareUrl": form_data.get('perchance-url', ''),
            "downloadUrl": "",
            "metrics": {
                "shapeshifterPulls": 0,
                "galleryChatClicks": 0,
                "galleryDownloadClicks": 0
            }
        })
    
    # Add categories if available
    categories = {}
    category_fields = ['species', 'gender', 'genre', 'source', 'role', 'personality', 'fetishes']
    for field in category_fields:
        if form_data.get(field):
            categories[field] = form_data[field]
    
    if categories:
        validated_categories = validate_categories(content_type, form_data['rating'], categories)
        base_manifest['categories'] = validated_categories
    
    return base_manifest

def create_changelog():
    """
    Create initial changelog structure
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        "currentVersion": "1.0.0",
        "created": now,
        "lastUpdated": now,
        "history": [
            {
                "version": "1.0.0",
                "date": now,
                "type": "initial",
                "changes": ["Initial release"]
            }
        ]
    }

def process_submission():
    """
    Process the submission and create appropriate files
    """
    # Parse issue body
    form_data = parse_issue_body(os.environ['ISSUE_BODY'])
    
    # Sanitize inputs
    content_type = form_data['content-type']
    content_name = sanitize_filename(form_data['content-name'])
    author = sanitize_filename(form_data['author'])
    rating = form_data['rating'].lower()
    
    # Create branch name
    branch_name = f"contribution/issue-{os.environ['ISSUE_NUMBER']}"
    
    # Create git branch
    os.system(f'git checkout -b {branch_name}')
    
    # Determine base path
    if content_type == 'Character':
        base_path = f"ai-character-chat/characters/{rating}/{content_name}_{author}"
    elif content_type == 'Custom Code':
        base_path = f"ai-character-chat/custom-codes/{content_name}_{author}"
    else:  # Lorebook
        base_path = f"lore-books/{rating}/{content_name}_{author}"
    
    # Create directory structure
    os.makedirs(base_path, exist_ok=True)
    
    # Create manifest.json
    manifest = create_manifest(content_type, form_data, os.environ['ISSUE_AUTHOR'])
    with open(f"{base_path}/manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Create README.md
    with open(f"{base_path}/readme.md", 'w') as f:
        f.write(form_data['readme'])
    
    # Create type-specific content
    if content_type == 'Character':
        # Create changelog.json
        changelog = create_changelog()
        with open(f"{base_path}/changelog.json", 'w') as f:
            json.dump(changelog, f, indent=2)
        
    elif content_type == 'Custom Code':
        # Create custom code file
        with open(f"{base_path}/{content_name}_{author}_code.js", 'w') as f:
            f.write(form_data['custom-code'])
            
    else:  # Lorebook
        # Create lorebook file
        with open(f"{base_path}/{content_name}_{author}_lorebook.txt", 'w') as f:
            f.write(form_data['lorebook'])
    
    # Commit changes
    os.system('git add .')
    os.system(f'git commit -m "Closes #{os.environ["ISSUE_NUMBER"]}: Add {content_type}: {content_name} by {author}"')
    os.system(f'git push origin {branch_name}')
    
    # Create PR
    headers = {
        'Authorization': f"token {os.environ['GITHUB_TOKEN']}",
        'Accept': 'application/vnd.github.v3+json'
    }
    
    pr_data = {
        'title': f"Add {content_type}: {content_name} by {author}",
        'body': f"Closes #{os.environ['ISSUE_NUMBER']}\n\nAutomatically created PR for content submission.",
        'head': branch_name,
        'base': 'develop'
    }
    
    response = requests.post(
        f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/pulls",
        headers=headers,
        json=pr_data
    )
    
    if response.status_code != 201:
        raise Exception(f"Failed to create PR: {response.text}")

if __name__ == "__main__":
    process_submission()

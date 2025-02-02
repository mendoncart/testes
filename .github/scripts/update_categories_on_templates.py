# .github/scripts/update_categories_on_templates.py
# Loads the categories file and use its categories to update it inside template issues
import json
import re

def load_categories():
    """
    Load and parse the categories.json file
    """
    with open('categories.json', 'r') as f:
        return json.load(f)

def generate_category_yaml(category):
    """
    Generate YAML for a single category dropdown
    
    Args:
        category (dict): Category information from categories.json
    
    Returns:
        str: YAML formatted dropdown for the category
    """
    # Combine general and nsfw tags into a single list
    all_tags = category['tags']['general'] + category['tags']['nsfw']
    
    # Generate the YAML structure
    yaml = f"""  - type: dropdown
    id: {category['name'].lower()}
    attributes:
      label: {category['name']}
      description: {category['description']}
      multiple: true
      options:
"""
    # Add each tag as an option
    for tag in all_tags:
        yaml += f"        - {tag}\n"
    
    # Add required validation if category is required
    yaml += "    validations:\n"
    yaml += f"      required: {str(category['required']).lower()}\n"
    
    return yaml

def update_template():
    """
    Update the contribution template with current categories from categories.json
    """
    # Load the current template
    with open('.github/ISSUE_TEMPLATE/contribution.yaml', 'r') as f:
        template = f.read()
    
    # Load categories
    categories = load_categories()
    
    # Generate YAML for all categories
    categories_yaml = ""
    for category in categories:
        categories_yaml += generate_category_yaml(category) + "\n"
    
    # Replace the categories section in the template
    new_template = re.sub(
        r'  # BEGIN_CATEGORIES.*?  # END_CATEGORIES',
        f'  # BEGIN_CATEGORIES\n{categories_yaml.rstrip()}\n  # END_CATEGORIES',
        template,
        flags=re.DOTALL
    )
    
    # Save the updated template
    with open('.github/ISSUE_TEMPLATE/contribution.yaml', 'w') as f:
        f.write(new_template)

if __name__ == "__main__":
    update_template()

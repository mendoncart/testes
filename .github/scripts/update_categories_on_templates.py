# Loads the categories file and use its categories to update it inside template issues
# .github/scripts/update_categories_on_templates.py
import json
import re
import os
from typing import Dict, List

class TemplateUpdater:
    """
    Class to handle template updates based on categories.json
    """
    def __init__(self):
        self.categories = self.load_categories()
        self.template_dir = '.github/ISSUE_TEMPLATE'
        
    def load_categories(self) -> List[Dict]:
        """
        Load and parse the categories.json file
        
        Returns:
            List[Dict]: List of category configurations
        """
        with open('categories.json', 'r') as f:
            return json.load(f)
    
    def ensure_directory_exists(self):
        """
        Ensure the template directory exists
        """
        os.makedirs(self.template_dir, exist_ok=True)
    
    def generate_category_yaml(self, category: Dict) -> str:
        """
        Generate YAML for a single category dropdown
        
        Args:
            category (Dict): Category information from categories.json
        
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
        for tag in sorted(all_tags):
            yaml += f"        - {tag}\n"
        
        # Add required validation if category is required
        yaml += "    validations:\n"
        yaml += f"      required: {str(category['required']).lower()}\n"
        
        return yaml
    
    def generate_category_request_options(self) -> str:
        """
        Generate the options list for category request template
        
        Returns:
            str: YAML formatted options for existing categories dropdown
        """
        yaml = "        - None (New Category)\n"
        for category in self.categories:
            yaml += f"        - {category['name']}\n"
        return yaml
    
    def update_contribution_template(self):
        """
        Update the contribution template with current categories
        """
        template_path = f"{self.template_dir}/contribution.yaml"
        
        # Generate categories section
        categories_yaml = ""
        for category in self.categories:
            categories_yaml += self.generate_category_yaml(category) + "\n"
            
        # Read existing template or use default
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template = f.read()
        else:
            # Here you would include the default template content
            template = "# Default template content\n"
            
        # Replace the categories section
        new_template = re.sub(
            r'  # BEGIN_CATEGORIES.*?  # END_CATEGORIES',
            f'  # BEGIN_CATEGORIES\n{categories_yaml.rstrip()}\n  # END_CATEGORIES',
            template,
            flags=re.DOTALL
        )
        
        # Save the updated template
        with open(template_path, 'w') as f:
            f.write(new_template)
            
    def update_category_request_template(self):
        """
        Update the category request template with current categories
        """
        template_path = f"{self.template_dir}/category-request.yaml"
        
        # Generate the category options
        categories_options = self.generate_category_request_options()
        
        # Template content
        template = """name: 🏷️ Category or Tag Request
description: Request new categories or tags for content classification
labels: ["category", "enhancement"]
body:
  - type: checkboxes
    id: search-check
    attributes:
      label: Search Check
      description: Please verify you have completed these steps before submitting
      options:
        - label: I have searched existing categories and tags in categories.json
          required: true
        - label: I have searched existing issues for similar category/tag requests
          required: true
        - label: I have checked if my request could fit within existing categories
          required: true

  # BEGIN_CATEGORIES_OPTIONS
  - type: dropdown
    id: existing-category
    attributes:
      label: Existing Category
      description: Select an existing category, or leave at 'None' to add a new one.
      options:
%s
    validations:
      required: true  
  # END_CATEGORIES_OPTIONS

  - type: input
    id: category-name
    attributes:
      label: └── New category Name
      description: Leave it blank if adding tags to existent category.
      placeholder: "e.g., Personality Traits"

  - type: textarea
    id: proposed-sfw-tags
    attributes:
      label: Proposed SFW Tags
      description: List the tags you'd like to add, one per line
      render: plain
      placeholder: |
        Tag 1
        Tag 2
        Tag 3
    validations:
      required: false

  - type: textarea
    id: proposed-nsfw-tags
    attributes:
      label: Proposed NSFW Tags
      description: List the tags you'd like to add, one per line
      render: plain
      placeholder: |
        Tag 1
        Tag 2
        Tag 3
    validations:
      required: false

  - type: textarea
    id: justification
    attributes:
      label: Justification
      description: Explain why these additions would be useful. Include examples if possible.
      placeholder: |
        - How will this improve content organization?
        - What types of content would use these tags?
        - Why can't existing categories/tags cover this?
    validations:
      required: true

  - type: textarea
    id: examples
    attributes:
      label: Example Characters (Optional)
      description: List some example characters that would use these categories/tags
      placeholder: |
        - Character 1: Would use tags X, Y
        - Character 2: Would use tags Y, Z

  - type: textarea
    id: additional-context
    attributes:
      label: Additional Context (Optional)
      description: Any other information that might be relevant to your request?
""" % categories_options

        # Save the template
        with open(template_path, 'w') as f:
            f.write(template)
    
    def update_all_templates(self):
        """
        Update all templates that depend on categories.json
        """
        self.ensure_directory_exists()
        self.update_contribution_template()
        self.update_category_request_template()

if __name__ == "__main__":
    updater = TemplateUpdater()
    updater.update_all_templates()

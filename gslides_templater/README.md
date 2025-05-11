# Google Slides Templater

A modern Python library for creating and working with Google Slides templates. Convert existing presentations into templates, create templates from scratch, and fill templates with your data.

## Features

- Convert existing Google Slides presentations into templates with placeholders
- Automatically identify potential placeholders in presentations
- Fill templates with various data types: text, numbers, lists, and images
- Maintain exact formatting from the original presentation
- Support for image and table placeholders
- Simple and flexible API for template creation and filling

## Installation

```bash
pip install gslides-templater
```

## Quick Start

### Authentication

```python
from gslides_templater import authenticate, SlidesClient

# Authenticate with Google API
credentials = authenticate(
    credentials_path="credentials.json",
    token_path="token.json"
)

# Create a client
client = SlidesClient(credentials)
```

### Creating a Template

```python
from gslides_templater.templates import TemplateConverter, TemplateCreator

# Convert an existing presentation to a template
presentation_id = "YOUR_PRESENTATION_ID"
converter = TemplateConverter(client)

# Analyze the presentation and suggest replacements
suggestions = converter.suggest_replacements(client.get_presentation(presentation_id))
print("Suggested replacements:")
for text, placeholder in suggestions.items():
    print(f"  - \"{text}\" -> {{{{{placeholder}}}}}")

# Customize replacements if needed
replacements = {
    "Company Name": "company_name",
    "John Doe": "person_name",
    "$1,000,000": "revenue",
    "2023": "year"
}

# Create the template
template = converter.convert_presentation(
    presentation_id,
    replacements=replacements,
    title="My Template",
    create_copy=True
)

print(f"Template created: {template.url}")

# Export template configuration for later use
creator = TemplateCreator(client)
creator.export_template_config(template, "template_config.json")
```

### Using a Template

```python
from gslides_templater.templates import TemplateFiller

# Create a template filler
filler = TemplateFiller(client)

# Create a new presentation from the template
presentation = filler.create_from_template(
    template.presentation_id,
    title="Filled Presentation"
)

# Data to fill the template with
data = {
    "company_name": "Acme Corporation",
    "person_name": "Jane Smith",
    "revenue": "$2,500,000",
    "year": "2024",
    "logo": "https://example.com/logo.png",  # Image URL
    "products": [  # List for table
        "Product A",
        "Product B",
        "Product C"
    ],
    "employees": [  # Dictionary list for table
        {"name": "Alice", "position": "CEO", "year": "2010"},
        {"name": "Bob", "position": "CTO", "year": "2012"},
        {"name": "Charlie", "position": "CFO", "year": "2015"}
    ]
}

# Fill the presentation with data
filler.fill_from_template_config(presentation, "template_config.json", data)

print(f"Filled presentation: {presentation.url}")
```

### Working with Template Configurations

```python
import json

# Save template info for later use
template_info = {
    "template_id": template.presentation_id,
    "config_path": "template_config.json"
}

with open("template_info.json", "w") as f:
    json.dump(template_info, f)

# Later, load the template info
with open("template_info.json", "r") as f:
    template_info = json.load(f)

# Create a new presentation from the saved template
filler = TemplateFiller(client)
presentation = filler.create_from_template(
    template_info["template_id"],
    title="New Presentation"
)

# Fill with new data
filler.fill_from_template_config(presentation, template_info["config_path"], new_data)
```

## Complete Workflow Example

A complete example demonstrating how to:
1. Import a presentation
2. Convert it to a template
3. Create new presentations based on the template

```python
from gslides_templater import SlidesClient, authenticate
from gslides_templater.templates import TemplateConverter, TemplateCreator, TemplateFiller
import json

# Authentication
credentials = authenticate(
    credentials_path="credentials.json",
    token_path="token.json"
)
client = SlidesClient(credentials)

# Step 1: Create a template from an existing presentation
source_presentation_id = "1AbCdEfGhIjKlMnOpQrStUvWxYz"  # Your presentation ID
converter = TemplateConverter(client)

# Analyze presentation content
suggestions = converter.suggest_replacements(client.get_presentation(source_presentation_id))
print("Suggested replacements:")
for text, placeholder in suggestions.items():
    print(f"  - \"{text}\" -> {{{{{placeholder}}}}}")

# Define replacements (you can use suggestions or define your own)
replacements = {
    "Acme Corp": "company_name",
    "John Smith": "ceo_name",
    "Annual Report 2023": "report_title",
    "$10M": "revenue"
}

# Create the template
template = converter.convert_presentation(
    source_presentation_id,
    replacements=replacements,
    title="Company Presentation Template",
    create_copy=True
)

print(f"Template created: {template.url}")

# Export template configuration
config_path = "template_config.json"
creator = TemplateCreator(client)
creator.export_template_config(template, config_path)

# Save template info for later use
with open("template_info.json", "w") as f:
    json.dump({
        "template_id": template.presentation_id,
        "config_path": config_path
    }, f)

# Step 2: Create and fill presentations from the template
filler = TemplateFiller(client)

# Sample data sets
companies = [
    {
        "company_name": "TechSolutions Inc.",
        "ceo_name": "Sarah Johnson",
        "report_title": "Annual Report 2024",
        "revenue": "$25M"
    },
    {
        "company_name": "Global Innovations Ltd.",
        "ceo_name": "David Chen",
        "report_title": "Q2 Progress Report",
        "revenue": "$8.5M"
    }
]

# Create a presentation for each company
for i, data in enumerate(companies):
    # Create a new presentation from the template
    presentation = filler.create_from_template(
        template.presentation_id,
        title=f"Presentation for {data['company_name']}"
    )
    
    # Fill the presentation with data
    filler.fill_from_template_config(presentation, config_path, data)
    
    print(f"Created presentation {i+1}: {presentation.url}")
```

## Advanced Features

### Automatic Template Creation

```python
# Automatically analyze and convert a presentation to a template
template, replacements = converter.analyze_and_convert(
    presentation_id,
    title="Auto-Generated Template",
    suggestion_threshold=0.7
)

print("Automatic replacements applied:")
for original_text, placeholder in replacements.items():
    print(f"  - \"{original_text}\" -> {{{{{placeholder}}}}}")
```

### Creating Templates from Scratch

```python
from gslides_templater.templates import TemplateCreator

# Create a blank template
creator = TemplateCreator(client)
template = creator.create_blank_template(title="New Template")

# Add slides with placeholders
slide1 = creator.add_placeholder_slide(
    template,
    title="{{title}}",
    content="{{content}}"
)

slide2 = creator.add_placeholder_slide(
    template,
    title="About {{company_name}}",
    content="Founded: {{founded_year}}\nLocation: {{location}}"
)

# Export the template configuration
creator.export_template_config(template, "new_template_config.json")
```

### Working with Images and Tables

```python
# Fill a template with images and tables
data = {
    "company_name": "Acme Corp",
    "logo": "https://example.com/logo.png",  # This will replace image placeholders
    "team": [  # This will fill tables
        {"name": "John", "role": "CEO"},
        {"name": "Jane", "role": "CTO"},
        {"name": "Bob", "role": "CFO"}
    ]
}

filler.fill_template(presentation, data)
```

### Direct Filling Without Configuration

```python
# Directly fill a presentation with data (without using a config file)
presentation = filler.create_from_template(template_id, title="Direct Filling")
filler.fill_template(presentation, data)
```

## API Structure

### Main Components

- **SlidesClient**: Core client for interacting with Google Slides API
- **TemplateConverter**: Converts existing presentations into templates
- **TemplateCreator**: Creates templates and manages placeholder configurations
- **TemplateFiller**: Fills templates with data to create new presentations

### Helper Classes

- **Presentation**: Represents a Google Slides presentation
- **Slide**: Represents a slide in a presentation
- **Element**: Base class for elements in a slide (shapes, images, tables, etc.)

## Authentication Options

Google Slides Templater supports multiple authentication methods:

### OAuth 2.0 Authentication

```python
credentials = authenticate(
    credentials_path="credentials.json",  # OAuth client credentials
    token_path="token.json"               # Path to save/load tokens
)
```

### Service Account Authentication

```python
credentials = authenticate(
    service_account_file="service-account.json"
)
```

### Default Credentials

```python
# Uses environment variables or application default credentials
credentials = authenticate()
```

## Error Handling

```python
from gslides_templater.client import APIError

try:
    template = converter.convert_presentation(presentation_id, replacements)
except APIError as e:
    print(f"API Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Details: {e.details}")
except Exception as e:
    print(f"Error: {e}")
```
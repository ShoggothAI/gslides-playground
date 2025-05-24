# Google Slides Templater

A simple and powerful Python library for working with Google Slides API. Create presentations, templates, and automate slide generation with full Markdown support.

## Features

- **Create and edit presentations** programmatically
- **Full Markdown support** - convert Markdown to Google Slides formatting
- **Smart template system** with automatic placeholder detection
- **Batch presentation processing**
- **Simple authentication** - supports multiple credential types
- **Minimal dependencies** - clean and lightweight

## Installation

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Optional (for enhanced Markdown support):
```bash
pip install markdown
```

## Quick Start

### 1. Authentication Setup

Choose one of the authentication methods:

#### Option A: Service Account (Recommended for automation)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Slides API and Google Drive API
4. Create a Service Account and download JSON credentials
5. Save as `service_account.json`

#### Option B: OAuth (Recommended for personal use)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 Client ID (Desktop application)
3. Download credentials and save as `credentials.json`

### 2. Basic Usage

```python
from gslides_templater import create_templater

# Initialize with service account
templater = create_templater(service_account_path='service_account.json')

# Or with OAuth
templater = create_templater(
    oauth_credentials_path='credentials.json',
    token_path='token.json'
)

# Create a new presentation
presentation_id = templater.create_presentation("My Report")

# Add a slide with Markdown content
templater.add_markdown_slide(presentation_id, '''
# Sales Report Q4 2024

## Key Metrics

Sales increased by **25%** this quarter thanks to:
- New product launches
- Team expansion
- *Excellent* customer feedback

### Next Steps
- Expand to new markets
- Hire additional staff
- Continue innovation
''')

# Get presentation URL
url = templater.get_presentation_url(presentation_id)
print(f"Presentation: {url}")
```

### 3. Create Presentation from Markdown

```python
markdown_content = '''
# Introduction
Welcome to our quarterly review.

# Key Achievements
We exceeded all targets:
- Revenue: **$2.5M** (+25%)
- Customers: **10,000** (+40%)
- Satisfaction: **4.8/5** stars

# Future Plans
Next quarter we will focus on:
- Product development
- Market expansion
- Team growth
'''

# Each level 1 header (#) becomes a new slide
presentation_id = templater.create_presentation_from_markdown(
    markdown_content, 
    title="Q4 2024 Review"
)
```

## Template System

### Creating Templates

Extract templates from existing presentations:

```python
# Create template from existing presentation
template = templater.create_template(
    presentation_id="your_presentation_id",
    template_name="quarterly_report"
)

# Save template to file
templater.save_template(template, "quarterly_report.json")
```

### Using Templates

```python
# Load template
template = templater.load_template("quarterly_report.json")

# Prepare data (supports Markdown formatting)
quarterly_data = {
    "title": "# Q1 2025 Report",
    "summary": "Sales grew **30%** this quarter with excellent results across all metrics.",
    "metrics": """
## Key Numbers
- Revenue: **$3.2M**
- Growth: *+30% YoY*
- Customers: `12,500`
    """,
    "chart_image": "https://example.com/chart.png"
}

# Apply template with data
new_presentation_id = templater.apply_template(template, quarterly_data, "Q1 2025 Final Report")
```

### Template Validation

```python
# Validate data before applying
validation = templater.validate_template_data(template, quarterly_data)

if validation['valid']:
    print("Data is valid!")
else:
    print("Issues found:")
    for issue in validation['missing_placeholders']:
        print(f"- Missing: {issue}")
```

## Markdown Support

The library supports rich Markdown formatting:

```python
markdown_text = '''
# Header 1
## Header 2
### Header 3

**Bold text** and *italic text*

~~Strikethrough~~ text

`Inline code` formatting

- Bullet lists
- With multiple items
- And nested items

1. Numbered lists
2. Are also supported
3. With proper formatting

> Blockquotes for important information

[Links](https://example.com) and ![Images](https://example.com/image.jpg)
'''

templater.add_markdown_slide(presentation_id, markdown_text)
```

**Note:** Code blocks and some complex Markdown features are simplified for Google Slides compatibility.

## Advanced Features

### Batch Operations

```python
# Create multiple presentations from template
template = templater.load_template("report_template.json")

# Example data structure
quarters_data = {
    "Q1": {"revenue": "$3.2M", "growth": "30%"},
    "Q2": {"revenue": "$3.8M", "growth": "35%"},
    "Q3": {"revenue": "$4.1M", "growth": "40%"},
    "Q4": {"revenue": "$4.5M", "growth": "45%"}
}

presentations = []
for quarter, data in quarters_data.items():
    template_data = {
        "title": f"# {quarter} 2024 Report",
        "revenue": data["revenue"],
        "growth": data["growth"]
    }
    pres_id = templater.apply_template(template, template_data, f"{quarter} 2024 Report")
    presentations.append(pres_id)
```

### Presentation Management

```python
# Get presentation information
info = templater.get_presentation_info(presentation_id)
print(f"Title: {info['title']}")
print(f"Slides: {info['total_slides']}")
print(f"Elements: {info['total_elements']}")

# Copy/clone presentation
new_id = templater.clone_presentation(presentation_id, "Copy of Original")

# Add text boxes with custom positioning
text_box_id = templater.add_text_box(
    presentation_id, slide_id,
    text="**Custom positioned text**",
    x=100, y=200,  # Position in points
    width=400, height=100  # Size in points
)

# Update text in existing elements
templater.set_text(presentation_id, text_box_id, "# Updated content with **Markdown**")

# Replace images
templater.replace_image(presentation_id, image_id, "https://example.com/new-image.jpg")
```

### Template Information

```python
# Get template details
template_info = templater.get_template_info(template)
print(f"Template: {template_info['name']}")
print(f"Placeholders: {template_info['total_placeholders']}")

# Generate sample data for template
sample_data = templater.create_sample_data(template)
print("Sample data structure:", sample_data)

# Preview changes before applying
preview = templater.preview_template_application(template, quarterly_data)
for change in preview['changes']:
    print(f"Slide {change['slide']}: {change['placeholder']} -> {change['new_value'][:50]}...")
```

## Authentication Details

### Service Account
```python
templater = create_templater(service_account_path='path/to/service_account.json')
```

### OAuth Flow
```python
templater = create_templater(
    oauth_credentials_path='path/to/credentials.json',
    token_path='path/to/token.json'  # Token will be saved here
)
```

### Application Default Credentials
```python
# Uses default credentials from environment
templater = create_templater()
```

### Manual Authentication
```python
from gslides_templater import authenticate, SlidesTemplater

credentials = authenticate(
    service_account_file='service_account.json',
    # or oauth_credentials_path='credentials.json',
    # token_path='token.json'
)

templater = SlidesTemplater(credentials)
```

## Error Handling

```python
try:
    presentation_id = templater.create_presentation("Test")
except FileNotFoundError:
    print("Credentials file not found")
except ValueError as e:
    print(f"Authentication failed: {e}")
except Exception as e:
    print(f"API error: {e}")
```

## Examples

Check the `examples/` directory for complete examples:

- `example_1_create_template.py` - Create template from existing presentation
- `example_2_apply_template.py` - Apply template with data
## API Reference

### SlidesTemplater Class

#### Core Methods
- `create_presentation(title)` - Create new presentation
- `get_presentation(presentation_id)` - Get presentation data
- `copy_presentation(presentation_id, title)` - Copy presentation
- `clone_presentation(presentation_id, title=None)` - Clone presentation (alias for copy)
- `get_presentation_url(presentation_id)` - Get presentation URL

#### Slide Methods
- `add_markdown_slide(presentation_id, markdown_content, slide_index=None)` - Add slide with Markdown
- `create_presentation_from_markdown(markdown_content, title)` - Create presentation from Markdown
- `add_text_box(presentation_id, slide_id, text, x, y, width, height)` - Add text box

#### Content Methods
- `set_text(presentation_id, element_id, text)` - Set element text with Markdown support
- `replace_image(presentation_id, image_id, new_url)` - Replace image by URL
- `batch_update(presentation_id, requests)` - Execute batch updates

#### Template Methods
- `create_template(presentation_id, template_name)` - Extract template from presentation
- `apply_template(template, data, title=None)` - Apply template with data
- `save_template(template, filename)` - Save template to file
- `load_template(filename)` - Load template from file
- `validate_template_data(template, data)` - Validate template data
- `preview_template_application(template, data)` - Preview template changes

#### Utility Methods
- `get_presentation_info(presentation_id)` - Get presentation information
- `get_template_info(template)` - Get template information
- `create_sample_data(template)` - Generate sample data for template

### Authentication Functions
- `authenticate(**kwargs)` - Universal authentication
- `setup_oauth_flow(client_secrets_file, token_save_path)` - Setup OAuth
- `validate_credentials(credentials)` - Validate credentials
- `create_service_account_template(output_file)` - Create service account template
- `create_oauth_template(output_file)` - Create OAuth template
- `check_credentials_file(file_path)` - Check credentials file validity

### Markdown Processing Functions
- `markdown_to_slides_elements(markdown_text)` - Convert Markdown to Slides elements
- `slides_elements_to_markdown(elements)` - Convert Slides elements to Markdown
- `clean_markdown_for_slides(text)` - Clean text for Slides compatibility

## Markdown Limitations

While the library supports rich Markdown formatting, some features are adapted for Google Slides compatibility:

- **Supported:** Headers, bold, italic, strikethrough, inline code, lists, quotes, links, images
- **Limited:** Code blocks are converted to inline code formatting
- **Not supported:** Tables, complex nested formatting, HTML tags

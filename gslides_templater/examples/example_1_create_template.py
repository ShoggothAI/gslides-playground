"""
Example 1: Creating a template file from a presentation ID

This example shows how to:
- Take an existing presentation by ID
- Analyze its structure
- Create template configuration with Markdown conversion
- Save to JSON file
"""

import sys
import os

# Add path to our package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gslides_templater import create_templater


def main():
    """Create template file from existing presentation"""

    print("🎯 Creating template file from presentation")
    print("=" * 45)

    try:
        # Initialize templater with OAuth credentials
        print("🔑 Setting up authentication...")

        # Check for credentials file
        credentials_file = "credentials.json"
        if not os.path.exists(credentials_file):
            credentials_file = "credentials.json"

        if not os.path.exists(credentials_file):
            print("❌ File credentials.json not found!")
            print("   Create OAuth credentials in Google Cloud Console")
            print("   and save as credentials.json")
            return

        templater = create_templater(
            oauth_credentials_path=credentials_file,
            token_path="token.json"  # Token will be saved here
        )
        print("   ✓ Authentication successful")

        user_input = input("Presentation ID: ").strip()

        source_presentation_id = user_input

        print(f"\n📋 Analyzing presentation...")
        print(f"   ID: {source_presentation_id}")

        # Get presentation information
        presentation_data = templater.get_presentation(source_presentation_id)

        print(f"   ✓ Title: {presentation_data.get('title', 'Untitled')}")
        print(f"   ✓ Slides: {len(presentation_data.get('slides', []))}")

        print(f"\n🔍 Creating template configuration with Markdown...")

        # Analyze presentation and create template
        template_config = templater.create_template(
            presentation_id=source_presentation_id,
            template_name="presentation_template"
        )

        print(f"   ✓ Found replaceable elements: {len(template_config.get('placeholders', {}))}")
        print(f"   ✓ Processed slides: {len(template_config.get('slides', []))}")

        # Show found placeholders
        placeholders = template_config.get('placeholders', {})
        if placeholders:
            print(f"\n📝 Found placeholders:")
            for name, info in placeholders.items():
                print(f"   • {name}")
                print(f"     Type: {info['type']}")
                print(f"     Description: {info['description']}")

                # Show Markdown example
                markdown_example = info.get('example', '')
                if markdown_example:
                    example_short = markdown_example[:100] + '...' if len(markdown_example) > 100 else markdown_example
                    print(f"     Markdown: {example_short}")

                # Show original example
                original_example = info.get('original_example', '')
                if original_example and original_example != markdown_example:
                    orig_short = original_example[:50] + '...' if len(original_example) > 50 else original_example
                    print(f"     Original: {orig_short}")
                print()
        else:
            print(f"\n⚠️  No placeholders found")
            print(f"   Presentation may not contain replaceable elements")

        print(f"💾 Saving template to file...")

        # Save configuration to file
        template_filename = "presentation_template.json"
        templater.save_template(template_config, template_filename)

        print(f"   ✓ File created: {template_filename}")

        # Show file structure
        print(f"\n📊 Created template structure:")
        print(f"   Name: {template_config['name']}")
        print(f"   Source presentation: {template_config['source_presentation_id']}")
        print(f"   Created at: {template_config.get('created_at')}")
        print(f"   Slides with replaceable elements: {len(template_config.get('slides', []))}")
        print(f"   Total placeholders: {len(template_config.get('placeholders', {}))}")

        # Show usage example
        print(f"\n📖 Example data for filling template:")
        print(f"   {{")
        for name, info in list(placeholders.items())[:3]:  # Show only first 3
            if info['type'] == 'text':
                print(f'       "{name}": "# New Header\\n\\nNew **text** with formatting",')
            elif info['type'] == 'image':
                print(f'       "{name}": "https://example.com/new-image.jpg",')
        if len(placeholders) > 3:
            print(f"       # ... {len(placeholders) - 3} more placeholders")
        print(f"   }}")

        print(f"\n✅ Template created successfully!")
        print(f"📁 File: {template_filename}")
        print(f"🔄 You can now use this file to create new presentations")

        # Source presentation URL
        presentation_url = templater.get_presentation_url(source_presentation_id)
        print(f"🌐 Source presentation: {presentation_url}")

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print(f"   Make sure credentials.json file exists")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {error_msg}")

        # Specific errors
        if "404" in error_msg or "not found" in error_msg.lower():
            print(f"\n🔧 Presentation not found:")
            print(f"   1. Check presentation ID is correct")
            print(f"   2. Make sure you have access to the presentation")
            print(f"   3. Presentation must be created in Google Slides")
            print(f"   4. ID should look like: 1KNhH44DjD72rjgx1EadpP43zOgpZGYIScMfnOYyzLys")

        elif "403" in error_msg or "permission" in error_msg.lower():
            print(f"\n🔧 Access denied:")
            print(f"   1. Presentation must be accessible to your account")
            print(f"   2. Check presentation access permissions")
            print(f"   3. Make sure OAuth credentials are configured correctly")

        elif "credentials" in error_msg.lower() or "auth" in error_msg.lower():
            print(f"\n🔧 Authentication issues:")
            print(f"   1. Check credentials.json file")
            print(f"   2. Make sure OAuth Client ID is created in Google Cloud Console")
            print(f"   3. Add required scopes for Google Slides API")
            print(f"   4. Delete token.json and try again")

        else:
            print(f"\n🔧 Possible causes:")
            print(f"   1. Internet connection issues")
            print(f"   2. Invalid credentials")
            print(f"   3. API request limit exceeded")
            print(f"   4. Google Slides API not enabled in project")


if __name__ == "__main__":
    main()
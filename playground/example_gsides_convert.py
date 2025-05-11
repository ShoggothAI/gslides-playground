"""
Example of correct usage of Google Slides Templater library.
"""

import json
from gslides_templater import SlidesClient, authenticate
from gslides_templater.templates import TemplateConverter, TemplateFiller, TemplateCreator

def main():
    """Standard workflow for creating and using a template."""
    # Source presentation ID
    source_presentation_id = "1EAYk18WDjIG-zp_0vLm3CsfQh_i8eXc67Jo2O9C6Vuc"

    # Paths to authentication files
    credentials_path = "../credentials.json" # TODO
    token_path = "token.json"

    # Path to save template configuration
    template_config_path = "template_config.json"

    # Sample data for filling in the template
    sample_data = {
        "person_name_1": "Alexander Pushkin",
        "person_name_2": "Family archive",
        "bath_time_is_so_much_fun": "Test text 1",
        "look_at_what_granny_got_me_for": "Test text 2",
        "my_first_fast_food_restaurant_": "Test text 3",
    }

    try:
        # Authentication with Google API
        credentials = authenticate(
        credentials_path=credentials_path,
        token_path=token_path
        )
        client = SlidesClient(credentials)

        # ====== PRESENTATION TEMPLATION ======

        print(f"1. Getting the original presentation...")
        original = client.get_presentation(source_presentation_id)

        print(f"2. Analysis and conversion of the presentation into a template...")
        converter = TemplateConverter(client)

        # Automatically detect texts for replacement
        suggestions = converter.suggest_replacements(original)
        replacements = {}
        for text, placeholder in suggestions.items():
            replacements[text] = placeholder

        # Create a template
        template = converter.convert_presentation(
        source_presentation_id,
        replacements=replacements,
        title="Presentation template",
        create_copy=True
        )

        print(f"3. Template created: {template.url}")

        # Save the template configuration
        creator = TemplateCreator(client)
        creator.export_template_config(template, template_config_path)

        print(f"4. Template configuration saved in {template_config_path}")

        # ====== USING A TEMPLATE ======

        print(f"5. Creating a new presentation from a template...")
        filler = TemplateFiller(client)

        # Creating a new presentation from a template
        presentation = filler.create_from_template(
        template.presentation_id,
        title="Filled presentation"
        )

        print(f"6. Filling the presentation with data...")
        filler.fill_from_template_config(presentation, template_config_path, sample_data)

        print(f"7. Done! The filled presentation is available at the link:")
        print(presentation.url)

        # ====== SAVING INFORMATION FOR REUSE ======

        # Saving key information for reusing the template
        template_info = {
        "template_id": template.presentation_id,
        "template_url": template.url,
        "config_path": template_config_path
        }

        with open("template_info.json", "w") as f:
            json.dump(template_info, f, indent=2)

        print(f"8. Template information saved in template_info.json")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
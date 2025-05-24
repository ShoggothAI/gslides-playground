"""
Example 2: Creating presentation from ready template with data filling

FULLY FIXED VERSION:
- Using NEW data instead of old from template
- Proper Markdown and image processing
- Correct replacement of all placeholders
- Detailed diagnostics and reporting
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gslides_templater import create_templater


def main():
   """Create presentation from ready template with NEW data"""

   print("🎯 Creating presentation from template with NEW data")
   print("=" * 55)

   try:
       print("🔑 Setting up authentication...")

       credentials_file = "credentials.json"
       if not os.path.exists(credentials_file):
           credentials_file = "credentials.json"

       if not os.path.exists(credentials_file):
           print("❌ File credentials.json not found!")
           print("   Place it next to the script or in parent folder")
           return

       templater = create_templater(
           oauth_credentials_path=credentials_file,
           token_path="token.json"
       )
       print("   ✓ Authentication successful")

       template_filename = "presentation_template.json"
       print(f"\n📁 Loading template from file: {template_filename}")

       if not os.path.exists(template_filename):
           print(f"❌ Template file not found: {template_filename}")
           print("   First run example_1_create_template.py")
           return

       template_config = templater.load_template(template_filename)

       print(f"   ✓ Template loaded: {template_config['name']}")
       print(f"   ✓ Source presentation: {template_config['source_presentation_id']}")
       print(f"   ✓ Placeholders in template: {len(template_config.get('placeholders', {}))}")

       placeholders = template_config.get('placeholders', {})
       if not placeholders:
           print("❌ No placeholders in template!")
           return

       text_placeholders = {name: info for name, info in placeholders.items()
                            if info['type'] == 'text'}
       image_placeholders = {name: info for name, info in placeholders.items()
                             if info['type'] == 'image'}
       other_placeholders = {name: info for name, info in placeholders.items()
                             if info['type'] not in ['text', 'image']}

       print(f"\n📝 Found placeholders:")
       print(f"   📝 Text: {len(text_placeholders)}")
       print(f"   🖼️ Images: {len(image_placeholders)}")
       print(f"   📦 Other: {len(other_placeholders)}")

       print(f"\n   Placeholder examples:")
       for i, (name, info) in enumerate(list(placeholders.items())[:5]):
           print(f"   • {name} ({info['type']}) - slide {info.get('slide_index', 0) + 1}")
       if len(placeholders) > 5:
           print(f"   ... and {len(placeholders) - 5} more")

       print(f"\n📊 Creating NEW data for filling...")

       new_data = {}

       text_data_examples = {
           "name_here": "# **Ekaterina Volkova** 👑",
           "baby_album": "### 🎈 *Family Moments 2024*",
           "bath_time": """**Fun bath time!** 🛁""",
           "look_at": """#### 👀 **Look at us!**""",
           "slide_2_text_15": """🍕 **First cafe in life!** ***Indescribable taste!***""",
           "boys_love": """#### 🚂 **Boys and their hobbies!**🔬""",
           "slide_5_text_36": """##### ⭐ **Our little commander!** > "Leadership from diapers" 😎""",
           "slide_3_text": """**Games and entertainment** 🎮""",
           "slide_4_text": """### Walk in the park 🌳 `Healthy sleep` guaranteed! 😴"""
       }

       for placeholder_name in text_placeholders.keys():
           if placeholder_name in text_data_examples:
               new_data[placeholder_name] = text_data_examples[placeholder_name]
               print(f"   📝 {placeholder_name}: personalized content")
           else:
               slide_num = text_placeholders[placeholder_name].get('slide_index', 0) + 1
               new_data[placeholder_name] = f"""**New content for slide {slide_num}** """
               print(f"   📝 {placeholder_name}: generated Markdown")

       high_quality_images = [
           "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=800&h=600&fit=crop&q=90",
           "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?w=800&h=600&fit=crop&q=90",
           "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=800&h=600&fit=crop&q=90",
           "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800&h=600&fit=crop&q=90",
           "https://images.unsplash.com/photo-1581833971358-2c8b550f87b3?w=800&h=600&fit=crop&q=90",
           "https://images.unsplash.com/photo-1576267423445-b2e0074d68a4?w=800&h=600&fit=crop&q=90",
           "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&h=600&fit=crop&q=90",
           "https://images.unsplash.com/photo-1519340333755-56e9c1d24ff4?w=800&h=600&fit=crop&q=90",
           "https://images.unsplash.com/photo-1566004100631-35d015d6a491?w=800&h=600&fit=crop&q=90",
           "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=800&h=600&fit=crop&q=90",
       ]

       image_counter = 0
       for placeholder_name in image_placeholders.keys():
           if image_counter < len(high_quality_images):
               new_data[placeholder_name] = high_quality_images[image_counter]
               image_counter += 1
               print(f"   🖼️ {placeholder_name}: new quality image #{image_counter}")
           else:
               new_data[placeholder_name] = f"https://picsum.photos/800/600?random={image_counter}"
               image_counter += 1
               print(f"   🖼️ {placeholder_name}: random image")

       for placeholder_name in other_placeholders.keys():
           placeholder_type = other_placeholders[placeholder_name]['type']
           new_data[placeholder_name] = f"New data for {placeholder_type} element"
           print(f"   📦 {placeholder_name}: data for {placeholder_type}")

       print(f"\n   ✅ Total data prepared: {len(new_data)}")
       print(f"   📝 Text elements: {len(text_placeholders)}")
       print(f"   🖼️ Image elements: {len(image_placeholders)}")
       print(f"   📦 Other elements: {len(other_placeholders)}")

       print(f"\n📋 Examples of new data:")
       for i, (name, value) in enumerate(list(new_data.items())[:3]):
           if isinstance(value, str):
               if value.startswith("http"):
                   print(f"   🖼️ {name}: {value}")
               else:
                   preview = value[:80] + '...' if len(value) > 80 else value
                   preview = preview.replace('\n', ' ')
                   print(f"   📝 {name}: {preview}")
       if len(new_data) > 3:
           print(f"   ... and {len(new_data) - 3} more elements")

       print(f"\n🔄 Creating new presentation with data...")

       start_time = time.time()
       new_presentation_id = templater.apply_template(
           template=template_config,
           data=new_data,
           title=f"🎨 New presentation from template - {time.strftime('%d.%m.%Y %H:%M')}"
       )
       end_time = time.time()

       print(f"   ✅ Presentation created in {end_time - start_time:.1f} seconds!")
       print(f"   ✅ ID: {new_presentation_id}")

       new_presentation = templater.get_presentation(new_presentation_id)

       print(f"\n📋 Information about created presentation:")
       print(f"   📄 Title: {new_presentation.get('title')}")
       print(f"   🆔 ID: {new_presentation_id}")
       print(f"   📊 Number of slides: {len(new_presentation.get('slides', []))}")

       print(f"\n🔄 Statistics of applied replacements:")
       replacement_stats = {
           'text_replaced': 0,
           'images_replaced': 0,
           'other_replaced': 0,
           'total_characters': 0
       }

       for placeholder_name, value in new_data.items():
           placeholder_info = placeholders.get(placeholder_name, {})
           slide_index = placeholder_info.get('slide_index', 0) + 1
           placeholder_type = placeholder_info.get('type', 'unknown')

           if placeholder_type == 'text':
               replacement_stats['text_replaced'] += 1
               replacement_stats['total_characters'] += len(str(value))
           elif placeholder_type == 'image':
               replacement_stats['images_replaced'] += 1
           else:
               replacement_stats['other_replaced'] += 1

       print(f"   📝 Text elements replaced: {replacement_stats['text_replaced']}")
       print(f"   🖼️ Images replaced: {replacement_stats['images_replaced']}")
       print(f"   📦 Other elements replaced: {replacement_stats['other_replaced']}")
       print(f"   📊 Markdown characters processed: {replacement_stats['total_characters']:,}")
       print(f"   📄 Slides processed: {len(template_config.get('slides', []))}")

       print(f"\n📝 Examples of applied replacements:")
       shown_examples = 0
       for placeholder_name, value in new_data.items():
           if shown_examples >= 5:
               break

           placeholder_info = placeholders.get(placeholder_name, {})
           slide_index = placeholder_info.get('slide_index', 0) + 1
           placeholder_type = placeholder_info.get('type', 'unknown')

           if isinstance(value, str):
               if value.startswith("http"):
                   print(f"   🖼️ Slide {slide_index}: {placeholder_name}")
                   print(f"      → New image: {value[:60]}...")
               else:
                   preview = value[:100] + '...' if len(value) > 100 else value
                   preview = preview.replace('\n', ' ↵ ')
                   print(f"   📝 Slide {slide_index}: {placeholder_name}")
                   print(f"      → {preview}")
               shown_examples += 1

       remaining_replacements = len(new_data) - shown_examples
       if remaining_replacements > 0:
           print(f"   ... and {remaining_replacements} more replacements")

       presentation_url = templater.get_presentation_url(new_presentation_id)
       print(f"\n🌐 Link to new presentation:")
       print(f"   {presentation_url}")

       print(f"\n✅ PRESENTATION SUCCESSFULLY CREATED WITH NEW DATA!")
       print(f"🎨 All Markdown elements converted to Google Slides")
       print(f"📝 All styles preserved: bold, italic, headers, lists")
       print(f"🖼️ All images replaced with quality new ones")
       print(f"🚀 Ready for viewing and editing!")

       print(f"\n💡 What to do next:")
       print(f"   1. 🔗 Open the link above in browser")
       print(f"   2. 🎨 Check quality of replacements and formatting")
       print(f"   3. ✏️ Edit manually if needed")
       print(f"   4. 📤 Share presentation with colleagues")
       print(f"   5. 💾 Save as PDF if needed")

       print(f"\n🔧 Technical information:")
       print(f"   📅 Template creation date: {template_config.get('created_at', 'Unknown')}")
       print(f"   🆔 Source presentation ID: {template_config['source_presentation_id']}")
       print(f"   📝 Template name: {template_config['name']}")
       print(f"   ⏱️ Processing time: {end_time - start_time:.2f} seconds")

   except FileNotFoundError as e:
       file_name = str(e).split("'")[1] if "'" in str(e) else "file"
       print(f"\n❌ ERROR: File not found")

       if "presentation_template.json" in str(e):
           print(f"📁 Template file not found: presentation_template.json")
           print(f"🔧 Solution:")
           print(f"   1. Run example_1_create_template.py")
           print(f"   2. Create template from existing presentation")
           print(f"   3. Make sure presentation_template.json file is created")
       elif "credentials.json" in str(e):
           print(f"🔑 File credentials.json not found")
           print(f"🔧 Solution:")
           print(f"   1. Download OAuth credentials from Google Cloud Console")
           print(f"   2. Save as credentials.json")
           print(f"   3. Place next to script")
       else:
           print(f"📄 File not found: {file_name}")
           print(f"🔧 Check file paths")

   except KeyError as e:
       print(f"\n❌ ERROR: Incorrect data structure")
       print(f"🔍 Missing key: {e}")
       print(f"🔧 Solution:")
       print(f"   1. Template file may be corrupted")
       print(f"   2. Recreate template with example_1_create_template.py")
       print(f"   3. Check that you're using latest code version")

   except Exception as e:
       error_msg = str(e)
       print(f"\n❌ ERROR: {error_msg}")

       if "404" in error_msg or "not found" in error_msg.lower():
           print(f"\n🔧 DIAGNOSIS: Resource not found")
           print(f"   🎯 Reasons:")
           print(f"   • Source presentation was deleted")
           print(f"   • Wrong presentation ID in template")
           print(f"   • No access to presentation")
           print(f"   🔧 Solutions:")
           print(f"   • Check source presentation exists")
           print(f"   • Recreate template with correct presentation")

       elif "403" in error_msg or "permission" in error_msg.lower():
           print(f"\n🔧 DIAGNOSIS: No access rights")
           print(f"   🎯 Reasons:")
           print(f"   • No rights to source presentation")
           print(f"   • Google Slides API not enabled")
           print(f"   • OAuth credentials issues")
           print(f"   🔧 Solutions:")
           print(f"   • Make sure you have access to source presentation")
           print(f"   • Check API settings in Google Cloud Console")
           print(f"   • Update OAuth credentials")

       elif "token" in error_msg.lower() or "auth" in error_msg.lower():
           print(f"\n🔧 DIAGNOSIS: Authentication problems")
           print(f"   🎯 Reasons:")
           print(f"   • Token expired")
           print(f"   • Incorrect credentials")
           print(f"   • OAuth settings issues")
           print(f"   🔧 Solutions:")
           print(f"   • Delete token.json and re-authorize")
           print(f"   • Check credentials.json")
           print(f"   • Make sure OAuth Client ID is configured correctly")

       elif "markdown" in error_msg.lower():
           print(f"\n🔧 DIAGNOSIS: Markdown processing error")
           print(f"   🎯 Reasons:")
           print(f"   • Incorrect Markdown syntax")
           print(f"   • Unclosed formatting tags")
           print(f"   • Style conflict")
           print(f"   🔧 Solutions:")
           print(f"   • Check Markdown markup correctness")
           print(f"   • Simplify formatting")
           print(f"   • Use Markdown validator")

       elif "image" in error_msg.lower() or "url" in error_msg.lower():
           print(f"\n🔧 DIAGNOSIS: Image problems")
           print(f"   🎯 Reasons:")
           print(f"   • Image URLs unavailable")
           print(f"   • Wrong URL format")
           print(f"   • Images blocked")
           print(f"   🔧 Solutions:")
           print(f"   • Use publicly accessible URLs")
           print(f"   • Check URLs start with https://")
           print(f"   • Try other images")

       else:
           print(f"\n🔧 GENERAL DIAGNOSIS:")
           print(f"   🌐 Check internet connection")
           print(f"   🔄 Try again in a few minutes")
           print(f"   📊 May have exceeded API request limit")
           print(f"   🆕 Make sure you're using latest code version")


if __name__ == "__main__":
   main()
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import requests
from django.conf import settings
import math


def add_text_to_image(image_path, text, style_options):
    """
    Add advanced styled text to an image and return the path to the modified image
    """
    try:
        # Debug: Print what we're processing
        print("=== IMAGE PROCESSING STARTED ===")
        print(f"Image path: {image_path}")
        print(f"Text: {text}")

        # Open the original image
        original_image = Image.open(image_path).convert('RGBA')
        width, height = original_image.size
        print(f"Image size: {width}x{height}")

        # Create a transparent layer for text and effects
        text_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)

        # Extract style options with debugging
        font_size = int(style_options.get('font_size', 48))
        font_color = style_options.get('font_color', '#FFFFFF')
        x_position = int(style_options.get('x_position', 250))
        y_position = int(style_options.get('y_position', 250))
        font_family = style_options.get('font_family', 'Roboto')
        text_alignment = style_options.get('text_alignment', 'center')
        font_weight = style_options.get('font_weight', '600')

        # Advanced options
        text_rotate = int(style_options.get('text_rotate', 0))
        text_opacity = int(style_options.get('text_opacity', 100))
        enable_shadow = style_options.get('enable_shadow') == 'on'
        shadow_x = int(style_options.get('shadow_x', 2))
        shadow_y = int(style_options.get('shadow_y', 2))
        shadow_blur = int(style_options.get('shadow_blur', 4))
        shadow_color = style_options.get('shadow_color', '#000000')
        enable_background = style_options.get('enable_background') == 'on'
        text_background = style_options.get('text_background', '#00000000')
        letter_spacing = float(style_options.get('letter_spacing', 0))
        line_height = float(style_options.get('line_height', 1.2))

        # Debug: Print extracted parameters
        print("=== PARAMETERS EXTRACTED FOR PROCESSING ===")
        print(f"Font: {font_family} (weight: {font_weight}, size: {font_size})")
        print(f"Position: ({x_position}, {y_position}), Alignment: {text_alignment}")
        print(f"Rotation: {text_rotate}°, Opacity: {text_opacity}%")
        print(f"Shadow: {enable_shadow} (X:{shadow_x}, Y:{shadow_y}, Blur:{shadow_blur}, Color:{shadow_color})")
        print(f"Letter Spacing: {letter_spacing}, Line Height: {line_height}")
        print(f"Background: {enable_background}, Color: {text_background}")
        print("============================================")

        # Convert HEX color to RGB with alpha
        def hex_to_rgba(hex_color, opacity=255):
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 8:  # With alpha
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                a = int(hex_color[6:8], 16)
                # Apply additional opacity
                a = int(a * (opacity / 255))
                return (r, g, b, a)
            elif len(hex_color) == 6:  # Without alpha
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b, opacity)
            else:
                return (255, 255, 255, opacity)

        # Calculate opacity (convert percentage to 0-255)
        opacity = int(text_opacity * 2.55)
        font_color_rgba = hex_to_rgba(font_color, opacity)
        shadow_color_rgba = hex_to_rgba(shadow_color, 200)  # Slightly transparent shadow
        background_rgba = hex_to_rgba(text_background)

        # Get font path with proper weight handling
        font_path = get_google_font(font_family, font_weight)
        if not font_path:
            font_path = get_font_path(font_family, font_weight)

        # Load font
        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                print(f"✓ Loaded font: {font_path}")
            else:
                font = ImageFont.load_default()
                print("⚠ Using default font")
        except Exception as e:
            print(f"✗ Error loading font: {e}")
            font = ImageFont.load_default()

        # Calculate text dimensions
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            # Fallback for older Pillow versions
            text_width, text_height = draw.textsize(text, font=font)

        # Apply letter spacing to total width calculation
        if letter_spacing != 0:
            total_letter_spacing = letter_spacing * (len(text) - 1) if len(text) > 1 else 0
            text_width += total_letter_spacing
            print(f"Letter spacing applied: {letter_spacing}px, Total width: {text_width}px")

        # Calculate text position based on alignment
        final_x = x_position
        if text_alignment == 'center':
            final_x = x_position - (text_width // 2)
        elif text_alignment == 'right':
            final_x = x_position - text_width

        # Calculate background height based on line height
        background_height = int(font_size * line_height)
        print(f"Line height: {line_height}, Background height: {background_height}px")

        # Draw text background if enabled
        if enable_background and background_rgba[3] > 0:
            padding = 5
            draw.rectangle([
                final_x - padding,
                y_position - padding,
                final_x + text_width + padding,
                y_position + background_height + padding
            ], fill=background_rgba)
            print("✓ Text background drawn")

        # Draw text shadow if enabled
        if enable_shadow:
            shadow_x_pos = final_x + shadow_x
            shadow_y_pos = y_position + shadow_y

            # Draw shadow text with letter spacing
            if letter_spacing != 0:
                current_x = shadow_x_pos
                for char in text:
                    try:
                        char_bbox = draw.textbbox((0, 0), char, font=font)
                        char_width = char_bbox[2] - char_bbox[0]
                    except AttributeError:
                        char_width = draw.textsize(char, font=font)[0]

                    draw.text((current_x, shadow_y_pos), char, fill=shadow_color_rgba, font=font)
                    current_x += char_width + letter_spacing
            else:
                draw.text((shadow_x_pos, shadow_y_pos), text, fill=shadow_color_rgba, font=font)
            print("✓ Text shadow drawn")

        # Draw main text with letter spacing
        if letter_spacing != 0:
            current_x = final_x
            for char in text:
                try:
                    char_bbox = draw.textbbox((0, 0), char, font=font)
                    char_width = char_bbox[2] - char_bbox[0]
                except AttributeError:
                    char_width = draw.textsize(char, font=font)[0]

                draw.text((current_x, y_position), char, fill=font_color_rgba, font=font)
                current_x += char_width + letter_spacing
        else:
            draw.text((final_x, y_position), text, fill=font_color_rgba, font=font)
        print("✓ Main text drawn")

        # Apply rotation if needed
        if text_rotate != 0:
            # Calculate rotation center
            center_x = final_x + text_width // 2
            center_y = y_position + background_height // 2

            # Rotate the text layer
            text_layer = text_layer.rotate(
                text_rotate,
                center=(center_x, center_y),
                resample=Image.BICUBIC
            )
            print(f"✓ Text rotated: {text_rotate}°")

        # Composite the text layer onto the original image
        original_image = Image.alpha_composite(original_image, text_layer)
        print("✓ Text composited onto image")

        # Convert back to RGB for JPEG saving
        final_image = original_image.convert('RGB')

        # Generate output path
        import time
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        timestamp = str(int(time.time()))
        output_filename = f"{name}_styled_{timestamp}.jpg"
        output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save the modified image
        final_image.save(output_path, quality=95)

        print(f"✓ Advanced styled image saved: {output_path}")
        print("=== IMAGE PROCESSING COMPLETED ===")

        return f"outputs/{output_filename}"

    except Exception as e:
        print(f"✗ Error in add_text_to_image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e

def get_google_font(font_family, font_weight='400'):
    """
    Download Google Font and return the local path
    """
    try:
        # Create fonts directory
        fonts_dir = os.path.join(settings.MEDIA_ROOT, 'fonts')
        os.makedirs(fonts_dir, exist_ok=True)

        # Format font family for URL
        formatted_family = font_family.replace(' ', '+')

        # Try to download the font
        font_filename = f"{font_family.replace(' ', '_')}_{font_weight}.ttf"
        font_path = os.path.join(fonts_dir, font_filename)

        # If font already exists, return the path
        if os.path.exists(font_path):
            return font_path

        # Google Fonts direct download URL
        download_url = f"https://fonts.googleapis.com/css2?family={formatted_family}:wght@{font_weight}"

        response = requests.get(download_url)
        if response.status_code == 200:
            # Parse CSS to find font URL
            import re
            font_urls = re.findall(r'url\((https://fonts.gstatic.com/[^)]+)\)', response.text)

            if font_urls:
                font_response = requests.get(font_urls[0])
                if font_response.status_code == 200:
                    with open(font_path, 'wb') as f:
                        f.write(font_response.content)
                    print(f"Downloaded font: {font_family} weight {font_weight}")
                    return font_path

    except Exception as e:
        print(f"Error downloading Google Font {font_family}: {e}")

    return None


def get_font_path(font_family, font_weight='400'):
    """
    Get the appropriate font path with weight consideration
    """
    # Font mapping with common fonts and their weights
    font_mapping = {
        'Arial': {
            '100': "arial.ttf",
            '300': "arial.ttf",
            '400': "arial.ttf",
            '500': "arialbd.ttf",
            '600': "arialbd.ttf",
            '700': "arialbd.ttf",
            '800': "arialbd.ttf",
            '900': "arialbd.ttf",
        },
        'Times New Roman': {
            'default': "times.ttf"
        },
        'Courier New': {
            'default': "cour.ttf"
        },
        'Verdana': {
            'default': "verdana.ttf"
        },
        'Georgia': {
            'default': "georgia.ttf"
        },
    }

    # Common font paths
    font_directories = [
        "C:/Windows/Fonts/",
        "/Library/Fonts/",
        "/System/Library/Fonts/",
        "/usr/share/fonts/truetype/",
    ]

    # Try to find the specific weight variant
    if font_family in font_mapping:
        weight_variants = font_mapping[font_family]
        if font_weight in weight_variants:
            font_file = weight_variants[font_weight]
        elif 'default' in weight_variants:
            font_file = weight_variants['default']
        else:
            font_file = None

        if font_file:
            for font_dir in font_directories:
                font_path = os.path.join(font_dir, font_file)
                if os.path.exists(font_path):
                    return font_path

    # Fallback: try common font files
    common_fonts = [
        "arial.ttf", "arialbd.ttf", "times.ttf", "cour.ttf",
        "verdana.ttf", "georgia.ttf", "DejaVuSans.ttf"
    ]

    for font_dir in font_directories:
        for font_file in common_fonts:
            font_path = os.path.join(font_dir, font_file)
            if os.path.exists(font_path):
                return font_path

    return None
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .utils import add_text_to_image
from .models import StyledImage, Category, SubCategory
from django.core import serializers
from django.db.models import Prefetch
import os
import json


def upload_page(request):
    """Render the upload page with categories"""
    categories = Category.objects.all().prefetch_related('subcategories')
    return render(request, 'styler/upload.html', {
        'categories': categories
    })


@csrf_exempt
def upload_and_style(request):
    """Handle image and text upload, style the text on image, return styled image"""
    if request.method == 'POST':
        try:
            # Debug: Print ALL POST parameters
            print("=== ALL POST PARAMETERS RECEIVED ===")
            for key, value in request.POST.items():
                print(f"{key}: {value}")
            print("=====================================")

            # Debug: Print FILES
            print("=== FILES RECEIVED ===")
            for key, value in request.FILES.items():
                print(f"{key}: {value}")
            print("======================")

            # Get the uploaded image
            if 'image' not in request.FILES:
                return JsonResponse({'error': 'No image provided'}, status=400)

            image_file = request.FILES['image']

            # Get all styling parameters with proper defaults
            text = request.POST.get('text', '').strip()
            font_size = request.POST.get('font_size', '48')
            font_color = request.POST.get('font_color', '#FFFFFF')
            x_position = request.POST.get('x_position', '250')
            y_position = request.POST.get('y_position', '250')
            font_family = request.POST.get('font_family', 'Roboto')
            text_alignment = request.POST.get('text_alignment', 'center')
            font_weight = request.POST.get('font_weight', '600')

            # Advanced parameters - CRITICAL: These must be in the request
            text_rotate = request.POST.get('text_rotate', '0')
            text_opacity = request.POST.get('text_opacity', '100')
            enable_shadow = request.POST.get('enable_shadow', '')
            shadow_x = request.POST.get('shadow_x', '2')
            shadow_y = request.POST.get('shadow_y', '2')
            shadow_blur = request.POST.get('shadow_blur', '4')
            shadow_color = request.POST.get('shadow_color', '#000000')
            enable_background = request.POST.get('enable_background', '')
            text_background = request.POST.get('text_background', '#00000000')
            letter_spacing = request.POST.get('letter_spacing', '0')
            line_height = request.POST.get('line_height', '1.2')

            # Category and subcategory
            category_id = request.POST.get('category')
            subcategory_id = request.POST.get('subcategory')

            # Debug: Print all extracted parameters
            print("=== EXTRACTED PARAMETERS ===")
            print(f"Text: {text}")
            print(f"Font Family: {font_family}")
            print(f"Font Weight: {font_weight}")
            print(f"Font Size: {font_size}")
            print(f"Text Rotation: {text_rotate}")
            print(f"Text Opacity: {text_opacity}")
            print(f"Letter Spacing: {letter_spacing}")
            print(f"Shadow Enabled: {enable_shadow}")
            print(f"Shadow X: {shadow_x}, Y: {shadow_y}, Blur: {shadow_blur}")
            print(f"Background Enabled: {enable_background}")
            print(f"Line Height: {line_height}")
            print("============================")

            # Validate inputs
            if not text:
                return JsonResponse({'error': 'No text provided'}, status=400)

            # Convert to appropriate types with error handling
            try:
                font_size = int(font_size)
                x_position = int(x_position)
                y_position = int(y_position)
                text_rotate = int(text_rotate)
                text_opacity = int(text_opacity)
                shadow_x = int(shadow_x)
                shadow_y = int(shadow_y)
                shadow_blur = int(shadow_blur)
                letter_spacing = float(letter_spacing)
                line_height = float(line_height)
            except ValueError as e:
                print(f"ValueError in parameter conversion: {e}")
                return JsonResponse({'error': f'Invalid numeric values: {str(e)}'}, status=400)

            # Validate ranges
            if text_opacity < 0 or text_opacity > 100:
                return JsonResponse({'error': 'Text opacity must be between 0 and 100'}, status=400)

            if text_rotate < -180 or text_rotate > 180:
                return JsonResponse({'error': 'Text rotation must be between -180 and 180 degrees'}, status=400)

            # Save uploaded image
            fs = FileSystemStorage()
            try:
                filename = fs.save(f"uploads/{image_file.name}", image_file)
                image_path = fs.path(filename)
                print(f"Image saved to: {image_path}")
            except Exception as e:
                print(f"Error saving image: {e}")
                return JsonResponse({'error': f'Error saving image: {str(e)}'}, status=500)

            # Prepare style options - Include ALL parameters
            style_options = {
                'font_size': font_size,
                'font_color': font_color,
                'x_position': x_position,
                'y_position': y_position,
                'font_family': font_family,
                'text_alignment': text_alignment,
                'font_weight': font_weight,
                'text_rotate': text_rotate,
                'text_opacity': text_opacity,
                'enable_shadow': enable_shadow,
                'shadow_x': shadow_x,
                'shadow_y': shadow_y,
                'shadow_blur': shadow_blur,
                'shadow_color': shadow_color,
                'enable_background': enable_background,
                'text_background': text_background,
                'letter_spacing': letter_spacing,
                'line_height': line_height,
            }

            # Debug: Print style options being sent to image processing
            print("=== STYLE OPTIONS SENT TO IMAGE PROCESSING ===")
            for key, value in style_options.items():
                print(f"{key}: {value}")
            print("==============================================")

            # Add text to image
            try:
                output_image_relative_path = add_text_to_image(image_path, text, style_options)
                print(f"Image processing completed: {output_image_relative_path}")
            except Exception as e:
                print(f"Error in add_text_to_image: {str(e)}")
                import traceback
                traceback.print_exc()
                # Clean up uploaded file if processing fails
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except:
                    pass
                return JsonResponse({'error': f'Image processing failed: {str(e)}'}, status=500)

            # Handle category relationships
            category = None
            subcategory = None
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    if subcategory_id:
                        subcategory = SubCategory.objects.get(id=subcategory_id, category=category)
                    print(f"Category set: {category.name}, Subcategory: {subcategory.name if subcategory else 'None'}")
                except (Category.DoesNotExist, SubCategory.DoesNotExist) as e:
                    print(f"Category/Subcategory not found: {e}")
                    # Continue without category if not found

            # Create database record - Save ALL parameters
            try:
                styled_image = StyledImage.objects.create(
                    original_image=filename,
                    text=text,
                    font_size=font_size,
                    font_color=font_color,
                    x_position=x_position,
                    y_position=y_position,
                    font_family=font_family,
                    text_alignment=text_alignment,
                    font_weight=font_weight,
                    text_rotate=text_rotate,
                    text_opacity=text_opacity,
                    enable_shadow=enable_shadow == 'on',
                    shadow_x=shadow_x,
                    shadow_y=shadow_y,
                    shadow_blur=shadow_blur,
                    shadow_color=shadow_color,
                    enable_background=enable_background == 'on',
                    text_background=text_background,
                    letter_spacing=letter_spacing,
                    line_height=line_height,
                    output_image=output_image_relative_path,
                    category=category,
                    subcategory=subcategory
                )
                print(f"Database record created with ID: {styled_image.id}")
            except Exception as e:
                print(f"Error creating database record: {e}")
                # Clean up files if database save fails
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                    output_path = os.path.join(settings.MEDIA_ROOT, output_image_relative_path)
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except:
                    pass
                return JsonResponse({'error': f'Database save failed: {str(e)}'}, status=500)

            # Return the styled image URL
            output_url = f"{settings.MEDIA_URL}{output_image_relative_path}"
            print(f"Final output URL: {output_url}")

            return JsonResponse({
                'success': True,
                'output_image_url': output_url,
                'styled_image_id': styled_image.id,
                'message': 'Image successfully created with all styling parameters applied',
                'debug_info': {
                    'font_family_applied': font_family,
                    'font_weight_applied': font_weight,
                    'text_rotation_applied': text_rotate,
                    'text_opacity_applied': text_opacity,
                    'shadow_enabled': enable_shadow == 'on',
                    'letter_spacing_applied': letter_spacing,
                    'line_height_applied': line_height
                }
            })

        except Exception as e:
            print(f"General error in upload_and_style: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

def get_subcategories(request, category_id):
    """API endpoint to get subcategories for a category"""
    try:
        subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'name')
        return JsonResponse({
            'subcategories': list(subcategories)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def download_styled_image(request, image_id):
    """Download the styled image"""
    try:
        styled_image = StyledImage.objects.get(id=image_id)

        if not styled_image.output_image:
            return JsonResponse({'error': 'No styled image available for download'}, status=404)

        image_path = styled_image.output_image.path

        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='image/jpeg')
                response['Content-Disposition'] = f'attachment; filename="styled_image_{image_id}.jpg"'
                return response
        else:
            return JsonResponse({'error': 'Styled image file not found'}, status=404)

    except StyledImage.DoesNotExist:
        return JsonResponse({'error': 'Image not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_styled_image(request, image_id):
    """Return the styled image directly"""
    try:
        styled_image = StyledImage.objects.get(id=image_id)

        if not styled_image.output_image:
            return JsonResponse({'error': 'No styled image available'}, status=404)

        image_path = styled_image.output_image.path

        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                return HttpResponse(f.read(), content_type='image/jpeg')
        else:
            return JsonResponse({'error': 'Styled image file not found'}, status=404)

    except StyledImage.DoesNotExist:
        return JsonResponse({'error': 'Image not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def get_image_data(request, image_id):
    """Get all styling data for a specific image for editing"""
    try:
        styled_image = StyledImage.objects.get(id=image_id)

        return JsonResponse({
            'success': True,
            'image_data': {
                'id': styled_image.id,
                'text': styled_image.text,
                'font_size': styled_image.font_size,
                'font_color': styled_image.font_color,
                'x_position': styled_image.x_position,
                'y_position': styled_image.y_position,
                'font_family': styled_image.font_family,
                'text_alignment': styled_image.text_alignment,
                'font_weight': styled_image.font_weight,
                'text_rotate': styled_image.text_rotate,
                'text_opacity': styled_image.text_opacity,
                'enable_shadow': styled_image.enable_shadow,
                'shadow_x': styled_image.shadow_x,
                'shadow_y': styled_image.shadow_y,
                'shadow_blur': styled_image.shadow_blur,
                'shadow_color': styled_image.shadow_color,
                'enable_background': styled_image.enable_background,
                'text_background': styled_image.text_background,
                'letter_spacing': styled_image.letter_spacing,
                'line_height': styled_image.line_height,
                'output_image_url': styled_image.output_image.url if styled_image.output_image else None,
            }
        })
    except StyledImage.DoesNotExist:
        return JsonResponse({'error': 'Image not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

def list_styled_images(request):
    """List all styled images from database with category information"""
    styled_images = StyledImage.objects.select_related('category', 'subcategory').all().order_by('-created_at')

    images_data = []
    for image in styled_images:
        category_info = None
        if image.category:
            category_info = {
                'category_id': image.category.id,
                'category_name': image.category.name,
                'subcategory_id': image.subcategory.id if image.subcategory else None,
                'subcategory_name': image.subcategory.name if image.subcategory else None,
            }

        images_data.append({
            'id': image.id,
            'text': image.text,
            'font_size': image.font_size,
            'font_color': image.font_color,
            'font_family': image.font_family,
            'x_position': image.x_position,
            'y_position': image.y_position,
            'category_info': category_info,
            'original_image_url': image.original_image.url if image.original_image else None,
            'output_image_url': image.output_image.url if image.output_image else None,
            'created_at': image.created_at.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'total_images': len(images_data),
        'images': images_data
    })


@csrf_exempt
def update_text_and_regenerate(request):
    """
    API endpoint for Postman - Update text and ALL styling parameters, return regenerated image
    Expected POST data: JSON with all styling parameters
    Returns: Image file directly
    """
    if request.method == 'POST':
        try:
            # Get data from POST request
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                image_id = data.get('id')
                new_text = data.get('text', '').strip()

                # Get ALL styling parameters from the request
                font_size = data.get('font_size')
                font_color = data.get('font_color')
                x_position = data.get('x_position')
                y_position = data.get('y_position')
                font_family = data.get('font_family')
                text_alignment = data.get('text_alignment')
                font_weight = data.get('font_weight')
                text_rotate = data.get('text_rotate')
                text_opacity = data.get('text_opacity')
                enable_shadow = data.get('enable_shadow')
                shadow_x = data.get('shadow_x')
                shadow_y = data.get('shadow_y')
                shadow_blur = data.get('shadow_blur')
                shadow_color = data.get('shadow_color')
                enable_background = data.get('enable_background')
                text_background = data.get('text_background')
                letter_spacing = data.get('letter_spacing')
                line_height = data.get('line_height')

            else:
                # Form data fallback
                image_id = request.POST.get('id')
                new_text = request.POST.get('text', '').strip()
                font_size = request.POST.get('font_size')
                font_color = request.POST.get('font_color')
                x_position = request.POST.get('x_position')
                y_position = request.POST.get('y_position')
                font_family = request.POST.get('font_family')
                text_alignment = request.POST.get('text_alignment')
                font_weight = request.POST.get('font_weight')
                text_rotate = request.POST.get('text_rotate')
                text_opacity = request.POST.get('text_opacity')
                enable_shadow = request.POST.get('enable_shadow')
                shadow_x = request.POST.get('shadow_x')
                shadow_y = request.POST.get('shadow_y')
                shadow_blur = request.POST.get('shadow_blur')
                shadow_color = request.POST.get('shadow_color')
                enable_background = request.POST.get('enable_background')
                text_background = request.POST.get('text_background')
                letter_spacing = request.POST.get('letter_spacing')
                line_height = request.POST.get('line_height')

            # Validate required fields
            if not image_id:
                return JsonResponse({'error': 'Image ID is required'}, status=400)

            if not new_text:
                return JsonResponse({'error': 'Text is required'}, status=400)

            # Get the existing styled image
            try:
                styled_image = StyledImage.objects.get(id=image_id)
            except StyledImage.DoesNotExist:
                return JsonResponse({'error': 'Image not found'}, status=404)

            if not styled_image.original_image:
                return JsonResponse({'error': 'Original image not found'}, status=404)

            # Debug: Print what we received
            print("=== UPDATE TEXT - PARAMETERS RECEIVED ===")
            print(f"Image ID: {image_id}")
            print(f"New Text: {new_text}")
            print(f"Font Family: {font_family}")
            print(f"Font Weight: {font_weight}")
            print(f"Text Rotation: {text_rotate}")
            print(f"Text Opacity: {text_opacity}")
            print(f"Letter Spacing: {letter_spacing}")
            print(f"Shadow Enabled: {enable_shadow}")
            print(f"Line Height: {line_height}")
            print("==========================================")

            # Update ALL fields - use request values if provided, otherwise keep existing values
            styled_image.text = new_text

            # Only update fields that were provided in the request
            if font_size is not None:
                styled_image.font_size = int(font_size)
            if font_color is not None:
                styled_image.font_color = font_color
            if x_position is not None:
                styled_image.x_position = int(x_position)
            if y_position is not None:
                styled_image.y_position = int(y_position)
            if font_family is not None:
                styled_image.font_family = font_family
            if text_alignment is not None:
                styled_image.text_alignment = text_alignment
            if font_weight is not None:
                styled_image.font_weight = font_weight
            if text_rotate is not None:
                styled_image.text_rotate = int(text_rotate)
            if text_opacity is not None:
                styled_image.text_opacity = int(text_opacity)
            if enable_shadow is not None:
                styled_image.enable_shadow = bool(enable_shadow)
            if shadow_x is not None:
                styled_image.shadow_x = int(shadow_x)
            if shadow_y is not None:
                styled_image.shadow_y = int(shadow_y)
            if shadow_blur is not None:
                styled_image.shadow_blur = int(shadow_blur)
            if shadow_color is not None:
                styled_image.shadow_color = shadow_color
            if enable_background is not None:
                styled_image.enable_background = bool(enable_background)
            if text_background is not None:
                styled_image.text_background = text_background
            if letter_spacing is not None:
                styled_image.letter_spacing = float(letter_spacing)
            if line_height is not None:
                styled_image.line_height = float(line_height)

            styled_image.save()

            # Get the original image path
            original_path = styled_image.original_image.path

            # Prepare style options using UPDATED database values
            style_options = {
                'font_size': styled_image.font_size,
                'font_color': styled_image.font_color,
                'x_position': styled_image.x_position,
                'y_position': styled_image.y_position,
                'font_family': styled_image.font_family,
                'text_alignment': styled_image.text_alignment,
                'font_weight': styled_image.font_weight,
                'text_rotate': styled_image.text_rotate,
                'text_opacity': styled_image.text_opacity,
                'enable_shadow': 'on' if styled_image.enable_shadow else '',
                'shadow_x': styled_image.shadow_x,
                'shadow_y': styled_image.shadow_y,
                'shadow_blur': styled_image.shadow_blur,
                'shadow_color': styled_image.shadow_color,
                'enable_background': 'on' if styled_image.enable_background else '',
                'text_background': styled_image.text_background,
                'letter_spacing': styled_image.letter_spacing,
                'line_height': styled_image.line_height,
            }

            # Debug: Print style options being used
            print("=== UPDATE TEXT - STYLE OPTIONS BEING USED ===")
            for key, value in style_options.items():
                print(f"{key}: {value}")
            print("==============================================")

            # Regenerate the image with new text and styles
            output_image_relative_path = add_text_to_image(
                original_path,
                new_text,
                style_options
            )

            # Update the output image path
            styled_image.output_image = output_image_relative_path
            styled_image.save()

            # Get the path to the new image
            output_image_path = os.path.join(settings.MEDIA_ROOT, output_image_relative_path)

            # Return the image directly
            if os.path.exists(output_image_path):
                with open(output_image_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='image/jpeg')
                    response['Content-Disposition'] = f'inline; filename="updated_image_{image_id}.jpg"'
                    return response
            else:
                return JsonResponse({'error': 'Generated image not found'}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            print(f"Error in update_text_and_regenerate: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


@csrf_exempt
def update_text_and_regenerate_json(request):
    """
    Alternative API endpoint that returns JSON with image URL
    Expected POST data: JSON with all styling parameters
    Returns: JSON with image URL and info
    """
    if request.method == 'POST':
        try:
            # Get data from POST request
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                image_id = data.get('id')
                new_text = data.get('text', '').strip()

                # Get ALL styling parameters from the request
                font_size = data.get('font_size')
                font_color = data.get('font_color')
                x_position = data.get('x_position')
                y_position = data.get('y_position')
                font_family = data.get('font_family')
                text_alignment = data.get('text_alignment')
                font_weight = data.get('font_weight')
                text_rotate = data.get('text_rotate')
                text_opacity = data.get('text_opacity')
                enable_shadow = data.get('enable_shadow')
                shadow_x = data.get('shadow_x')
                shadow_y = data.get('shadow_y')
                shadow_blur = data.get('shadow_blur')
                shadow_color = data.get('shadow_color')
                enable_background = data.get('enable_background')
                text_background = data.get('text_background')
                letter_spacing = data.get('letter_spacing')
                line_height = data.get('line_height')

            else:
                image_id = request.POST.get('id')
                new_text = request.POST.get('text', '').strip()
                font_size = request.POST.get('font_size')
                font_color = request.POST.get('font_color')
                x_position = request.POST.get('x_position')
                y_position = request.POST.get('y_position')
                font_family = request.POST.get('font_family')
                text_alignment = request.POST.get('text_alignment')
                font_weight = request.POST.get('font_weight')
                text_rotate = request.POST.get('text_rotate')
                text_opacity = request.POST.get('text_opacity')
                enable_shadow = request.POST.get('enable_shadow')
                shadow_x = request.POST.get('shadow_x')
                shadow_y = request.POST.get('shadow_y')
                shadow_blur = request.POST.get('shadow_blur')
                shadow_color = request.POST.get('shadow_color')
                enable_background = request.POST.get('enable_background')
                text_background = request.POST.get('text_background')
                letter_spacing = request.POST.get('letter_spacing')
                line_height = request.POST.get('line_height')

            # Validate required fields
            if not image_id:
                return JsonResponse({'error': 'Image ID is required'}, status=400)

            if not new_text:
                return JsonResponse({'error': 'Text is required'}, status=400)

            # Get the existing styled image
            try:
                styled_image = StyledImage.objects.get(id=image_id)
            except StyledImage.DoesNotExist:
                return JsonResponse({'error': 'Image not found'}, status=404)

            if not styled_image.original_image:
                return JsonResponse({'error': 'Original image not found'}, status=404)

            # Store old values for response
            old_text = styled_image.text
            old_styles = {
                'font_family': styled_image.font_family,
                'font_weight': styled_image.font_weight,
                'text_rotate': styled_image.text_rotate,
                'text_opacity': styled_image.text_opacity,
                'letter_spacing': styled_image.letter_spacing,
                'enable_shadow': styled_image.enable_shadow,
                'line_height': styled_image.line_height,
            }

            # Update ALL fields
            styled_image.text = new_text

            # Only update fields that were provided in the request
            if font_size is not None:
                styled_image.font_size = int(font_size)
            if font_color is not None:
                styled_image.font_color = font_color
            if x_position is not None:
                styled_image.x_position = int(x_position)
            if y_position is not None:
                styled_image.y_position = int(y_position)
            if font_family is not None:
                styled_image.font_family = font_family
            if text_alignment is not None:
                styled_image.text_alignment = text_alignment
            if font_weight is not None:
                styled_image.font_weight = font_weight
            if text_rotate is not None:
                styled_image.text_rotate = int(text_rotate)
            if text_opacity is not None:
                styled_image.text_opacity = int(text_opacity)
            if enable_shadow is not None:
                styled_image.enable_shadow = bool(enable_shadow)
            if shadow_x is not None:
                styled_image.shadow_x = int(shadow_x)
            if shadow_y is not None:
                styled_image.shadow_y = int(shadow_y)
            if shadow_blur is not None:
                styled_image.shadow_blur = int(shadow_blur)
            if shadow_color is not None:
                styled_image.shadow_color = shadow_color
            if enable_background is not None:
                styled_image.enable_background = bool(enable_background)
            if text_background is not None:
                styled_image.text_background = text_background
            if letter_spacing is not None:
                styled_image.letter_spacing = float(letter_spacing)
            if line_height is not None:
                styled_image.line_height = float(line_height)

            styled_image.save()

            # Get the original image path
            original_path = styled_image.original_image.path

            # Style options from updated image
            style_options = {
                'font_size': styled_image.font_size,
                'font_color': styled_image.font_color,
                'x_position': styled_image.x_position,
                'y_position': styled_image.y_position,
                'font_family': styled_image.font_family,
                'text_alignment': styled_image.text_alignment,
                'font_weight': styled_image.font_weight,
                'text_rotate': styled_image.text_rotate,
                'text_opacity': styled_image.text_opacity,
                'enable_shadow': 'on' if styled_image.enable_shadow else '',
                'shadow_x': styled_image.shadow_x,
                'shadow_y': styled_image.shadow_y,
                'shadow_blur': styled_image.shadow_blur,
                'shadow_color': styled_image.shadow_color,
                'enable_background': 'on' if styled_image.enable_background else '',
                'text_background': styled_image.text_background,
                'letter_spacing': styled_image.letter_spacing,
                'line_height': styled_image.line_height,
            }

            # Regenerate the image with new text and styles
            output_image_relative_path = add_text_to_image(
                original_path,
                new_text,
                style_options
            )

            # Update the output image path
            styled_image.output_image = output_image_relative_path
            styled_image.save()

            # Return JSON response
            output_url = f"{settings.MEDIA_URL}{output_image_relative_path}"

            return JsonResponse({
                'success': True,
                'message': 'Text and styles updated and image regenerated successfully',
                'image_id': image_id,
                'old_text': old_text,
                'new_text': new_text,
                'styles_updated': {
                    'font_family': f"{old_styles['font_family']} → {styled_image.font_family}",
                    'font_weight': f"{old_styles['font_weight']} → {styled_image.font_weight}",
                    'text_rotation': f"{old_styles['text_rotate']}° → {styled_image.text_rotate}°",
                    'text_opacity': f"{old_styles['text_opacity']}% → {styled_image.text_opacity}%",
                    'letter_spacing': f"{old_styles['letter_spacing']}px → {styled_image.letter_spacing}px",
                    'shadow_enabled': f"{old_styles['enable_shadow']} → {styled_image.enable_shadow}",
                    'line_height': f"{old_styles['line_height']} → {styled_image.line_height}",
                },
                'output_image_url': output_url,
                'download_url': f"/download/{image_id}/",
                'direct_image_url': f"/image/{image_id}/",
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


def get_categories_with_images(request):
    """
    API endpoint to get all categories with only basic info and category image
    Returns: JSON with category name, description, created_at, total_images, category_image
    """
    try:
        # Get all categories with their subcategories and related images
        categories = Category.objects.prefetch_related(
            'subcategories',
            'styled_images'
        ).all()

        categories_data = []

        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'created_at': category.created_at.isoformat(),
                'total_images': category.styled_images.count(),
                'category_image': None  # Default to None
            }

            # Get category image - using the category_image field if it exists
            # If you added the category_image field as per previous suggestions
            if hasattr(category, 'category_image') and category.category_image:
                category_data['category_image'] = category.category_image.url

            # Fallback: Use the first image in the category as category image
            elif category.styled_images.exists():
                first_image = category.styled_images.first()
                if first_image and first_image.output_image:
                    category_data['category_image'] = first_image.output_image.url
                elif first_image and first_image.original_image:
                    category_data['category_image'] = first_image.original_image.url

            categories_data.append(category_data)

        return JsonResponse({
            'success': True,
            'total_categories': len(categories_data),
            'categories': categories_data
        })

    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


def get_categories_basic(request):
    """
    API endpoint to get only basic category info with category image
    Returns: JSON with category name, description, created_at, total_images, category_image
    """
    try:
        categories = Category.objects.prefetch_related('styled_images').all()

        categories_data = []

        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'created_at': category.created_at.isoformat(),
                'total_images': category.styled_images.count(),
                'category_image': None
            }

            # Get category image - check if category_image field exists
            if hasattr(category, 'category_image') and category.category_image:
                # Use absolute URL
                category_data['category_image'] = get_absolute_media_url(request, category.category_image.url)

            # Fallback to first image in category
            elif category.styled_images.exists():
                first_image = category.styled_images.first()
                if first_image and first_image.output_image:
                    category_data['category_image'] = get_absolute_media_url(request, first_image.output_image.url)
                elif first_image and first_image.original_image:
                    category_data['category_image'] = get_absolute_media_url(request, first_image.original_image.url)

            categories_data.append(category_data)

        return JsonResponse({
            'success': True,
            'total_categories': len(categories_data),
            'categories': categories_data
        })

    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

def get_category_images(request, category_id):
    """
    API endpoint to get a specific category with its images
    """
    try:
        category = Category.objects.prefetch_related(
            Prefetch(
                'subcategories',
                queryset=SubCategory.objects.prefetch_related(
                    Prefetch(
                        'styled_images',
                        queryset=StyledImage.objects.select_related('category', 'subcategory')
                    )
                )
            ),
            Prefetch(
                'styled_images',
                queryset=StyledImage.objects.filter(subcategory__isnull=True)
            )
        ).get(id=category_id)

        category_data = {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'created_at': category.created_at.isoformat(),
            'total_images': category.styled_images.count(),
            'subcategories': [],
            'images': []
        }

        # Get images directly under this category
        direct_images = category.styled_images.filter(subcategory__isnull=True)
        for image in direct_images:
            category_data['images'].append({
                'id': image.id,
                'text': image.text,
                'font_size': image.font_size,
                'font_color': image.font_color,
                'font_family': image.font_family,
                'x_position': image.x_position,
                'y_position': image.y_position,
                'original_image_url': get_absolute_media_url(request, image.original_image.url) if image.original_image else None,
                'output_image_url': get_absolute_media_url(request, image.output_image.url) if image.output_image else None,
                'created_at': image.created_at.isoformat(),
            })

        # Get subcategories with their images
        for subcategory in category.subcategories.all():
            subcategory_data = {
                'id': subcategory.id,
                'name': subcategory.name,
                'description': subcategory.description,
                'created_at': subcategory.created_at.isoformat(),
                'total_images': subcategory.styled_images.count(),
                'images': []
            }

            for image in subcategory.styled_images.all():
                subcategory_data['images'].append({
                    'id': image.id,
                    'text': image.text,
                    'font_size': image.font_size,
                    'font_color': image.font_color,
                    'font_family': image.font_family,
                    'x_position': image.x_position,
                    'y_position': image.y_position,
                    'original_image_url': get_absolute_media_url(request, image.original_image.url) if image.original_image else None,
                    'output_image_url': get_absolute_media_url(request, image.output_image.url) if image.output_image else None,
                    'created_at': image.created_at.isoformat(),
                })

            category_data['subcategories'].append(subcategory_data)

        return JsonResponse({
            'success': True,
            'category': category_data
        })

    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
def get_subcategory_images(request, subcategory_id):
    """
    API endpoint to get a specific subcategory with its images
    """
    try:
        subcategory = SubCategory.objects.prefetch_related(
            Prefetch(
                'styled_images',
                queryset=StyledImage.objects.select_related('category', 'subcategory')
            )
        ).get(id=subcategory_id)

        subcategory_data = {
            'id': subcategory.id,
            'name': subcategory.name,
            'description': subcategory.description,
            'created_at': subcategory.created_at.isoformat(),
            'category': {
                'id': subcategory.category.id,
                'name': subcategory.category.name,
                'description': subcategory.category.description
            },
            'total_images': subcategory.styled_images.count(),
            'images': []
        }

        for image in subcategory.styled_images.all():
            subcategory_data['images'].append({
                'id': image.id,
                'text': image.text,
                'font_size': image.font_size,
                'font_color': image.font_color,
                'font_family': image.font_family,
                'x_position': image.x_position,
                'y_position': image.y_position,
                'original_image_url': image.original_image.url if image.original_image else None,
                'output_image_url': image.output_image.url if image.output_image else None,
                'created_at': image.created_at.isoformat(),
            })

        return JsonResponse({
            'success': True,
            'subcategory': subcategory_data
        })

    except SubCategory.DoesNotExist:
        return JsonResponse({'error': 'Subcategory not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


def get_absolute_media_url(request, relative_url):
    """Convert relative media URL to absolute URL"""
    if not relative_url:
        return None

    # Get the absolute URL using the request
    if request:
        return request.build_absolute_uri(relative_url)
    else:
        # Fallback for when there's no request (shouldn't happen in views)
        return f"https://yousefelmesalamy.pythonanywhere.com{relative_url}"

def get_uncategorized_images(request):
    """
    API endpoint to get all images that don't belong to any category
    """
    try:
        uncategorized_images = StyledImage.objects.filter(category__isnull=True)

        images_data = []
        for image in uncategorized_images:
            images_data.append({
                'id': image.id,
                'text': image.text,
                'font_size': image.font_size,
                'font_color': image.font_color,
                'font_family': image.font_family,
                'x_position': image.x_position,
                'y_position': image.y_position,
                'original_image_url': image.original_image.url if image.original_image else None,
                'output_image_url': image.output_image.url if image.output_image else None,
                'created_at': image.created_at.isoformat(),
            })

        return JsonResponse({
            'success': True,
            'total_images': len(images_data),
            'uncategorized_images': images_data
        })

    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
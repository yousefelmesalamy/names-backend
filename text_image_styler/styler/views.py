from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .utils import add_text_to_image
from .models import StyledImage, Category
from django.core import serializers
from django.db.models import Prefetch, Q, Sum
import os
import json


def upload_page(request):
    """Render the upload page with categories"""
    categories = Category.objects.all()
    return render(request, 'styler/upload.html', {
        'categories': categories
    })


@csrf_exempt
def upload_and_style(request):
    """Handle image and text upload, style the text on image, return styled image"""
    if request.method == 'POST':
        try:
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

            # Advanced parameters
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

            # Category (no subcategory anymore)
            category_id = request.POST.get('category')

            # Validate inputs
            if not text:
                return JsonResponse({'error': 'No text provided'}, status=400)

            # Convert to appropriate types
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
            except Exception as e:
                return JsonResponse({'error': f'Error saving image: {str(e)}'}, status=500)

            # Prepare style options
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

            # Add text to image
            try:
                output_image_relative_path = add_text_to_image(image_path, text, style_options)
            except Exception as e:
                # Clean up uploaded file if processing fails
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except:
                    pass
                return JsonResponse({'error': f'Image processing failed: {str(e)}'}, status=500)

            # Handle category relationship
            category = None
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    # Continue without category if not found
                    pass

            # Create database record
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
                    update_clicks=0  # Initialize click counter
                )
            except Exception as e:
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

            return JsonResponse({
                'success': True,
                'output_image_url': output_url,
                'styled_image_id': styled_image.id,
                'message': 'Image successfully created with all styling parameters applied',
            })

        except Exception as e:
            return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


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
                'update_clicks': styled_image.update_clicks,
                'last_updated': styled_image.last_updated.isoformat(),
                'output_image_url': styled_image.output_image.url if styled_image.output_image else None,
            }
        })
    except StyledImage.DoesNotExist:
        return JsonResponse({'error': 'Image not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


def list_styled_images(request):
    """List all styled images from database with category information"""
    styled_images = StyledImage.objects.select_related('category').all().order_by('-created_at')

    images_data = []
    for image in styled_images:
        category_info = None
        if image.category:
            category_info = {
                'category_id': image.category.id,
                'category_name': image.category.name,
            }

        images_data.append({
            'id': image.id,
            'text': image.text,
            'font_size': image.font_size,
            'font_color': image.font_color,
            'font_family': image.font_family,
            'x_position': image.x_position,
            'y_position': image.y_position,
            'update_clicks': image.update_clicks,
            'last_updated': image.last_updated.isoformat(),
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
                category_id = data.get('category_id')  # Added category update

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
                category_id = request.POST.get('category_id')

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

            # INCREMENT CLICK COUNTER - This is the key change!
            styled_image.increment_clicks()

            # Update ALL fields - use request values if provided, otherwise keep existing values
            styled_image.text = new_text

            # Update category if provided
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    styled_image.category = category
                except Category.DoesNotExist:
                    # Keep existing category if new one doesn't exist
                    pass

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
                category_id = data.get('category_id')

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
                category_id = request.POST.get('category_id')

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

            # INCREMENT CLICK COUNTER
            old_clicks = styled_image.update_clicks
            styled_image.increment_clicks()

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

            # Update category if provided
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    styled_image.category = category
                except Category.DoesNotExist:
                    pass

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
                'click_tracking': {
                    'old_clicks': old_clicks,
                    'new_clicks': styled_image.update_clicks,
                    'total_clicks': styled_image.update_clicks,
                    'last_updated': styled_image.last_updated.isoformat()
                },
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
                'show_in_landing': category.show_in_landing,
                'category_image': None
            }

            # Get category image
            if hasattr(category, 'category_image') and category.category_image:
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


def get_categories_landing(request):
    """
    NEW ENDPOINT: Get only categories marked for landing page display
    Returns: JSON with categories that have show_in_landing = True
    """
    try:
        # Filter categories that should be shown in landing page
        landing_categories = Category.objects.filter(
            show_in_landing=True
        ).prefetch_related('styled_images')

        categories_data = []

        for category in landing_categories:
            # Get some featured images for the category (limit to 4 for landing)
            featured_images = category.styled_images.all()[:4]

            category_data = {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'created_at': category.created_at.isoformat(),
                'total_images': category.styled_images.count(),
                'show_in_landing': category.show_in_landing,
                'category_image': None,
                'featured_images': []
            }

            # Get category image
            if hasattr(category, 'category_image') and category.category_image:
                category_data['category_image'] = get_absolute_media_url(request, category.category_image.url)

            # Get featured images
            for image in featured_images:
                featured_image_data = {
                    'id': image.id,
                    'text': image.text[:50] + '...' if len(image.text) > 50 else image.text,
                    'output_image_url': get_absolute_media_url(request,
                                                               image.output_image.url) if image.output_image else None,
                    'update_clicks': image.update_clicks,
                    'last_updated': image.last_updated.isoformat(),
                }
                category_data['featured_images'].append(featured_image_data)

            categories_data.append(category_data)

        return JsonResponse({
            'success': True,
            'total_categories': len(categories_data),
            'landing_categories': categories_data
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
                'styled_images',
                queryset=StyledImage.objects.select_related('category')
            )
        ).get(id=category_id)

        category_data = {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'created_at': category.created_at.isoformat(),
            'total_images': category.styled_images.count(),
            'show_in_landing': category.show_in_landing,
            'images': []
        }

        # Get all images in this category
        for image in category.styled_images.all():
            category_data['images'].append({
                'id': image.id,
                'text': image.text,
                'font_size': image.font_size,
                'font_color': image.font_color,
                'font_family': image.font_family,
                'x_position': image.x_position,
                'y_position': image.y_position,
                'update_clicks': image.update_clicks,
                'last_updated': image.last_updated.isoformat(),
                'original_image_url': get_absolute_media_url(request,
                                                             image.original_image.url) if image.original_image else None,
                'output_image_url': get_absolute_media_url(request,
                                                           image.output_image.url) if image.output_image else None,
                'created_at': image.created_at.isoformat(),
            })

        return JsonResponse({
            'success': True,
            'category': category_data
        })

    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
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


def get_image_stats(request):
    """
    NEW ENDPOINT: Get statistics about image updates
    Returns: JSON with click statistics
    """
    try:
        # Get total images
        total_images = StyledImage.objects.count()

        # Get images with clicks
        images_with_clicks = StyledImage.objects.filter(update_clicks__gt=0).count()

        # Get total clicks across all images
        total_clicks = StyledImage.objects.aggregate(Sum('update_clicks'))['update_clicks__sum'] or 0

        # Get top 10 most updated images
        top_images = StyledImage.objects.select_related('category').order_by('-update_clicks')[:10]

        top_images_data = []
        for image in top_images:
            top_images_data.append({
                'id': image.id,
                'text': image.text[:30] + '...' if len(image.text) > 30 else image.text,
                'update_clicks': image.update_clicks,
                'last_updated': image.last_updated.isoformat(),
                'category': image.category.name if image.category else 'Uncategorized',
                'output_image_url': get_absolute_media_url(request,
                                                           image.output_image.url) if image.output_image else None,
            })

        return JsonResponse({
            'success': True,
            'stats': {
                'total_images': total_images,
                'images_with_clicks': images_with_clicks,
                'total_clicks': total_clicks,
                'average_clicks_per_image': total_clicks / total_images if total_images > 0 else 0,
            },
            'top_updated_images': top_images_data
        })

    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


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
                'update_clicks': image.update_clicks,
                'last_updated': image.last_updated.isoformat(),
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


def get_trending_images(request):
    """
    NEW ENDPOINT: Get trending images (recently updated with high activity)
    Returns: JSON with images that have been recently updated
    """
    try:
        # Get query parameters
        limit = request.GET.get('limit', 10)

        try:
            limit = int(limit)
            if limit > 50:
                limit = 50
        except ValueError:
            limit = 10

        from datetime import datetime, timedelta
        from django.utils import timezone

        # Get images updated in the last 7 days
        week_ago = timezone.now() - timedelta(days=7)

        trending_images = StyledImage.objects.select_related('category').filter(
            last_updated__gte=week_ago,
            update_clicks__gt=0
        ).order_by('-update_clicks', '-last_updated')[:limit]

        images_data = []
        for image in trending_images:
            # Calculate activity score (clicks per day since creation)
            days_since_creation = (timezone.now() - image.created_at).days
            if days_since_creation == 0:
                days_since_creation = 1
            activity_score = image.update_clicks / days_since_creation

            images_data.append({
                'id': image.id,
                'text': image.text,
                'text_preview': image.text[:50] + '...' if len(image.text) > 50 else image.text,
                'update_clicks': image.update_clicks,
                'activity_score': round(activity_score, 2),
                'last_updated': image.last_updated.isoformat(),
                'created_at': image.created_at.isoformat(),
                'days_since_creation': days_since_creation,
                'category': {
                    'id': image.category.id if image.category else None,
                    'name': image.category.name if image.category else 'Uncategorized',
                } if image.category else None,
                'output_image_url': get_absolute_media_url(request,
                                                           image.output_image.url) if image.output_image else None,
                'trending_badge': get_trending_badge(activity_score),
            })

        return JsonResponse({
            'success': True,
            'timeframe': 'last_7_days',
            'limit': limit,
            'trending_images': images_data
        })

    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


def get_trending_badge(activity_score):
    """Determine trending badge based on activity score"""
    if activity_score >= 2:
        return '🔥 Hot'
    elif activity_score >= 1:
        return '↑ Trending'
    elif activity_score >= 0.5:
        return '↗️ Rising'
    else:
        return '↗️ Active'


def get_most_updated_images(request):
    """
    NEW ENDPOINT: Get images with the highest update clicks
    Returns: JSON with images sorted by update_clicks (most updated first)
    """
    try:
        # Get query parameters
        limit = request.GET.get('limit', 10)  # Default 10 images
        category_id = request.GET.get('category_id')
        timeframe = request.GET.get('timeframe')  # daily, weekly, monthly, yearly

        try:
            limit = int(limit)
            if limit > 50:  # Prevent too large requests
                limit = 50
        except ValueError:
            limit = 10

        # Base queryset
        queryset = StyledImage.objects.select_related('category').filter(
            update_clicks__gt=0  # Only include images with at least one update
        )

        # Filter by category if specified
        if category_id:
            try:
                category_id = int(category_id)
                queryset = queryset.filter(category_id=category_id)
            except ValueError:
                pass

        # Filter by timeframe if specified
        from datetime import datetime, timedelta
        from django.utils import timezone

        if timeframe:
            now = timezone.now()
            if timeframe == 'daily':
                start_date = now - timedelta(days=1)
            elif timeframe == 'weekly':
                start_date = now - timedelta(weeks=1)
            elif timeframe == 'monthly':
                start_date = now - timedelta(days=30)
            elif timeframe == 'yearly':
                start_date = now - timedelta(days=365)
            else:
                start_date = None

            if start_date:
                queryset = queryset.filter(last_updated__gte=start_date)

        # Get the most updated images
        most_updated_images = queryset.order_by('-update_clicks', '-last_updated')[:limit]

        images_data = []
        for image in most_updated_images:
            # Calculate activity level based on clicks
            if image.update_clicks >= 20:
                activity_level = 'very_high'
            elif image.update_clicks >= 10:
                activity_level = 'high'
            elif image.update_clicks >= 5:
                activity_level = 'medium'
            else:
                activity_level = 'low'

            images_data.append({
                'id': image.id,
                'text': image.text,
                'text_preview': image.text[:50] + '...' if len(image.text) > 50 else image.text,
                'update_clicks': image.update_clicks,
                'activity_level': activity_level,
                'last_updated': image.last_updated.isoformat(),
                'created_at': image.created_at.isoformat(),
                'category': {
                    'id': image.category.id if image.category else None,
                    'name': image.category.name if image.category else 'Uncategorized',
                    'show_in_landing': image.category.show_in_landing if image.category else False,
                } if image.category else None,
                'original_image_url': get_absolute_media_url(request,
                                                             image.original_image.url) if image.original_image else None,
                'output_image_url': get_absolute_media_url(request,
                                                           image.output_image.url) if image.output_image else None,
                'styling_info': {
                    'font_family': image.font_family,
                    'font_size': image.font_size,
                    'font_color': image.font_color,
                    'text_alignment': image.text_alignment,
                    'font_weight': image.font_weight,
                }
            })

        # Get statistics
        total_images = StyledImage.objects.count()
        total_updates = StyledImage.objects.aggregate(Sum('update_clicks'))['update_clicks__sum'] or 0
        avg_updates = total_updates / total_images if total_images > 0 else 0

        return JsonResponse({
            'success': True,
            'stats': {
                'total_images_in_result': len(images_data),
                'total_images_in_database': total_images,
                'total_update_clicks': total_updates,
                'average_clicks_per_image': round(avg_updates, 2),
                'timeframe': timeframe,
                'limit': limit,
            },
            'images': images_data
        })

    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)



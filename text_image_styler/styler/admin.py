from django.contrib import admin
from django.utils.html import format_html
from .models import Category, StyledImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'show_in_landing',  # Use the field, not the method
        'styled_images_count',
        'created_at'
    ]
    list_editable = ['show_in_landing']  # This should be the field name
    list_filter = ['show_in_landing', 'created_at']
    search_fields = ['name', 'description']

    def styled_images_count(self, obj):
        return obj.styled_images.count()
    styled_images_count.short_description = 'Images'


class StyledImageAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = [
        'id',
        'text_preview',
        'category_display',
        'update_clicks',
        'last_updated',
        'font_size',
        'font_family',
        'original_image_preview_list',
        'output_image_preview_list',
        'created_at',
    ]

    # Fields that can be used for filtering
    list_filter = [
        'category',
        'font_family',
        'font_size',
        'created_at',
        'update_clicks',
    ]

    # Fields that can be searched
    search_fields = [
        'text',
        'font_family',
        'category__name'
    ]

    # Fields that are read-only
    readonly_fields = [
        'created_at',
        'last_updated',
        'update_clicks',
        'original_image_preview',
        'output_image_preview',
        'original_image_preview_list',
        'output_image_preview_list',
        'category_display',
    ]

    # Fields to display in the detail view with sections
    fieldsets = (
        ('Category Information', {
            'fields': (
                'category',
                'category_display',
            )
        }),
        ('Click Tracking', {
            'fields': (
                'update_clicks',
                'last_updated',
            ),
            'classes': ('collapse',)
        }),
        ('Image Information', {
            'fields': (
                'original_image',
                'original_image_preview',
                'output_image',
                'output_image_preview',
            )
        }),
        ('Text Content', {
            'fields': (
                'text',
            )
        }),
        ('Styling Options', {
            'fields': (
                'font_family',
                'font_size',
                'font_color',
                'x_position',
                'y_position',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )

    # Custom methods for list display
    def text_preview(self, obj):
        """Display shortened text preview"""
        if len(obj.text) > 30:
            return f"{obj.text[:30]}..."
        return obj.text
    text_preview.short_description = 'Text'

    def category_display(self, obj):
        """Display category with styling"""
        if obj.category:
            return format_html(
                '<span style="background: #e3f2fd; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
                obj.category.name
            )
        return format_html('<span style="color: #999;">No category</span>')
    category_display.short_description = 'Category'

    def original_image_preview_list(self, obj):
        """Display small original image preview in list view"""
        if obj.original_image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border: 1px solid #ddd; border-radius: 3px;" />',
                obj.original_image.url
            )
        return format_html('<span style="color: #999;">-</span>')
    original_image_preview_list.short_description = 'Original'

    def output_image_preview_list(self, obj):
        """Display small output image preview in list view"""
        if obj.output_image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border: 1px solid #4CAF50; border-radius: 3px;" />',
                obj.output_image.url
            )
        return format_html('<span style="color: #999;">-</span>')
    output_image_preview_list.short_description = 'Styled'

    def original_image_preview(self, obj):
        """Display original image preview in admin detail view"""
        if obj.original_image:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-height: 300px; max-width: 300px; border: 1px solid #ddd; border-radius: 5px; padding: 5px;" />'
                '<br><a href="{}" target="_blank" style="font-size: 12px;">View Full Size</a>'
                '</div>',
                obj.original_image.url,
                obj.original_image.url
            )
        return format_html('<span style="color: #999;">No original image</span>')
    original_image_preview.short_description = 'Original Image Preview'

    def output_image_preview(self, obj):
        """Display output image preview in admin detail view"""
        if obj.output_image:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-height: 300px; max-width: 300px; border: 2px solid #4CAF50; border-radius: 5px; padding: 5px;" />'
                '<br><a href="{}" target="_blank" style="font-size: 12px;">View Full Size</a>'
                '</div>',
                obj.output_image.url,
                obj.output_image.url
            )
        return format_html('<span style="color: #999;">No output image generated</span>')
    output_image_preview.short_description = 'Styled Image Preview'

    # Configuration for the actions dropdown
    actions = ['assign_to_category', 'regenerate_output_images', 'reset_clicks']

    def assign_to_category(self, request, queryset):
        """Admin action to assign multiple images to a category"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        selected_ids = queryset.values_list('id', flat=True)
        request.session['category_assignment_ids'] = list(selected_ids)

        self.message_user(
            request,
            f"Please select a category for {len(selected_ids)} images."
        )
        return HttpResponseRedirect(reverse('admin:styler_category_changelist'))
    assign_to_category.short_description = "Assign to category"

    def regenerate_output_images(self, request, queryset):
        """Admin action to regenerate output images"""
        from .utils import add_text_to_image

        regenerated_count = 0
        for styled_image in queryset:
            if styled_image.original_image:
                try:
                    original_path = styled_image.original_image.path
                    style_options = {
                        'font_size': styled_image.font_size,
                        'font_color': styled_image.font_color,
                        'x_position': styled_image.x_position,
                        'y_position': styled_image.y_position,
                        'font_family': styled_image.font_family,
                    }
                    output_image_path = add_text_to_image(
                        original_path,
                        styled_image.text,
                        style_options
                    )
                    styled_image.output_image = output_image_path
                    styled_image.save()
                    regenerated_count += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error regenerating image {styled_image.id}: {str(e)}",
                        level='ERROR'
                    )
        self.message_user(
            request,
            f"Successfully regenerated {regenerated_count} output images."
        )
    regenerate_output_images.short_description = "Regenerate output images"

    def reset_clicks(self, request, queryset):
        """Admin action to reset click counters"""
        updated = queryset.update(update_clicks=0)
        self.message_user(
            request,
            f"Successfully reset click counters for {updated} images."
        )
    reset_clicks.short_description = "Reset click counters"

    # Admin configuration
    list_per_page = 20
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_display_links = ['id', 'text_preview']


# Register the StyledImage model
admin.site.register(StyledImage, StyledImageAdmin)
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, SubCategory, StyledImage


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1
    fields = ['name', 'description']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'styled_images_count', 'subcategories_count', 'created_at']
    search_fields = ['name', 'description']
    inlines = [SubCategoryInline]

    def styled_images_count(self, obj):
        return obj.styled_images.count()

    styled_images_count.short_description = 'Images'

    def subcategories_count(self, obj):
        return obj.subcategories.count()

    subcategories_count.short_description = 'Subcategories'


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'styled_images_count', 'created_at']
    list_filter = ['category']
    search_fields = ['name', 'category__name', 'description']

    def styled_images_count(self, obj):
        return obj.styled_images.count()

    styled_images_count.short_description = 'Images'


class StyledImageAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = [
        'id',
        'text_preview',
        'category_display',
        'subcategory_display',
        'font_size',
        'font_family',
        'original_image_preview_list',
        'output_image_preview_list',
        'created_at',
    ]

    # Fields that can be used for filtering
    list_filter = [
        'category',
        'subcategory',
        'font_family',
        'font_size',
        'created_at'
    ]

    # Fields that can be searched
    search_fields = [
        'text',
        'font_family',
        'category__name',
        'subcategory__name'
    ]

    # Fields that are read-only
    readonly_fields = [
        'created_at',
        'original_image_preview',
        'output_image_preview',
        'original_image_preview_list',
        'output_image_preview_list',
        'category_display',
        'subcategory_display',
    ]

    # Fields to display in the detail view with sections
    fieldsets = (
        ('Category Information', {
            'fields': (
                'category',
                'subcategory',
                'category_display',
            )
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

    def subcategory_display(self, obj):
        """Display subcategory with styling"""
        if obj.subcategory:
            return format_html(
                '<span style="background: #f3e5f5; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
                obj.subcategory.name
            )
        return format_html('<span style="color: #999;">-</span>')

    subcategory_display.short_description = 'Subcategory'

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
    actions = ['assign_to_category', 'regenerate_output_images']

    def assign_to_category(self, request, queryset):
        """Admin action to assign multiple images to a category"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        # Store selected IDs in session for category assignment
        selected_ids = queryset.values_list('id', flat=True)
        request.session['category_assignment_ids'] = list(selected_ids)

        self.message_user(
            request,
            f"Please select a category for {len(selected_ids)} images."
        )

        # Redirect to a category selection page (you can create this)
        return HttpResponseRedirect(reverse('admin:styler_category_changelist'))

    assign_to_category.short_description = "Assign to category"

    def regenerate_output_images(self, request, queryset):
        """Admin action to regenerate output images"""
        from .utils import add_text_to_image

        regenerated_count = 0
        for styled_image in queryset:
            if styled_image.original_image:
                try:
                    # Get the original image path
                    original_path = styled_image.original_image.path

                    # Style options
                    style_options = {
                        'font_size': styled_image.font_size,
                        'font_color': styled_image.font_color,
                        'x_position': styled_image.x_position,
                        'y_position': styled_image.y_position,
                        'font_family': styled_image.font_family,
                    }

                    # Regenerate the output image
                    output_image_path = add_text_to_image(
                        original_path,
                        styled_image.text,
                        style_options
                    )

                    # Update the model
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

    # Admin configuration
    list_per_page = 20
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    # Make the list view more compact
    list_display_links = ['id', 'text_preview']

    # Auto-select subcategories based on category
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'category' in form.base_fields and 'subcategory' in form.base_fields:
            form.base_fields['subcategory'].queryset = SubCategory.objects.none()

            if obj and obj.category:
                form.base_fields['subcategory'].queryset = SubCategory.objects.filter(category=obj.category)
        return form


# Register the StyledImage model
admin.site.register(StyledImage, StyledImageAdmin)
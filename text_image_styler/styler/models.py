from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category_image = models.ImageField(
        upload_to='category_images/',
        blank=True,
        null=True,
        help_text="Representative image for this category"
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "SubCategories"
        unique_together = ['category', 'name']
        ordering = ['category__name', 'name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class StyledImage(models.Model):
    # Category relationships
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='styled_images')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='styled_images')

    # Existing fields
    original_image = models.ImageField(upload_to='uploads/')
    text = models.TextField()
    font_size = models.IntegerField(default=36)
    font_color = models.CharField(max_length=7, default='#FFFFFF')  # HEX color
    font_family = models.CharField(max_length=100, default='Roboto')
    x_position = models.IntegerField(default=50)
    y_position = models.IntegerField(default=50)
    output_image = models.ImageField(upload_to='outputs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # NEW FIELDS - Add these to resolve the error
    text_alignment = models.CharField(
        max_length=10,
        choices=[('left', 'Left'), ('center', 'Center'), ('right', 'Right')],
        default='center'
    )
    font_weight = models.CharField(
        max_length=10,
        choices=[
            ('100', 'Thin'),
            ('200', 'Extra Light'),
            ('300', 'Light'),
            ('400', 'Regular'),
            ('500', 'Medium'),
            ('600', 'Semi Bold'),
            ('700', 'Bold'),
            ('800', 'Extra Bold'),
            ('900', 'Black')
        ],
        default='600'
    )

    # Advanced styling parameters
    text_rotate = models.IntegerField(default=0)  # Rotation in degrees
    text_opacity = models.IntegerField(default=100)  # Opacity percentage (0-100)

    # Shadow effects
    enable_shadow = models.BooleanField(default=False)
    shadow_x = models.IntegerField(default=2)
    shadow_y = models.IntegerField(default=2)
    shadow_blur = models.IntegerField(default=4)
    shadow_color = models.CharField(max_length=7, default='#000000')  # HEX color

    # Background effects
    enable_background = models.BooleanField(default=False)
    text_background = models.CharField(max_length=9, default='#00000000')  # HEX color with alpha

    # Text spacing
    letter_spacing = models.FloatField(default=0.0)  # Letter spacing in pixels
    line_height = models.FloatField(default=1.2)  # Line height multiplier

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        category_info = ""
        if self.category:
            category_info = f" ({self.category.name}"
            if self.subcategory:
                category_info += f" > {self.subcategory.name}"
            category_info += ")"
        return f"Styled Image {self.id} - {self.text[:20]}...{category_info}"

    def get_category_display(self):
        """Get formatted category display"""
        if self.category and self.subcategory:
            return f"{self.category.name} > {self.subcategory.name}"
        elif self.category:
            return self.category.name
        return "Uncategorized"
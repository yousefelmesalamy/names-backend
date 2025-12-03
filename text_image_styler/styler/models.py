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
    # NEW FIELD: Show in landing page
    show_in_landing = models.BooleanField(
        default=False,
        help_text="Show this category in the landing page"
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_landing_display(self):
        """Get formatted string for admin display"""
        return "✅" if self.show_in_landing else "❌"


class StyledImage(models.Model):
    # Category relationship only (removed subcategory)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='styled_images'
    )

    # Click tracking fields
    update_clicks = models.IntegerField(
        default=0,
        verbose_name="Update Clicks",
        help_text="Number of times this image was updated via API"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Updated",
        help_text="Last time the image was updated"
    )

    # Existing fields
    original_image = models.ImageField(upload_to='uploads/')
    text = models.TextField()
    font_size = models.IntegerField(default=36)
    font_color = models.CharField(max_length=7, default='#FFFFFF')
    font_family = models.CharField(max_length=100, default='Roboto')
    x_position = models.IntegerField(default=50)
    y_position = models.IntegerField(default=50)
    output_image = models.ImageField(upload_to='outputs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Text styling fields
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
    text_rotate = models.IntegerField(default=0)
    text_opacity = models.IntegerField(default=100)

    # Shadow effects
    enable_shadow = models.BooleanField(default=False)
    shadow_x = models.IntegerField(default=2)
    shadow_y = models.IntegerField(default=2)
    shadow_blur = models.IntegerField(default=4)
    shadow_color = models.CharField(max_length=7, default='#000000')

    # Background effects
    enable_background = models.BooleanField(default=False)
    text_background = models.CharField(max_length=9, default='#00000000')

    # Text spacing
    letter_spacing = models.FloatField(default=0.0)
    line_height = models.FloatField(default=1.2)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        category_info = f" ({self.category.name})" if self.category else ""
        return f"Styled Image {self.id} - {self.text[:20]}...{category_info}"

    def get_category_display(self):
        """Get formatted category display"""
        return self.category.name if self.category else "Uncategorized"

    def increment_clicks(self):
        """Increment the update clicks counter"""
        self.update_clicks += 1
        self.save(update_fields=['update_clicks', 'last_updated'])
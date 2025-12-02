from rest_framework import serializers
from django.conf import settings


class CategorySerializer(serializers.ModelSerializer):
    category_image = serializers.SerializerMethodField()

    def get_category_image(self, obj):
        if obj.category_image:
            # Get the request from context
            request = self.context.get('request')
            if request:
                # Build absolute URL
                return request.build_absolute_uri(obj.category_image.url)
            else:
                # Fallback: manually construct the absolute URL
                domain = "https://yousefelmesalamy.pythonanywhere.com"
                return domain + obj.category_image.url
        return None

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'total_images', 'category_image']
from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_page, name='upload_page'),
    path('api/upload-style/', views.upload_and_style, name='upload_and_style'),
    path('api/update-text/', views.update_text_and_regenerate, name='update_text'),
    path('api/update-text-json/', views.update_text_and_regenerate_json, name='update_text_json'),
    path('api/categories/', views.get_categories_basic, name='categories-basic'),
    path('api/categories/landing/', views.get_categories_landing, name='categories-landing'),
    path('api/categories/<int:category_id>/', views.get_category_images, name='get_category_images'),
    path('api/images/stats/', views.get_image_stats, name='image_stats'),
    path('download/<int:image_id>/', views.download_styled_image, name='download_styled_image'),
    path('image/<int:image_id>/', views.get_styled_image, name='get_styled_image'),
    path('api/images/', views.list_styled_images, name='list_styled_images'),
    path('api/get-image-data/<int:image_id>/', views.get_image_data, name='get_image_data'),
    path('api/uncategorized/', views.get_uncategorized_images, name='get_uncategorized_images'),
    # NEW ENDPOINTS
    path('api/search/', views.search_images, name='search_images'),  # Unified search
    path('api/tags/', views.list_all_tags, name='list_all_tags'),  # List all tags
    path('api/trending/', views.get_trending_images, name='trending_images'),  # If not already added
    path('api/most-updated/', views.get_most_updated_images, name='most_updated_images'),  # If not already added
]
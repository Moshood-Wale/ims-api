"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.permissions import AllowAny
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
# from drf_yasg.generators import OpenAPISchemaGenerator
# schema_view = get_schema_view(
#     openapi.Info(
#         title='IMS API',
#         default_version='v1.0',
#         description='IMS API Documentation',
#     ),
#     public=True,
#     permission_classes=(AllowAny,),
# )

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/doc/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path('admin/', admin.site.urls),
    path('api/v1/inventory', include('inventory.urls')),
    path('api/v1/order', include('order.urls')),
    # path('swagger/', schema_view.with_ui('swagger',
    #      cache_timeout=0), name='schema-swagger-ui'),
]
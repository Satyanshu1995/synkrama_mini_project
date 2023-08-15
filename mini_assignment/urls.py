from django.urls import path
from mini_assignment import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('api/posts/', views.ListCreatePostAPIView.as_view()),
    path('api/posts/<int:id>', views.UpdateDeletePostAPIView.as_view()),
    path('api/register/', views.UserRegistrationView.as_view()),
    path('auth-token/', obtain_auth_token),
   
]
from .models import Post
from .serializers import *
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_201_CREATED
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import send_mail
from rest_framework.exceptions import APIException



class UserRegistrationView(CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_201_CREATED)

@receiver(post_save,sender = Post)
def send_email_on_post_create(sender, instance, created, **kwargs):
    if created:
        subject = 'New Post Created'
        message = f"A new post titled {instance.title} has been created by {instance.author.username}"
        from_email = 'satyanshusrivastavaaec@gmail.com'
        recipient_list = [instance.author.email]

        send_mail(subject,message,from_email,recipient_list)

class ListCreatePostAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):

        valid_query_params = ['title','body','author','page']
        extra_params = set(request.query_params.keys()) - set(valid_query_params)

        if extra_params:
            raise APIException(detail="Extra query parameters passed: {}".format(",".join(extra_params)))
        

        title = request.query_params.get('title', None)
        body = request.query_params.get('body', None)
        author = request.query_params.get('author', None)

        queryset = Post.objects.all()

        if title:
            queryset = queryset.filter(title__icontains=title)
        if body:
            queryset = queryset.filter(body__icontains=body)
        if author:
            queryset = queryset.filter(author__username=author)

        paginator = self.pagination_class()

        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = PostSerializer(paginated_queryset, many=True)
        data = serializer.data
        return paginator.get_paginated_response(data)
    
    def post(self,request):
        data = {
            'title': request.data.get('title'),
            'body': request.data.get('body'),
            'author': request.user.id
        }

        serializer = PostSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=201)
        return Response(serializer.errors, status=400)

post_save.connect(send_email_on_post_create, sender=Post)


class UpdateDeletePostAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self,id):
        try:
            return Post.objects.get(id=id)
        
        except Post.DoesNotExist:
            return None
        

    def get(self, request, id):
        post = self.get_object(id)
        if not post:
            return Response({'detail':'post not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PostSerializer(post)
        return Response(serializer.data)
    
    def put(self, request, id):
        post = self.get_object(id)

        if not post:
            return Response({'detail':'post not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if post.author != request.user:
            
            return Response(
                {'detail': 'You do not have permission to update this post.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=201)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
    def delete(self, request, id):
        post = self.get_object(id)

        if not post:
            return Response({'detail':'post not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if post.author != request.user:
            
            return Response(
                {'detail': 'You do not have permission to delete this post.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
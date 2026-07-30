from django.shortcuts import render
from rest_framework.views import APIView
# Create your views here.
# class HomeView(APIView):
#     def post():



    
def index(request):
    return render(request, 'app/index.html')

def gameroom(request, room):
    return render(request, 'app/gameroom.html', {"room_name": room})

from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'app/index.html')

def gameroom(request, room):
    return render(request, 'app/gameroom.html', {"room_name": room})

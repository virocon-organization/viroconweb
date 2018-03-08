from django.shortcuts import render


def about(request):
    return render(request, 'info/about.html')


def impressum(request):
    return render(request, 'info/impressum.html')

def help(request):
    return render(request, 'info/help.html')

from django.shortcuts import render


def about(request):
    return render(request, 'contact/about.html')


def impressum(request):
    return render(request, 'contact/impressum.html')

def help(request):
    return render(request, 'contact/help.html')

from django.shortcuts import render


def home(request):
    """ returns the home.html

    Params
    ------
    request : request
        home call

    Returns
    -------
    HttpResponse
        to home.html
    """
    return render(request, 'home/home.html')

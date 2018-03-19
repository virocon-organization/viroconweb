"""
Manages Python functions which take Web requests and returns Web responses.
"""
from django.shortcuts import render


def about(request):
    """
    Takes a generated HttpRequest for the about page and returns a HttpResponse for the about page.

    Parameters
    ----------
    request : HttpRequest
        The generated request for the about page.


    Return
    ------
    HttpResponse
        Is based on the template info/about.html.

    """
    return render(request, 'info/about.html')


def imprint(request):
    """
    Takes a generated HttpRequest for the imprint page and returns a HttpResponse for the imprint page.

    Parameters
    ----------
    request : HttpRequest
        The generated request for the imprint page.


    Return
    ------
    HttpResponse
        Is based on the template info/imprint.html.

    """
    return render(request, 'info/imprint.html')


def help(request):
    """
    Takes a generated HttpRequest for the help page and returns a HttpResponse for the help page.

    Parameters
    ----------
    request : HttpRequest
        The generated request for the help page.


    Return
    ------
    HttpResponse
        Is based on the template info/help.html.

    """
    return render(request, 'info/help.html')

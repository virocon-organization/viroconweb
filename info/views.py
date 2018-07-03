"""
Manages Python functions which take Web requests and returns Web responses.
"""
from django.shortcuts import render
from contour.settings import VIROCON_CITATION
from viroconweb.settings import VERSION as VIROCONWEB_VERSION
from viroconcom.version import __version__ as VIROCONCOM_VERSION


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
    return render(request,
                  'info/about.html',
                  {'user': request.user,
                   'virocon_citation': VIROCON_CITATION,
                   'viroconweb_version': VIROCONWEB_VERSION,
                   'viroconcom_version': VIROCONCOM_VERSION,}
                  )


def imprint(request):
    """
    Returns a HttpResponse for the Legal Info page.

    Parameters
    ----------
    request : HttpRequest
        The generated request for the Legal Info page.


    Return
    ------
    HttpResponse
        Is based on the template info/imprint.html.

    """
    return render(request, 'info/imprint.html')


def terms(request):
    """
    Returns a HttpResponse for the Terms of Service page.

    Parameters
    ----------
    request : HttpRequest
        The request for the Terms of Service page.


    Return
    ------
    HttpResponse
        Is based on the template info/terms_and_privacy.html.

    """
    return render(request, 'info/terms_and_privacy.html')


def privacy(request):
    """
    Returns a HttpResponse for the Privacy Polcy page.

    Parameters
    ----------
    request : HttpRequest
        The request for the Privacy Policy page.


    Return
    ------
    HttpResponse
        Is based on the template info/terms_and_privacy.html.

    """
    return render(request, 'info/terms_and_privacy.html')


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

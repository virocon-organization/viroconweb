from django.shortcuts import render


def about(request):
    """ returns about page.

    Parameters
    ----------
    request : request
        about call

    Returns
    -------
    HttpResponse
        to about page.
    """
    return render(request, 'contact/about.html')


def impressum(request):
    """ returns imprint page.

        Parameters
        ----------
        request : request
            imprint call

        Returns
        -------
        HttpResponse
            to imprint page.
        """
    return render(request, 'contact/impressum.html')


def help(request):
    """ returns help page.

        Parameters
        ----------
        request : request
            help call

        Returns
        -------
        HttpResponse
            to help page.
        """
    return render(request, 'contact/help.html')

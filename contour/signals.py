from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import MeasureFileModel, ProbabilisticModel, EnvironmentalContour
import os
import shutil
import warnings

from virocon.settings import USE_S3


# Thanks to: https://stackoverflow.com/questions/33080360/how-to-delete-files-
# from-filesystem-using-post-delete-django-1-8 as well as to:
# https://stackoverflow.com/questions/28135029/django-signals-not-working
def _delete_file(instance, path):
    """
   Deletes a file or folder from the filesystem.

   Parameters
   ----------
   instance : The object that was deleted,
        E.g. a MeasureFileModel or ProbabilisticModel object.
   path: str,
       The path of the file or folder.
   """
    if path:
        if path=='S3':
            if instance.__class__.__name__ == 'MeasureFileModel':
                instance.measure_file.delete(save=False)
                instance.scatter_plot.delete(save=False)
            elif instance.__class__.__name__ == 'PlottedFigure':
                instance.image.delete(save=False)
            elif instance.__class__.__name__ == 'EnvironmentalContour':
                instance.latex_report.delete(save=False)
        else:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
    else:
        warnings.warn("Cannot delete the path with the value " + str(path))


# Thanks to: https://stackoverflow.com/questions/17507784/consolidating-
# multiple-post-save-signals-with-one-receiver
@receiver(post_delete)
def delete_file(sender, instance=None, **kwargs):
    """
    Deletes a file when the corresponding MeasureFileModel object is deleted.

    Parameters
    ----------
    sender : Class of object that was deleted,
        E.g. the class MeasureFileModel or ProbabilisticModel.
    instance : The object that was deleted,
        E.g. a MeasureFileModel or ProbabilisticModel object.
    """
    list_of_models = ('MeasureFileModel, '
                      'ProbabilisticModel, '
                      'EnvironmentalContour, '
                      'PlottedFigure')
    if sender.__name__ in list_of_models:
        if hasattr(instance, 'path_of_statics') and instance.path_of_statics:
            _delete_file(instance, instance.path_of_statics)
        if sender.__name__ == 'MeasureFileModel' and instance.measure_file:
            print('Deleting MeasureFile')
            if USE_S3:
                _delete_file(instance, path='S3')
            else:
                _delete_file(instance, instance.measure_file.path)
        elif sender.__name__ == 'PlottedFigure' and instance.image:
            if USE_S3:
                _delete_file(instance, path='S3')
            else:
                _delete_file(instance, instance.image.path)
        elif sender.__name__ == 'EnvironmentalContour' and instance.latex_report:
            if USE_S3:
                _delete_file(instance, path='S3')
            else:
                _delete_file(instance, instance.latex_report.path)

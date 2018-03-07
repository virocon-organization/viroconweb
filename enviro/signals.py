from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import MeasureFileModel, ProbabilisticModel, EnvironmentalContour
import os
import shutil
import warnings


# Thanks to: https://stackoverflow.com/questions/33080360/how-to-delete-files-
# from-filesystem-using-post-delete-django-1-8 as well as to:
# https://stackoverflow.com/questions/28135029/django-signals-not-working
def _delete_file(path):
   """
   Deletes a file or folder from the filesystem.

   Parameters
   ----------
   path: str,
       The path of the file or folder.
   """
   if path:
       if os.path.isfile(path):
           os.remove(path)
       elif os.path.isdir(path):
           shutil.rmtree(path)
   else:
       warnings.warn("Cannot delete the path with the value " + str(path))

# Thanks to: https://stackoverflow.com/questions/17507784/consolidating-
# multiple-post-save-signals-with-one-receiver
@receiver(post_delete)
def delete_file(sender, instance=None,  **kwargs):
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
                      'EnvironmentalContour')
    if sender.__name__ in list_of_models:
        if instance.path_of_statics:
            _delete_file(instance.path_of_statics)
        if sender.__name__ == 'MeasureFileModel':
            if instance.measure_file:
                _delete_file(instance.measure_file.path)
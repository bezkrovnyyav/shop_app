import os
from django.db import models

def _delete_file(path):
   """ Deletes file from filesystem. """
   if os.path.isfile(path):
       os.remove(path)


@receiver(models.signals.post_delete, sender=Product)
def delete_file(sender, instance, *args, **kwargs):
    """ Deletes thumbnail files on `post_delete` """
    if instance.photo:
        _delete_file(instance.photo.path)
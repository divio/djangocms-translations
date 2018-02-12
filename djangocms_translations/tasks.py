from distutils.util import strtobool
import os

from celery import Celery

from .models import TranslationRequest

# FIXME: Ideally we should use @shared_task but for this we need a broker (even when testing locally)
app = Celery('djangocms_translations')
app.conf.update({'task_always_eager': bool(strtobool(os.environ.get('CELERY_ALWAYS_EAGER', '0')))})


@app.task
def prepare_translation_bulk_request(translation_request_id):
    translation_request = TranslationRequest.objects.get(id=translation_request_id)
    translation_request.export_content_from_cms()
    translation_request.get_quote_from_provider()

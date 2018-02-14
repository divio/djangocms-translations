from celery import shared_task

from .models import TranslationRequest


@shared_task
def prepare_translation_bulk_request(translation_request_id):
    translation_request = TranslationRequest.objects.get(id=translation_request_id)
    translation_request.export_content_from_cms()
    translation_request.get_quote_from_provider()

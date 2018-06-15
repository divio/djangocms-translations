# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, UpdateView, DetailView
from django.utils.translation import ugettext

from cms.utils.conf import get_cms_setting

from . import forms, models
from .cms_renderer import UnboundPluginRenderer
from .models import TranslationRequest


@require_GET
@login_required
def adjust_import_data_view(request, pk):
    if not request.toolbar.structure_mode_active:
        # always force structure mode
        structure = get_cms_setting('CMS_TOOLBAR_URL__BUILD')
        return redirect(request.path + '?' + structure)

    requests = (
        TranslationRequest
        .objects
        .filter(state=TranslationRequest.STATES.IMPORT_FAILED)
    )
    trans_request = get_object_or_404(requests, pk=pk)

    if not trans_request.archived_placeholders.exists():
        raise Http404

    archived_placeholders = trans_request.archived_placeholders.iterator()
    # Force the cms to use our custom renderer
    request.toolbar.__dict__['structure_renderer'] = UnboundPluginRenderer(
        request,
        language=trans_request.target_language,
        placeholders=[ar_pl.placeholder for ar_pl in archived_placeholders],
    )
    request.toolbar.__dict__['uses_legacy_structure_mode'] = False
    context = {
        'toolbar': request.toolbar,
        'trans_request': trans_request,
    }
    return render(request, 'djangocms_translations/adjust_import_data.html', context)


@csrf_exempt
@require_POST
def process_provider_callback_view(request, pk):
    requests = (
        TranslationRequest
        .objects
        .filter(state=TranslationRequest.STATES.IN_TRANSLATION)
    )
    trans_request = get_object_or_404(requests, pk=pk)
    success = trans_request.import_response(request.body)
    return JsonResponse({'success': success})


@login_required
def import_from_archive(request, pk):
    requests = (
        TranslationRequest
        .objects
        .filter(state=TranslationRequest.STATES.IMPORT_FAILED)
    )
    trans_request = get_object_or_404(requests, pk=pk)

    if not trans_request.archived_placeholders.exists():
        raise Http404

    if request.method == 'POST':
        target_cms_page = trans_request.target_cms_page

        try:
            trans_request._import_from_archive()
        except IntegrityError:
            messages.error(request, ugettext('Failed to import plugins.'))
            redirect_to = reverse('admin:translation-request-adjust-import-data', args=(pk,))
        else:
            messages.error(request, ugettext('Plugins imported successfully.'))
            redirect_to = target_cms_page.get_absolute_url(trans_request.target_language)
        return redirect(redirect_to)

    context = {
        "title": ugettext('Import from archive'),
        "object": trans_request,
        "opts": TranslationRequest._meta,
        "app_label": TranslationRequest._meta.app_label,
    }
    return render(request, 'djangocms_translations/import_confirmation.html', context)


class CreateTranslationRequestView(CreateView):
    template_name = 'djangocms_translations/create_request.html'
    form_class = forms.CreateTranslationForm

    def get_success_url(self):
        return reverse('admin:choose-translation-quote', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        form_kwargs = super(CreateTranslationRequestView, self).get_form_kwargs()
        form_kwargs['user'] = self.request.user
        form_kwargs['initial'] = self.request.GET.dict()
        return form_kwargs

    def form_valid(self, form):
        response = super(CreateTranslationRequestView, self).form_valid(form)
        self.object.set_content_from_cms()
        self.object.get_quote_from_provider()
        return response


class ChooseTranslationQuoteView(UpdateView):
    template_name = 'djangocms_translations/choose_quote.html'
    form_class = forms.ChooseTranslationQuoteForm
    model = models.TranslationRequest

    def get_success_url(self):
        return reverse('admin:djangocms_translations_translationrequest_changelist')

    def form_valid(self, form):
        response = super(ChooseTranslationQuoteView, self).form_valid(form)
        self.object.set_status(models.TranslationRequest.STATES.READY_FOR_SUBMISSION)
        self.object.submit_request()
        return response


@csrf_exempt
@require_POST
def get_quote_from_provider_view(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied

    translation_request = get_object_or_404(
        TranslationRequest.objects.filter(state=TranslationRequest.STATES.PENDING_QUOTE),
        pk=pk,
    )
    translation_request.get_quote_from_provider()
    return JsonResponse({'success': True})


class TranslationRequestStatusView(DetailView):
    template_name = 'djangocms_translations/status_detail.html'
    model = models.TranslationRequest


class CheckRequestStatusView(DetailView):
    model = models.TranslationRequest

    def get_success_url(self):
        return reverse('admin:djangocms_translations_translationrequest_changelist')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.check_status()
        messages.success(request, 'Status updated.')
        return redirect(self.get_success_url())

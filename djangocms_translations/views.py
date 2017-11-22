# -*- coding: utf-8 -*-
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, UpdateView, DetailView

from . import forms, models


class CreateTranslationRequestView(CreateView):
    template_name = 'djangocms_translations/create_request.html'
    form_class = forms.CreateTranslationForm

    def get_success_url(self):
        return reverse('admin:choose-translation-quote', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super(CreateTranslationRequestView, self).form_valid(form)
        self.object.export_content_from_cms()
        self.object.get_quote_from_provider()
        return response

    def get_initial(self):
        return {
            'source_language': self.request.GET.get('source_lang') or None,
            'target_language': self.request.GET.get('target_lang') or None,
            'user': self.request.user,
            'cms_page': self.request.GET.get('cms_page_id'),
        }


class TranslationRequestProviderCallbackView(UpdateView):
    model = models.TranslationRequest

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(TranslationRequestProviderCallbackView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        success = self.get_object().import_response(request.body)
        return JsonResponse({'success': success})


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


class ImportProviderResponse(UpdateView):
    model = models.TranslationRequest

    def get_success_url(self):
        return self.object.cms_page.get_absolute_url(language=self.object.target_language)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success = self.object.import_response(self.object.order.response_content)

        if success:
            messages.success(request, 'Imported content.')
            return redirect(self.get_success_url())
        messages.error(request, 'Failed to import content.')
        return redirect('admin:translation-request-import-response', args=(self.object.pk,))

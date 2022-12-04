
from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    '''Описание класса AboutAuthorView для страницы about/author'''
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    '''Описание класса AboutTechView для страницы about/tech'''
    template_name = 'about/tech.html'

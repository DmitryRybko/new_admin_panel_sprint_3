from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from ...models import Filmwork


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def get_queryset(self):
        movie_detail = Filmwork.objects.prefetch_related('genres', 'persons').values("id", "title", "description", "creation_date", "rating", "type")\
            .annotate(genres=ArrayAgg('genres__name',
                                      distinct=True),
                      actors=ArrayAgg('persons__full_name', filter=Q(personfilmwork__role="actor"),
                                      distinct=True),
                      directors=ArrayAgg('persons__full_name', filter=Q(personfilmwork__role="director"),
                                         distinct=True),
                      writers=ArrayAgg('persons__full_name', filter=Q(personfilmwork__role="writer"),
                                       distinct=True))
        return movie_detail

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):

        queryset = self.get_queryset()
        paginator, actual_page, queryset, is_paginated = self.paginate_queryset(queryset, self.paginate_by)

        page_num = self.request.GET.get('page', 1)

        if page_num == "last":
            page_num = paginator.num_pages
            next_page = None
            previous_page = int(page_num) - 1

        elif page_num == 1:
            previous_page = None
            next_page = int(page_num) + 1

        else:
            previous_page = int(page_num) - 1
            next_page = int(page_num) + 1

        context = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': previous_page,
            'next': next_page,
            'results': list(queryset),
        }
        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):

    pk_url_kwarg = 'movie_id'

    def get_context_data(self, *, object_list=None, **kwargs):

        movie = kwargs.get("object")
        if movie:
            return movie

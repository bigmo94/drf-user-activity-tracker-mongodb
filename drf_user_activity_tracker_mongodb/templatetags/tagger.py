from urllib.parse import urlencode

from django import template

from drf_user_activity_tracker_mongodb.utils import CustomPaginator

register = template.Library()


@register.simple_tag
def under_score_tag(obj, attribute):
    obj = dict(obj)
    return obj.get(attribute)


@register.simple_tag
def clean_url_encode(data, remove):
    attrs = data.copy()
    if remove in data:
        attrs.pop(remove)
    return urlencode(attrs)


@register.simple_tag
def get_proper_elided_page_range(p, count, number, on_each_side=3, on_ends=2):
    paginator = CustomPaginator(p.dataset, count, p.per_page)
    return paginator.get_elided_page_range(number=number,
                                           on_each_side=on_each_side,
                                           on_ends=on_ends)

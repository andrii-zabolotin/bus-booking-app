from django import template

register = template.Library()


@register.filter(name="query_transform")
def query_transform(request, **kwargs):
    """usages: {% query_transform request page=1 %}"""
    updated = request.GET.copy()

    for k, v in kwargs.items():
        updated[k] = v

    # trash any pjax params, we never want to render those
    try:
        del updated["page"]
    except KeyError:
        pass

    return updated.urlencode()

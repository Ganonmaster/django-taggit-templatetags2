from django import template
from django.db import models
from django.db.models import Count
from django.db.models.loading import get_model, cache
from django.core.exceptions import FieldError

from classytags.core import Options
from classytags.arguments import Argument
from classytags.helpers import AsTag

from taggit import VERSION as TAGGIT_VERSION
from taggit.managers import TaggableManager
from taggit.models import TaggedItem, Tag
from taggit_templatetags import settings

T_MAX = getattr(settings, 'TAGCLOUD_MAX', 6.0)
T_MIN = getattr(settings, 'TAGCLOUD_MIN', 1.0)

register = template.Library()

class ModelResolver(object):
    def __init__(self, real):
        self.real = real

    def resolve(self, context):
        value = self.real.resolve(context)
        app, model = value.split(".")
        return cache.get_model(app, model)


class ModelArgument(Argument):
    def parse_token(self, parser, token):
        real = super(ModelArgument, self).parse_token(parser, token)
        return ModelResolver(real)
        
def get_queryset(forvar=None, taggeditem_model, tag_model):
    through_opts = taggeditem_model._meta
    count_field = ("%s_%s_items" % (through_opts.app_label,
                    through_opts.object_name)).lower()

    if forvar is None:
        # get all tags
        queryset = tag_model.objects.all()
    else:
        # extract app label and model name
        beginning, applabel, model = None, None, None
        try:
            beginning, applabel, model = forvar.rsplit('.', 2)
        except ValueError:
            try:
                applabel, model = forvar.rsplit('.', 1)
            except ValueError:
                applabel = forvar
        applabel = applabel.lower()
        
        # filter tagged items        
        if model is None:
            # Get tags for a whole app
            queryset = taggeditem_model.objects.filter(content_type__app_label=applabel)
            tag_ids = queryset.values_list('tag_id', flat=True)
            queryset = tag_model.objects.filter(id__in=tag_ids)
        else:
            # Get tags for a model
            model = model.lower()
            if ":" in model:
                model, manager_attr = model.split(":", 1)
            else:
                manager_attr = "tags"
            model_class = get_model(applabel, model)
            manager = getattr(model_class, manager_attr)
            queryset = manager.all()

    return queryset.annotate(num_times=Count(count_field))


def get_weight_fun(t_min, t_max, f_min, f_max):
    def weight_fun(f_i, t_min=t_min, t_max=t_max, f_min=f_min, f_max=f_max):
        # Prevent a division by zero here, found to occur under some
        # pathological but nevertheless actually occurring circumstances.
        if f_max == f_min:
            mult_fac = 1.0
        else:
            mult_fac = float(t_max-t_min)/float(f_max-f_min)
        return t_max - (f_max-f_i)*mult_fac
    return weight_fun
     
class TaggitBaseTag(AsTag):

    options = Options(
        'as',
        Argument('varname', resolve=False, required=False),
        'for',
        Argument('forvar', required=False),
        'limit',
        Argument('limit', required=False, default=10),
        'taggeditem_model',
        ModelArgument('taggeditem_model', required=False, default=TaggedItem),
        'tag_model',
        ModelArgument('tag_model', required=False, default=Tag)
    )
    
@register.tag   
class GetTagList(TaggitBaseTag):
    name = 'get_taglist'
    
    def get_value(self, context, forvar, limit, taggeditem_model, tag_model):
        queryset = get_queryset(forvar, taggeditem_model, tag_model)        
        queryset = queryset.order_by('-num_times')        
        context[asvar] = queryset
        if limit:
            queryset = queryset[:limit]
        return ''

@register.tag   
class GetTagCloud(TaggitBaseTag):
    name = 'get_tagcloud'

    def get_value(self, context, forvar, limit, taggeditem_model, tag_model):
        queryset = get_queryset(forvar, taggeditem_model, tag_model)
        num_times = queryset.values_list('num_times', flat=True)
        if(len(num_times) == 0):
            context[asvar] = queryset
            return ''
        weight_fun = get_weight_fun(T_MIN, T_MAX, min(num_times), max(num_times))
        queryset = queryset.order_by('name')
        if limit:
            queryset = queryset[:limit]
        for tag in queryset:
            tag.weight = weight_fun(tag.num_times)
        context[asvar] = queryset
        return ''
     
# method from
# https://github.com/dokterbob/django-taggit-templatetags/commit/fe893ac1c93d58cd122c621804f311430c93dc12  
# {% get_similar_obects to product as similar_videos for metaphore.embeddedvideo %}
@register.tag
class GetSimilarObjects(AsTag):
    name = 'get_similar_objects'
    options = Options(
        'to',
        Argument('to', resolve=False, required=False),
        'as',
        Argument('varname', required=False),
        'for',
        Argument('forvar', required=False),
        'taggeditem_model',
        ModelArgument('taggeditem_model', required=False, default=TaggedItem)
    )
    def get_value(self, context, tovar, asvar, forvar, taggeditem_model):
        if forvar:
            assert hasattr(tovar, 'tags')
            tags = tovar.tags.all()
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(forvar)
            items = taggeditem_model.objects.filter(content_type=ct, tag__in=tags)
            from django.db.models import Count
            ordered = items.values('object_id').annotate(Count('object_id')).order_by()
            ordered_ids = map(lambda x: x['object_id'], ordered)
            objects = ct.model_class().objects.filter(pk__in=ordered_ids)
        else:
            objects = tovar.tags.similar_objects()
        context[asvar] = objects    
        return ''    

    
def include_tagcloud(forvar=None):
    return {'forvar': forvar}

def include_taglist(forvar=None):
    return {'forvar': forvar}
  
register.inclusion_tag('taggit_templatetags/taglist_include.html')(include_taglist)
register.inclusion_tag('taggit_templatetags/tagcloud_include.html')(include_tagcloud)

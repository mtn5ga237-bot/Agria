from django import template

register = template.Library()


@register.filter(name='split')
def split(valeur, separateur=','):
    """Coupe une chaine en liste selon le separateur donne (usage : {{ "a,b"|split:"," }})."""
    return [item.strip() for item in valeur.split(separateur)]


@register.simple_tag(takes_context=True)
def actif_si(context, prefixe):
    """Retourne 'active' si le chemin courant commence par le prefixe donne (surlignage du menu lateral)."""
    request = context.get('request')
    if not request:
        return ''
    return 'active' if request.path.startswith(prefixe) else ''


@register.filter(name='dictget')
def dictget(dictionnaire, cle):
    """Acces a une valeur de dictionnaire par une cle variable (usage : {{ mon_dict|dictget:cle }}),
    ce que le gabarit Django ne permet pas nativement (seul mon_dict.cle_litterale fonctionne)."""
    if not dictionnaire:
        return None
    return dictionnaire.get(cle)


@register.filter(name='add_class')
def add_class(champ, classes):
    """Ajoute des classes CSS (Bootstrap) a un champ de formulaire Django dans le gabarit."""
    widget = champ.field.widget
    existantes = widget.attrs.get('class', '')
    fusionnees = f'{existantes} {classes}'.strip()
    return champ.as_widget(attrs={**widget.attrs, 'class': fusionnees})

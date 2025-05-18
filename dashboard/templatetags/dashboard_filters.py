from django import template
import os
import re

register = template.Library()

@register.filter
def youtube_embed_url(url):
    """
    Convertit une URL YouTube en URL embed
    Exemple: https://www.youtube.com/watch?v=ABCDEFG -> https://www.youtube.com/embed/ABCDEFG
    """
    if not url:
        return ''
    
    # Motifs pour les URLs YouTube
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&\s]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([^\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f'https://www.youtube.com/embed/{video_id}'
    
    # Si aucun motif ne correspond, retourner l'URL originale
    return url

@register.filter
def filename(path):
    """
    Extrait le nom du fichier d'un chemin complet
    Exemple: /path/to/file.txt -> file.txt
    """
    return os.path.basename(path) if path else ''

@register.filter
def get_content_type_icon(content_type):
    """
    Retourne la classe d'icône Bootstrap en fonction du type de contenu
    """
    icons = {
        'text': 'bi-file-text',
        'video': 'bi-camera-video',
        'file': 'bi-file-earmark',
        'image': 'bi-image',
        'url': 'bi-link'
    }
    return icons.get(content_type, 'bi-question-circle') 
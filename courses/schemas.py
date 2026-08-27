# courses/schemas.py

SECTION_SCHEMAS = {
    'TEXT': {
        'label': 'Paragraphe Texte',
        'fields': {
            'text': {
                'type': 'string',
                'widget': 'rich-text',  # Indique au frontend d'afficher un éditeur WYSIWYG/Markdown
                'label': 'Contenu du texte',
                'required': True
            }
        }
    },
    'IMAGE': {
        'label': 'Image avec légende',
        'fields': {
            'url': {
                'type': 'string',
                'widget': 'image-uploader',  # Indique au frontend d'afficher un champ avec bouton d'upload/champ URL
                'label': 'Lien de l\'image',
                'required': True
            },
            'caption': {
                'type': 'string',
                'widget': 'text-input',  # Champ texte simple <input type="text">
                'label': 'Légende',
                'required': False
            }
        }
    },
    'CODE': {
        'label': 'Extrait de code',
        'fields': {
            'language': {
                'type': 'string',
                'widget': 'select',  # Liste déroulante <select>
                'options': ['python', 'javascript', 'html', 'css', 'sql'],
                'label': 'Langage de programmation',
                'default': 'python'
            },
            'code': {
                'type': 'string',
                'widget': 'code-editor',  # Éditeur de code type Monaco / VS Code intégrateur
                'label': 'Code source',
                'required': True
            }
        }
    }
}
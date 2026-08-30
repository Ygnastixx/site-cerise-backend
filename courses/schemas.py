# Déclare le schéma des types de sections de cours

SECTION_SCHEMAS = {
    'TITLE': {
        'label': 'Titre / En-tête',
        'layout': 'TITLE_SLIDE',
        'fields': {}
    },
    'TEXT': {
        'label': 'Paragraphe Texte', # label lisible dans le frontend pour l'utilisateur
        'layout': 'TEXT_LAYOUT', # Identifiant du layout pour les slides dans le studio
        'fields': { # Description des champs de contenu pour le frontend (formulaire de saisie)
            'text': {
                'type': 'string', # Type de donnée attendu (string, number, array, object, etc.)
                'widget': 'rich-text', # Type de widget pour le frontend (éditeur de texte enrichi, éditeur de code, uploader d'image, etc.)
                'label': 'Contenu du texte', 
                'required': False # Indique si le champ est obligatoire ou non pour le frontend
            }
        },
        'extractor': lambda content: {"body": content.get("text", "")} # Fonction pour extraire les données pertinentes du champ JSON 'content' pour le slide final.
    },
    'IMAGE': {
        'label': 'Image avec légende',
        'layout': 'IMAGE_LAYOUT',
        'fields': {
            'url': {'type': 'string', 'widget': 'image-uploader', 'label': "Lien de l'image", 'required': False},
            'caption': {'type': 'string', 'widget': 'text-input', 'label': 'Légende', 'required': False}
        },
        'extractor': lambda content: {
            "image_url": content.get("url", ""),
            "caption": content.get("caption", "")
        }
    },
    'CODE': {
        'label': 'Extrait de code',
        'layout': 'CODE_LAYOUT',
        'fields': {
            'language': {
                'type': 'string',
                'widget': 'select',
                'options': ['python', 'javascript', 'html', 'css', 'sql'],
                'label': 'Langage de programmation',
                'default': 'python'
            },
            'code': {'type': 'string', 'widget': 'code-editor', 'label': 'Code source', 'required': False}
        },
        'extractor': lambda content: {
            "code_content": content.get("code", ""),
            "language": content.get("language", "text")
        }
    },
    'LIST': {
        'label': 'Liste à puces',
        'layout': 'LIST_LAYOUT',
        'fields': {
            'items': {'type': 'array', 'widget': 'list-input', 'label': 'Éléments', 'required': False}
        },
        'extractor': lambda content: {"items": content.get("items", [])}
    },
    'CALLOUT': {
        'label': "Encart d'attention",
        'layout': 'CALLOUT_LAYOUT',
        'fields': {
            'text': {'type': 'string', 'widget': 'text-input', 'label': 'Texte', 'required': False}
        },
        'extractor': lambda content: {"text": content.get("text", "")}
    }
}
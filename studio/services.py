"""Moteurs de generation du Studio.

Trois moteurs independants, un par module de l'equipe :
  - `construire_slides`    : structure abstraite des diapositives (Developpeur 1)
  - `construire_affiche`   : donnees d'une affiche de seance      (Developpeur 2)
  - `generer_texte_social` : texte d'annonce redige par IA        (Developpeur 3)
"""

import logging

from django.conf import settings
import requests
from django.utils import formats, timezone

from courses.schemas import SECTION_SCHEMAS

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Slides
# --------------------------------------------------------------------------

# Chaque type de section produit une mise en page et un champ de contenu distincts.


def _slide_depuis_section(section, numero):
    """Traduit une section en diapositive exploitable par le Frontend."""
    # 1. Récupère la config depuis SECTION_SCHEMAS ou applique un fallback
    schema = SECTION_SCHEMAS.get(section.type, {})
    layout = schema.get("layout", "TEXT_LAYOUT")

    slide = {
        "slide_number": numero,
        "type": layout,
        "title": section.title,
    }

    contenu = section.content if isinstance(section.content, dict) else {}

    # 2. Utilise l'extractor propre au type si défini dans SECTION_SCHEMAS
    extractor = schema.get("extractor")
    if extractor and callable(extractor):
        slide.update(extractor(contenu))
    else:
        # Fallback par défaut : injecte les clés JSON directement dans le slide
        slide.update(contenu)

    return slide


def construire_slides(course):
    """Aplatit l'arbre des sections d'un cours en une liste ordonnee de slides.

    L'arbre est parcouru en profondeur : une sous-section suit immediatement sa
    section parente, ce qui preserve l'ordre de lecture du cours.
    """
    sections = list(course.sections.all().order_by("order", "id"))

    enfants_par_parent = {}
    racines = []
    for section in sections:
        if section.parent_id is None:
            racines.append(section)
        else:
            enfants_par_parent.setdefault(section.parent_id, []).append(section)

    slides = []
    compteur = 1

    # Diapositive d'ouverture : le titre de la presentation.
    slides.append(
        {
            "slide_number": compteur,
            "type": "TITLE_SLIDE",
            "title": course.title,
            "subtitle": course.description,
        }
    )
    compteur += 1

    def parcourir(noeud):
        nonlocal compteur
        slides.append(_slide_depuis_section(noeud, compteur))
        compteur += 1
        for enfant in enfants_par_parent.get(noeud.id, []):
            parcourir(enfant)

    for racine in racines:
        parcourir(racine)

    return {"presentation_title": course.title, "slides": slides}


# --------------------------------------------------------------------------
# Affiches
# --------------------------------------------------------------------------


def _date_en_toutes_lettres(valeur):
    """Formate une date en francais : "Samedi 15 octobre a 14h00"."""
    date_locale = timezone.localtime(valeur)
    jour = formats.date_format(date_locale, "l").capitalize()
    jour_et_mois = formats.date_format(date_locale, "j F")
    heure = formats.date_format(date_locale, "H\\hi")
    return f"{jour} {jour_et_mois} a {heure}"


def construire_affiche(session, template=None):
    """Assemble les donnees d'affiche d'une seance pour le composant Frontend."""
    materiels = [
        reservation.equipment.name
        for reservation in session.equipment_reservations.select_related("equipment").all()
    ]

    donnees = {
        "title": session.theme,
        "date_formatted": _date_en_toutes_lettres(session.date),
        "location": session.location,
        "materials_needed": materiels,
    }

    if template is not None:
        donnees["template"] = {
            "id": template.id,
            "name": template.name,
            "layout_type": template.layout_type,
            "template_file": template.template_file,
        }

    return donnees


# --------------------------------------------------------------------------
# Texte d'annonce pour les reseaux sociaux
# --------------------------------------------------------------------------


def _texte_de_repli(session, materiels):
    """Texte compose localement, utilise quand l'API d'IA est indisponible.

    L'endpoint doit rester fonctionnel sans cle API : le staff obtient un
    brouillon exploitable plutot qu'une erreur.
    """
    lignes = [
        f"Rendez-vous le {_date_en_toutes_lettres(session.date)} "
        f"pour notre seance sur le theme : {session.theme}.",
        f"Lieu : {session.location}.",
    ]

    if session.description:
        lignes.append(session.description)

    if materiels:
        lignes.append("Materiel prevu : " + ", ".join(materiels) + ".")

    lignes.append("Inscrivez-vous des maintenant et rejoignez-nous !")
    return "\n\n".join(lignes)


def generer_texte_social(session):
    """Redige un texte d'annonce pour Facebook / LinkedIn.

    Renvoie le couple (texte, source) ou `source` vaut "ai" ou "fallback",
    afin que le Frontend sache si le texte a ete redige par l'IA.
    """
    materiels = [
        reservation.equipment.name
        for reservation in session.equipment_reservations.select_related("equipment").all()
    ]

    if not settings.OPENROUTER_API_KEY:
        logger.info("OPENROUTER_API_KEY absente : generation locale du texte d'annonce.")
        return _texte_de_repli(session, materiels), "fallback"

    consignes = (
        "Tu rediges les annonces d'un club universitaire de robotique et "
        "d'electronique. Ecris un post court (3 a 5 phrases) en francais, "
        "chaleureux et incitatif, pour annoncer une seance. Utilise deux ou "
        "trois emojis pertinents. Termine par un appel a participer. "
        "Reponds uniquement par le texte du post, sans commentaire."
    )

    faits = [
        f"Theme : {session.theme}",
        f"Date : {_date_en_toutes_lettres(session.date)}",
        f"Lieu : {session.location}",
    ]
    if session.description:
        faits.append(f"Description : {session.description}")
    if session.course:
        faits.append(f"Cours associe : {session.course.title}")
    if materiels:
        faits.append("Materiel : " + ", ".join(materiels))

    try:
        reponse = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "anthropic/claude-sonnet-4.5",  # <- a ajuster selon le modele voulu sur OpenRouter
                "max_tokens": 500,
                "messages": [
                    {"role": "system", "content": consignes},
                    {"role": "user", "content": "\n".join(faits)},
                ],
            },
            timeout=15,
        )
        reponse.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Appel OpenRouter en echec (%s) : repli sur le texte local.", exc)
        return _texte_de_repli(session, materiels), "fallback"

    donnees = reponse.json()
    try:
        texte = donnees["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        logger.warning("Reponse OpenRouter inattendue : repli sur le texte local.")
        return _texte_de_repli(session, materiels), "fallback"

    if not texte:
        return _texte_de_repli(session, materiels), "fallback"

    return texte, "ai"
def generer_texte_social_openrouter(session):
    if not settings.OPENROUTER_API_KEY:
        return _texte_de_repli(session, []), "fallback"

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free", # ou un autre modèle gratuit
        "messages": [
            {"role": "system", "content": "Tu rédiges des annonces de club de robotique..."},
            {"role": "user", "content": f"Thème : {session.theme}\nLieu : {session.location}"}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip(), "ai"
    except Exception as e:
        logger.warning("Erreur OpenRouter: %s", e)

    return _texte_de_repli(session, []), "fallback"

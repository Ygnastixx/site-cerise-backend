from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from courses.models import Course, Section
from inventory.models import Equipment
from sessions_app.models import Session, SessionEquipment
from studio.models import SlideTemplate

User = get_user_model()


class Command(BaseCommand):
    help = "Remplit la base avec des données de démonstration présentables pour la vidéo."

    def handle(self, *args, **options):
        self.stdout.write("Création des utilisateurs...")

        admin, _ = User.objects.get_or_create(matricule="0001", defaults=dict(
            username="Admin Club", email="admin@club-robotique.fr"))
        admin.set_password("Demo1234!")
        admin.role, admin.is_approved, admin.is_staff, admin.is_superuser = "ADMIN", True, True, True
        admin.save()

        staff, _ = User.objects.get_or_create(matricule="0002", defaults=dict(
            username="Camille Staff", email="camille@club-robotique.fr"))
        staff.set_password("Demo1234!")
        staff.role, staff.is_approved = "STAFF", True
        staff.save()

        membre1, _ = User.objects.get_or_create(matricule="0003", defaults=dict(
            username="Jean Membre", email="jean@club-robotique.fr"))
        membre1.set_password("Demo1234!")
        membre1.role, membre1.is_approved = "MEMBER", True
        membre1.save()

        en_attente, _ = User.objects.get_or_create(matricule="0004", defaults=dict(
            username="Alex Nouveau", email="alex@club-robotique.fr"))
        en_attente.set_password("Demo1234!")
        en_attente.role, en_attente.is_approved = "MEMBER", False
        en_attente.save()

        self.stdout.write("Création du matériel...")
        esp32, _ = Equipment.objects.get_or_create(name="Carte ESP32", defaults=dict(
            brand="Espressif", model="ESP32-WROOM-32", purchase_price=12.50, quantity=15,
            description="Microcontrôleur Wi-Fi/Bluetooth pour projets IoT"))
        fer, _ = Equipment.objects.get_or_create(name="Fer à souder 60W", defaults=dict(
            brand="Aneng", model="SL102", purchase_price=45.00, quantity=10,
            description="Fers à souder réglables avec embouts"))
        multimetre, _ = Equipment.objects.get_or_create(name="Multimètre numérique", defaults=dict(
            brand="Aneng", model="AN8008", purchase_price=25.00, quantity=8,
            description="Mesure tension, courant, résistance"))
        breadboard, _ = Equipment.objects.get_or_create(name="Plaque d'essai (breadboard)", defaults=dict(
            brand="Générique", model="830 points", purchase_price=3.50, quantity=30,
            description="Pour prototypage sans soudure"))

        self.stdout.write("Création des cours...")

        cours1, _ = Course.objects.get_or_create(title="Initiation à l'ESP32", defaults=dict(
            description="Découverte de la programmation ESP32 et du Wi-Fi embarqué",
            status=Course.Status.PUBLISHED, author=admin))
        if not cours1.sections.exists():
            s1 = Section.objects.create(course=cours1, title="Introduction", type="TITLE",
                                         content={"level": "h1"}, order=1)
            Section.objects.create(course=cours1, parent=s1, title="Pourquoi l'ESP32 ?", type="TEXT",
                content={"text": "L'ESP32 est un microcontrôleur peu coûteux, doté d'un Wi-Fi et d'un Bluetooth intégrés, parfait pour les objets connectés."}, order=2)
            Section.objects.create(course=cours1, parent=s1, title="Ce qu'il faut savoir", type="LIST",
                content={"items": ["Double coeur Xtensa 32 bits", "Wi-Fi 802.11 b/g/n", "Bluetooth Low Energy", "Alimentation 3.3V"]}, order=3)
            s2 = Section.objects.create(course=cours1, title="Premier programme", type="TITLE",
                                         content={"level": "h1"}, order=4)
            Section.objects.create(course=cours1, parent=s2, title="Code Blink Wi-Fi", type="CODE",
                content={"language": "cpp", "code": "void setup() {\n  pinMode(LED_BUILTIN, OUTPUT);\n}\n\nvoid loop() {\n  digitalWrite(LED_BUILTIN, HIGH);\n  delay(500);\n  digitalWrite(LED_BUILTIN, LOW);\n  delay(500);\n}"}, order=5)
            Section.objects.create(course=cours1, parent=s2, title="Attention", type="CALLOUT",
                content={"text": "Vérifie toujours le voltage avant de brancher la carte : l'ESP32 fonctionne en 3.3V, pas en 5V !"}, order=6)

        cours2, _ = Course.objects.get_or_create(title="Bases de l'électronique", defaults=dict(
            description="Les fondamentaux avant de se lancer dans un projet",
            status=Course.Status.PUBLISHED, author=staff))
        if not cours2.sections.exists():
            s = Section.objects.create(course=cours2, title="La loi d'Ohm", type="TITLE",
                                        content={"level": "h1"}, order=1)
            Section.objects.create(course=cours2, parent=s, title="Définition", type="TEXT",
                content={"text": "U = R × I. La tension est égale à la résistance multipliée par le courant."}, order=2)

        Course.objects.get_or_create(title="Introduction au PCB (brouillon)", defaults=dict(
            description="Cours en cours de rédaction", status=Course.Status.DRAFT, author=staff))

        Course.objects.get_or_create(title="Modèle : structure standard d'un cours", defaults=dict(
            description="Modèle vierge à dupliquer pour créer un nouveau cours",
            status=Course.Status.DRAFT, is_template=True, author=admin))

        self.stdout.write("Création des gabarits Studio...")
        SlideTemplate.objects.get_or_create(name="Affiche club - vert", defaults=dict(
            layout_type=SlideTemplate.LayoutType.POSTER, created_by=admin))
        SlideTemplate.objects.get_or_create(name="Diapositives - standard", defaults=dict(
            layout_type=SlideTemplate.LayoutType.SLIDE, created_by=admin))

        self.stdout.write("Création des séances...")
        dans_3_jours = timezone.now().replace(hour=14, minute=0, second=0, microsecond=0) + timezone.timedelta(days=3)
        semaine_prochaine = dans_3_jours + timezone.timedelta(days=7)

        session1, created1 = Session.objects.get_or_create(theme="Initiation ESP32", defaults=dict(
            date=dans_3_jours, location="Salle de TP 3",
            description="Premier contact avec le microcontrôleur ESP32", course=cours1))
        if created1:
            SessionEquipment.objects.create(session=session1, equipment=esp32, quantity_reserved=10)
            SessionEquipment.objects.create(session=session1, equipment=breadboard, quantity_reserved=10)

        session2, created2 = Session.objects.get_or_create(theme="Atelier soudure", defaults=dict(
            date=semaine_prochaine, location="Atelier B",
            description="Apprendre à souder proprement ses premiers montages", course=cours2))
        if created2:
            SessionEquipment.objects.create(session=session2, equipment=fer, quantity_reserved=6)
            SessionEquipment.objects.create(session=session2, equipment=multimetre, quantity_reserved=4)

        self.stdout.write(self.style.SUCCESS("Base de démonstration prête."))
        self.stdout.write("Mot de passe pour tous les comptes : Demo1234!")
        self.stdout.write("  0001 - Admin Club (ADMIN)")
        self.stdout.write("  0002 - Camille Staff (STAFF)")
        self.stdout.write("  0003 - Jean Membre (MEMBER, déjà approuvé)")
        self.stdout.write("  0004 - Alex Nouveau (MEMBER, EN ATTENTE — à approuver pendant la démo)")
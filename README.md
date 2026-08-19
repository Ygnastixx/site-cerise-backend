# 🚀 Platform Backend API — Architecture Multi-Modules

API REST développée avec **Django** et **Django REST Framework**.

---

## 📌 1. Prérequis

* **Python 3.10+**
* **Git**
* **VS Code** (recommandé)

---

## 🛠️ 2. Guide d'installation rapide

```bash
# 1. Cloner le projet
git clone https://github.com/Ygnastixx/site-cerise-backend.git
cd site-cerise-backend

# 2. Créer et activer l'environnement virtuel
python -m venv venv
# Windows : .\venv\Scripts\Activate.ps1 dans powershell ou venv\scripts\activate dans cmd
# macOS/Linux : source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
# Windows : copy .env.example .env
# macOS/Linux : cp .env.example .env

# 5. Appliquer les migrations & Lancer le serveur
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 🧩 3. Organisation des Modules (Applications Django)
Le projet est découpé en 5 applications indépendantes :

* **users/** : Authentification, rôles (Admin/Staff/Membre) et validation des inscriptions.

* **courses/** : Gestion des cours (brouillon, publié, corbeille, modèles) et des sections hiérarchiques.

* **sessions_app/** : Planning des séances du club et association aux cours/sections.

* **inventory/** : Inventaire du matériel du club et suivi des quantités réservées par séance.

* **studio/** : Génération de texte pour réseaux via IA et transformation des cours en slides JSON.

---

##  📁 4. Arborescence du projet

```bash
backend-api/
├── manage.py
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── config/                 # Projet global (settings, urls racine)
│   ├── settings.py
│   └── urls.py
├── users/                  # App 1: Authentification & Validation Admin
│   ├── models.py           # User sur-mesure (role, is_approved)
│   ├── views.py
│   └── urls.py
├── courses/                # App 2: Cours & Sections (Arbre)
│   ├── models.py           # Course, Section
│   ├── views.py
│   └── urls.py
├── sessions_app/           # App 3: Séances & Liens avec les cours
│   ├── models.py           # Session, SessionSection
│   ├── views.py
│   └── urls.py
├── inventory/              # App 4: Gestion du Matériel du club
│   ├── models.py           # Equipment, SessionEquipment
│   ├── views.py
│   └── urls.py
└── studio/                 # App 5: Génération IA, affiches & Slides / Templates
    ├── models.py           # SlideTemplate
    ├── views.py            # API IA & Génération JSON
    ├── urls.py
    └── presentation/       # Moteur de conversion Cours -> Slides
        ├── builder.py
        ├── models.py
        └── rules.py

```
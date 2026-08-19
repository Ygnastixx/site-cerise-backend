## 🛠️ Guide de Contribution & Workflow de Développement

### 1. Gestion des Branches Git

Afin de garder la branche `main` stable, **ne dévloppez jamais directement sur `main`**. Chaque membre de l'équipe doit créer une branche dédiée à sa fonctionnalité.

#### Procédure pour chaque nouvelle tâche :
1. Assurez-vous d'être à jour sur `main` :
   ```bash
   git checkout main
   git pull origin main

   ```

2. Créez et basculez sur votre branche de fonctionnalité (nommage conseillé : `feature/nom-du-module` ou `fix/nom-du-bug`) :
   ```bash
   git checkout -b feature/gestion-cours

   ```


3. Publiez votre branche sur le dépôt distant lors du premier push :
   ```bash
   git push -u origin feature/gestion-cours

   ```


4. Une fois votre fonctionnalité terminée et testée, créez une **Pull Request (PR)** sur GitHub vers `main`.

---

### 2. Boucle de Développement Django (Workflow standard)

Lorsque vous travaillez sur votre application attribuée, suivez systématiquement cet ordre pour construire vos fonctionnalités API :

```text
Modèle (models.py) ──> Migration ──> Sérialiseur (serializers.py) ──> Vue (views.py) ──> URL (urls.py) ──> Test & Commit

```

#### Étape par étape :

1. **Définir le Modèle (`models.py`)** : Créez ou modifiez les classes de données dans votre application.
2. **Générer et appliquer la migration** :
```bash
python manage.py makemigrations
python manage.py migrate

```


3. **Créer le Sérialiseur (`serializers.py`)** : Transformez vos modèles en JSON (utilisez `ModelSerializer` de Django REST Framework).
4. **Écrire la Vue (`views.py`)** : Implémentez la logique métier et les permissions (`APIView`, `ModelViewSet`, etc.).
5. **Brancher la route (`urls.py`)** : Déclarez l'endpoint dans le `urls.py` de votre module.
6. **Commiter à chaque étape clé** : Faites des commits atomiques et explicites :
```bash
git add .
git commit -m "feat(courses): ajout du modele Course et des migrations"
git push

```



---

### 3. Exécution et Écriture des Tests

Avant chaque `git push` ou ouverture de Pull Request, assurez-vous que l'ensemble de la suite de tests passe sans erreur.

#### Lancer les tests :

* **Exécuter tous les tests du projet :**
```bash
python manage.py test

```


* **Exécuter uniquement les tests de votre application :**
```bash
python manage.py test courses

```


* **Exécuter une classe de test spécifique :**
```bash
python manage.py test courses.tests.CourseAPITestCase

```



#### Bonne pratique pour rédiger un test (`tests.py`) :

Chaque module doit avoir des tests automatisés vérifiant au minimum :

* La création/lecture des modèles.
* L'accès aux endpoints avec et sans Token JWT (`APITestCase`). Consulter `\courses\tests.py` pour voir un exemple.
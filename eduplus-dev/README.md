# EduPlus - Plateforme d'Apprentissage en Ligne

EduPlus est une plateforme d'apprentissage en ligne complète construite avec Django, permettant aux instructeurs de créer et vendre des cours en ligne, et aux étudiants de s'inscrire et suivre ces cours.

## Fonctionnalités

- **Gestion des utilisateurs** : Inscription, connexion, profils personnalisés
- **Catalogue de cours** : Parcourir et rechercher des cours par catégorie
- **Création de cours** : Interface pour les instructeurs avec modules, contenu multimédia
- **Paiements sécurisés** : Intégration avec Stripe pour les transactions
- **Tableau de bord étudiant** : Suivi de progression, certificats
- **Système de notation** : Évaluations et avis sur les cours
- **Coupons de réduction** : Promotions et réductions sur les cours

## Prérequis

- Python 3.8+
- pip (gestionnaire de paquets Python)
- Compte Stripe (pour les paiements)

## Installation

1. Clonez le dépôt :
```bash
git clone https://gitlab.com/devloppements/eduplus.git
cd eduplus
```

2. Créez et activez un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Créez un fichier `.env` à la racine du projet (voir `.env.example` pour la structure)

5. Appliquez les migrations :
```bash
python manage.py migrate
```

6. Créez un superutilisateur :
```bash
python manage.py createsuperuser
```

7. Lancez le serveur de développement :
```bashexit()
python manage.py runserver
```

## Configuration de l'environnement

Créez un fichier `.env` à la racine du projet en vous basant sur le fichier `.env.example` :

```bash
cp .env.example .env
```

Les valeurs par défaut sont configurées pour le développement:

```
# Configuration pour le développement
SECRET_KEY=django-insecure-dev-only-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3

# Configuration Stripe - Utilisez vos clés de test Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

> **Note**: Le fichier `.env.example` contient également des configurations commentées pour la production que vous pourrez utiliser lors du déploiement.

## Données de test

Pour peupler la base de données avec des données de test :

```bash
python populate_test_data.py
```

## Déploiement en production

Pour un déploiement en production sécurisé, assurez-vous de :

1. Définir `DEBUG=False` dans vos variables d'environnement
2. Configurer une base de données PostgreSQL
3. Configurer les paramètres de sécurité dans votre fichier `.env` :
   ```
   SECURE_HSTS_SECONDS=31536000
   SECURE_HSTS_INCLUDE_SUBDOMAINS=True
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```
4. Configurer un serveur web comme Nginx ou Apache avec Gunicorn/uWSGI
5. Utiliser des certificats SSL

## Structure du projet

- **courses/** : Gestion des cours et du contenu pédagogique
- **users/** : Authentification et gestion des utilisateurs
- **payments/** : Transactions et facturation
- **dashboard/** : Tableaux de bord étudiants et instructeurs
- **templates/** : Templates HTML
- **static/** : Fichiers statiques (CSS, JS, images)
- **media/** : Fichiers téléchargés par les utilisateurs

## Contribuer

1. Forker le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Valider les modifications (`git commit -m 'Add some amazing feature'`)
4. Pousser vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Merge Request

## Licence

Ce projet est la propriété de EduPlus. Tous droits réservés.

## Contact

Pour toute question, veuillez contacter l'équipe de développement à dev@eduplus.fr

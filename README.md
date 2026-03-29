# Payment Platform — Backend API

Backend Django REST Framework pour la plateforme de gestion des paiements et wallets internes.

\---

## Stack

|Composant|Technologie|
|-|-|
|Backend|Django 5 + DRF|
|Auth|JWT (SimpleJWT)|
|Base de données|PostgreSQL|
|Permissions|Rôles : Admin / Commerçant|

\---

## Installation rapide

```bash
# Cloner et entrer dans le projet
git clone <repo> \&\& cd backend

# Setup automatique (venv + dépendances + DB + migrations + fixtures)
bash setup.sh
```

### Manuel (étape par étape)

```bash
python -m venv venv
source venv/bin/activate          # Windows : venv\\Scripts\\activate
pip install -r requirements.txt

cp .env.example .env              # remplir les valeurs

python manage.py makemigrations
python manage.py migrate
python manage.py loaddata apps/abonnements/fixtures/plans.json
python manage.py createsuperuser
python manage.py runserver
```

\---

## Variables d'environnement (.env)

```env
SECRET\_KEY=your-secret-key
DEBUG=True
DB\_NAME=payment\_platform
DB\_USER=postgres
DB\_PASSWORD=yourpassword
DB\_HOST=localhost
DB\_PORT=5432
ALLOWED\_HOSTS=localhost,127.0.0.1
CORS\_ORIGINS=http://localhost:3000
```

\---

## Endpoints API

Base URL : `http://localhost:8000/api/v1/`

### 🔐 Authentification

|Méthode|Endpoint|Description|Auth|
|-|-|-|-|
|POST|`auth/register/`|Créer un compte|❌|
|POST|`auth/login/`|Connexion → tokens JWT|❌|
|POST|`auth/logout/`|Invalider le refresh token|✅|
|POST|`auth/token/refresh/`|Rafraîchir l'access token|❌|
|GET|`auth/me/`|Profil connecté|✅|
|PATCH|`auth/me/`|Modifier profil|✅|
|POST|`auth/change-password/`|Changer mot de passe|✅|
|GET|`auth/users/`|Liste commerçants (admin)|🔑|
|GET/PUT|`auth/users/<id>/`|Détail commerçant (admin)|🔑|

### 💳 Wallet

|Méthode|Endpoint|Description|Auth|
|-|-|-|-|
|GET|`wallets/me/`|Mon wallet + solde|✅|
|POST|`wallets/charger/`|Charger le wallet|✅|
|GET|`wallets/all/`|Tous les wallets (admin)|🔑|

### 💸 Transactions

|Méthode|Endpoint|Description|Auth|
|-|-|-|-|
|GET|`transactions/`|Historique (filtrable)|✅|
|GET|`transactions/<id>/`|Détail transaction|✅|
|POST|`transactions/transfert/`|Transfert interne (gratuit)|✅|
|POST|`transactions/<id>/annuler/`|Annuler une transaction|✅|
|GET|`transactions/dashboard/`|Dashboard financier|✅|
|GET|`transactions/admin/all/`|Toutes les transactions|🔑|

### 🏦 Comptes Externes

|Méthode|Endpoint|Description|Auth|
|-|-|-|-|
|GET|`comptes/`|Mes comptes externes|✅|
|POST|`comptes/`|Lier un compte|✅|
|GET|`comptes/<id>/`|Détail compte|✅|
|PATCH|`comptes/<id>/`|Modifier compte|✅|
|DELETE|`comptes/<id>/`|Délier compte|✅|
|GET|`comptes/<id>/paiements/`|Paiements entrants|✅|

### 📦 Abonnements

|Méthode|Endpoint|Description|Auth|
|-|-|-|-|
|GET|`abonnements/plans/`|Plans disponibles|✅|
|GET|`abonnements/me/`|Mon abonnement|✅|
|POST|`abonnements/souscrire/`|Souscrire / changer de plan|✅|
|POST|`abonnements/resilier/`|Résilier|✅|
|POST|`abonnements/renouveler/`|Renouveler manuellement|✅|
|GET|`abonnements/all/`|Tous les abonnements (admin)|🔑|

> ✅ = JWT requis · 🔑 = JWT Admin requis · ❌ = Public

\---

## Structure du projet

```
backend/
├── manage.py
├── requirements.txt
├── setup.sh
├── .env.example
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/
│   ├── models.py        # TimeStampedModel
│   ├── permissions.py   # IsAdmin, IsCommerçant, IsOwnerOrAdmin
│   ├── pagination.py    # StandardPagination
│   ├── exceptions.py    # custom\_exception\_handler
│   └── utils.py         # generate\_reference, success\_response
└── apps/
    ├── users/           # Auth JWT + gestion utilisateurs
    ├── wallets/         # Wallet + chargement
    ├── transactions/    # Transferts + dashboard
    ├── comptes/         # Comptes bancaires externes
    └── abonnements/     # Plans + abonnements
```

\---

## Format des réponses

Toutes les réponses suivent ce format uniforme :

```json
{
  "success": true,
  "message": "Opération réussie.",
  "data": { ... }
}
```

Erreurs :

```json
{
  "success": false,
  "status": 400,
  "errors": { "field": \["message d'erreur"] }
}
```

\---

## Exemple — Transfert interne

```http
POST /api/v1/transactions/transfert/
Authorization: Bearer <access\_token>
Content-Type: application/json

{
  "email\_recepteur": "autre@commercant.com",
  "montant": 5000,
  "description": "Règlement facture #42"
}
```

Réponse :

```json
{
  "success": true,
  "message": "Transfert effectué avec succès. Frais : 0 MRU",
  "data": {
    "id": 12,
    "reference": "A3F9D12C4B7E1098",
    "type": "interne",
    "statut": "success",
    "montant": "5000.00",
    "frais": "0.00",
    ...
  }
}
```

\---

## Plans d'abonnement

|Plan|Prix/mois|Comptes externes max|
|-|-|-|
|Gratuit|0 MRU|1|
|Basic|990 MRU|3|
|Pro|2 490 MRU|10|
|Enterprise|7 990 MRU|Illimité|

> Toutes les transactions \*\*internes\*\* entre commerçants sont \*\*gratuites\*\* (frais = 0).


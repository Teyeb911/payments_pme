# TrackPay Interop API - RSS Bank

Cette documentation explique comment RSS Bank peut envoyer un transfert vers un utilisateur TrackPay.

## Base URL

Production:

```txt
https://config-ap28-1mhk.onrender.com
```

## Authentification

Chaque requete doit contenir le header:

```txt
X-Partner-Key: sk_interop_xxx
```

La cle partenaire est fournie separement par TrackPay. Elle doit rester cote serveur RSS Bank et ne doit jamais etre exposee dans une application mobile ou web publique.

## 1. Verifier un utilisateur TrackPay

Permet de verifier si un email existe chez TrackPay avant d'envoyer un transfert.

```txt
GET /api/interop/verify-user/?email=user@example.com
```

Exemple:

```bash
curl -X GET \
  "https://config-ap28-1mhk.onrender.com/api/interop/verify-user/?email=user@example.com" \
  -H "X-Partner-Key: sk_interop_xxx"
```

Reponse si l'utilisateur existe:

```json
{
  "exists": true,
  "name": "Nom utilisateur",
  "email": "user@example.com"
}
```

Reponse si l'utilisateur n'existe pas:

```json
{
  "exists": false,
  "error": "Aucun compte TrackPay trouve avec cet email."
}
```

## 2. Envoyer un transfert vers TrackPay

Credite le wallet TrackPay du destinataire.

```txt
POST /api/interop/receive/
```

Headers:

```txt
Content-Type: application/json
X-Partner-Key: sk_interop_xxx
```

Body:

```json
{
  "email": "user@example.com",
  "amount": 500,
  "sender": "Ahmed - RSS Bank",
  "reference": "TXN_RSS_123"
}
```

Exemple:

```bash
curl -X POST \
  "https://config-ap28-1mhk.onrender.com/api/interop/receive/" \
  -H "Content-Type: application/json" \
  -H "X-Partner-Key: sk_interop_xxx" \
  -d "{\"email\":\"user@example.com\",\"amount\":500,\"sender\":\"Ahmed - RSS Bank\",\"reference\":\"TXN_RSS_123\"}"
```

Reponse en succes:

```json
{
  "status": "SUCCESS",
  "receiver": "Nom utilisateur",
  "email": "user@example.com",
  "amount": "500",
  "reference": "TXN_RSS_123"
}
```

## Regles importantes

- `reference` doit etre unique pour chaque transfert.
- `amount` doit etre superieur a `0`.
- Le transfert est traite de maniere atomique: le wallet est credite et l'historique est cree dans la meme operation.
- Dans l'historique TrackPay, le type de transaction est `interop_received`.
- La reference affichee dans TrackPay est la reference envoyee par RSS Bank.

## Erreurs possibles

Cle partenaire invalide:

```json
{
  "error": "Cle partenaire invalide ou inactive."
}
```

Email manquant:

```json
{
  "error": "Parametre email requis."
}
```

Champs manquants:

```json
{
  "error": "Champs manquants: email, amount, sender, reference"
}
```

Reference deja utilisee:

```json
{
  "error": "Reference deja utilisee."
}
```

Utilisateur introuvable:

```json
{
  "error": "Aucun compte TrackPay trouve avec cet email."
}
```

Montant invalide:

```json
{
  "error": "Montant invalide."
}
```

Erreur serveur:

```json
{
  "status": "FAILED",
  "error": "Erreur lors du traitement."
}
```

## Checklist avant production

1. Deployer le backend TrackPay.
2. Appliquer les migrations:

```bash
python manage.py migrate
```

3. Creer ou verifier le partenaire `RSS Bank` dans Django Admin.
4. Verifier que `is_active = true`.
5. Envoyer la cle `X-Partner-Key` a RSS Bank par canal securise.
6. Faire un test avec une petite somme et une reference unique.

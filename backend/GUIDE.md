# StageX-Marrakech — Guide d'installation de l'import d'offres

Aucun fichier existant n'est modifié : `app.py`, `offres_sources.py`, le frontend et la table `offres` restent tels quels. Vous **créez** 6 nouveaux fichiers.

## Étape 1 — Créer les fichiers

Dans `C:\Users\de\OneDrive\Documents\StageX-Marrakech\backend\`, créez ces fichiers (nouveau fichier → collez le contenu complet → enregistrez en UTF-8) :

| Fichier | Rôle |
|---|---|
| `backend\stagex_regles.py` | Règles : stage, Marrakech, 5 domaines, durée, « Non précisé » |
| `backend\stagex_db.py` | File d'attente SQLite + publication dans `offres` |
| `backend\verifier_url.py` | Contrôle honnête des liens (une requête, aucun contournement) |
| `backend\source_claude.py` | Claude API : recherche web + extraction |
| `backend\source_jooble.py` | API officielle Jooble |
| `backend\importer_offres.py` | Commande principale |

À la racine du projet : copiez `env.example` sous le nom **`.env`**.

## Étape 2 — Installer et tester (sans clé, sans Internet)

```powershell
cd C:\Users\de\OneDrive\Documents\StageX-Marrakech
.\venv\Scripts\Activate.ps1
pip install requests anthropic
python backend\importer_offres.py test-regles
```

Résultat attendu, dernière ligne : `TOUS LES TESTS PASSENT`.

**Sauvegarde de la base avant toute importation :**

```powershell
Copy-Item database\stagex.db database\stagex_sauvegarde.db
```

## Étape 3 — Indeed (méthode propre : vous lisez, Claude structure)

1. Sur Indeed, dans votre navigateur, ouvrez une offre de stage à Marrakech.
2. Créez `data\offres_manuelles\indeed_001.txt` :
   - ligne 1 : l'URL de l'offre (barre d'adresse)
   - à partir de la ligne 2 : collez tout le texte de l'offre (Ctrl+A, Ctrl+C sur la page)
3. Lancez :

```powershell
python backend\importer_offres.py manuel
python backend\importer_offres.py valider
```

`valider` rouvre chaque lien : tapez `o` seulement si la page montre bien cette offre.

**Sans clé Claude**, créez plutôt un `.json` dans le même dossier :

```json
{
  "titre": "Titre exact de l'offre",
  "entreprise_source": "Nom exact",
  "ville": "Marrakech",
  "description": "Résumé fidèle",
  "profil": "Compétences demandées",
  "date_publication": null,
  "url_source": "https://ma.indeed.com/...",
  "url_candidature": null,
  "duree": null
}
```

`null` devient automatiquement « Non précisé ».

## Étape 4 — Claude API (recherche automatique)

1. Créez un compte sur https://platform.claude.com, ajoutez un moyen de paiement, créez une clé.
2. Collez-la dans `.env` : `ANTHROPIC_API_KEY=sk-ant-...`
3. Testez sur un seul domaine d'abord :

```powershell
python backend\importer_offres.py claude --domaine "Data Analyst"
python backend\importer_offres.py liste
```

Lignes possibles :
- `[EN ATTENTE] ... | ok: HTTP 200, titre retrouvé...` → lien confirmé automatiquement
- `[EN ATTENTE] ... | bloque: HTTP 403` → site qui refuse les robots (Indeed, LinkedIn) : à valider vous-même
- `[IGNORÉE] URL absente des résultats réels` → Claude a proposé une URL qui ne sort pas de ses recherches : écartée
- `[REJET] ... -> Marrakech non mentionnée` → règles StageX non respectées

4. Puis tout :

```powershell
python backend\importer_offres.py claude
python backend\importer_offres.py publier-auto
python backend\importer_offres.py valider
```

## Étape 5 — Jooble (facultatif)

Demandez une clé sur https://jooble.org/api/about, collez-la dans `.env`, puis :

```powershell
python backend\importer_offres.py jooble
python backend\importer_offres.py valider
```

## Étape 6 — Vérifier sur le site

```powershell
python backend\app.py
```

Ouvrez http://127.0.0.1:5000/api/offres puis la page `offres.html`.

**Vérifiez** que les valeurs de `domaine` (ex. `Développement`) et `type` (`Stage` / `PFE`) correspondent bien aux options des filtres de `offres.html`. Si vos filtres utilisent d'autres libellés, dites-le-moi et j'adapterai.

## Entretien (une fois par semaine)

```powershell
python backend\importer_offres.py reverifier
```

Retire du site les offres dont le lien renvoie 404/410. Les offres Indeed (403) ne peuvent pas être revérifiées automatiquement : repassez-les à la main.

## Retour arrière

Les nouvelles tables (`offres_candidates`, `offres_verification`) n'affectent pas l'API. Pour tout annuler :

```powershell
Copy-Item database\stagex_sauvegarde.db database\stagex.db -Force
```

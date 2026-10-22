# Multi News V2

Portail d'actualités international multilingue, sans compte utilisateur et sans tracking. Le site affiche des titres et liens vers les médias d'origine.

## Architecture
- `site/` : site statique responsive, accessible sans build Node.
- `scripts/collect.py` : collecte RSS et normalisation JSON.
- `.github/workflows/pages.yml` : publication GitHub Pages et rafraîchissement programmé.

## Publication
Dans **Settings → Pages → Build and deployment → Source**, choisir **GitHub Actions**. Le workflow `Publish Multi News` peut ensuite être lancé manuellement dans l'onglet Actions.

URL attendue : https://adelovitch.github.io/multi-news-v2/

## Vérification locale
```bash
python scripts/collect.py
cp -r data site/data
python -m http.server 8000 -d site
```
Ouvrir http://localhost:8000. Aucun compte ni clé API nécessaires.

**Limites :** la collecte RSS dépend de la disponibilité des éditeurs ; le planificateur Actions ne garantit pas une mise à jour exacte à l'heure. Le filtre porte sur la langue des sources, et ne traduit pas les articles. Si toutes les sources échouent, le workflow échoue pour éviter de publier un flux vide.

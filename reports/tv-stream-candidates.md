# Multi News TV — candidats pour lecteurs intégrables (23 octobre 2026)

## Méthode
La lecture d'une vidéo HLS sur Firefox a été confirmée par le test Mux/Big Buck Bunny. Pour une chaîne tierce, tester séparément la provenance officielle du diffuseur, sa possibilité d'intégration, la disponibilité du direct, la géolocalisation et la lecture réelle sur GitHub Pages. Une URL accessible n'est pas une licence de redistribution.

| Candidat | Type | Documentation / provenance | Décision |
| --- | --- | --- | --- |
| NASA sur Twitch | Diffusions officielles événementielles, pas une chaîne d'information 24h/24 | https://www.nasa.gov/news-release/nasa-goes-live-first-twitch-stream-from-space-station/ et https://dev.twitch.tv/docs/embed/ | Test dans le laboratoire avec le lecteur officiel Twitch, parent=adelovitch.github.io, muet et sans lecture automatique; disponibilité non garantie |
| ARTE | Chaîne TV culturelle, direct et vidéos | https://corporate.arte.tv/fr/conditions-generales-dutilisation-cgu/ | Seulement avec le code généré par le lecteur « Intégrer » pour un contenu autorisé; ne pas construire d'iframe libre vers le direct |
| Deutsche Welle | Actualités TV | https://corporate.dw.com/de/livestream/a-2514651 | Lien direct officiel seulement. Autorisation d'intégration non établie |
| France 24 | Actualités TV | https://www.france24.com/fr/direct | Lien direct officiel seulement. Lien HLS trouvé dans des index tiers insuffisant pour les droits d'intégration |
| TV5MONDE Europe | Chaîne généraliste | Test HLS externe : networkError / manifestLoadError sur Firefox | Échec technique, autorisation d'intégration non confirmée |
| franceinfo sur YouTube | Actualités TV | https://www.youtube.com/franceinfo/live | Les deux variantes d'iframe ont échoué dans le navigateur de test; ne pas annoncer de lecture directe |
| Mux Big Buck Bunny | Vidéo HLS de démonstration, pas un direct | https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8 | Lecture HTML5/HLS.js confirmée par l'utilisateur |

Le laboratoire `site/tv/lab/` est volontairement isolé. Un lecteur officiel qui charge mais affiche « hors ligne » ne prouve pas la présence d'un direct actif. Aucun candidat TV 24h/24 ne peut être annoncé comme pleinement validé aujourd'hui.

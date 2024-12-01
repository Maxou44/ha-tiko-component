# Tiko
Composant personnalisé pour Home Assistant permettant d'interagir avec les radiateurs connectés via Tiko, que ce soit via Tiko.fr ou Tiko.ch.

## Introduction
J'ai développé cette intégration car toutes les solutions existantes pour Tiko nécessitaient un composant additionnel en NodeJS ou en PHP pour gérer la communication avec l'API de Tiko.

Ce module est développé directement en tant que composant Home Assistant, offrant ainsi une intégration optimale et une configuration via l'interface utilisateur. Il inclut également un polling "intelligent" pour les mettre à jour rapidement après un changement d'état.

Les requêtes GraphQL ont été optimisées pour ne solliciter que les données strictement nécessaires auprès de Tiko, améliorant ainsi les performances et réduisant l'impact réseau.

## Configuration
Une fois avoir ajouté le module "tiko" dans votre dossier "custom_components" et redémarré Home Assistant, vous devriez pouvoir l'installer directement depuis le bouton "Ajouter une intégration".

Quand le module sera stable, j'ajouterai l'installation avec HACS, n'hésitez pas à faire des retours en attendant.

## Considérations
Les données sont récupérées toutes les 30 secondes auprès de l'API de Tiko. Elles sont également récupérées immédiatement à chaque changement d'état dans Home Assistant, garantissant ainsi une meilleure précision.

Gardez à l'esprit que la détection de la chauffe n'est pas instantanée, même avec l'application officielle, il y a donc un délai lorsque vous augmentez le chauffage et le moment où le radiateur se déclenche.

Il est possible de conserver la planification de ses radiateurs sur l'application Tiko. Mais pour une utilisation optimale, il est recommandé de la désactiver car elle pourrait venir écraser vos automatisations Home Assistant.

## Entitées et capteurs
Pour chaque pièce disponible dans Tiko, le module créera :
- Un capteur "Current temperature" pour la température actuelle.
- Un capteur "Target temperature" pour la température cible.
- Un capteur "Current humidity" pour l'humidité actuelle.
- Un capteur binaire "Battery" pour indiquer le niveau de batterie faible du capteur de température.
- Un capteur "Energy Consumption" Pour mesurer la consommation électrique
- Une entité thermostat pour la gestion du chauffage.

### L'entitée thermostat

Une entitée de type thermostat est mise à disposition pour chacun des radiateurs, vous permettant de contrôler la température et de définir les différents "presets" disponibles. Chaque radiateur est désactivable indépendament, l'API de Tiko ne gérant pas cette fonctionnalité directement, une température de 0 degré sera configurée, ce qui désactive le radiateur.

L'entité prend en charge les presets suivants :
- **Eco** : Correspond au mode "Hors gel" et fixe la température à 7°C.
- **Away** : Correspond au mode "Absence" et fixe la température à 17°C.
- **Boost** : Correspond au mode "Boost" et fixe la température à 25°C.

_Notez qu'en définissant la température à 0, il ne sera plus possible de modifier la température depuis les interfaces Tiko. Pour la réactiver et la modifier à nouveau, il faudra activer un mode. Il s'agit d'un bug de leur application/interface web._

## Remerciements
Merci à @paulchartres, @noiwid, @BenoitAnastay, et @marvinroger pour leurs différentes recherches ayant permis le reverse engineering des API de Tiko.
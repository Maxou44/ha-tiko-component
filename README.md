# Tiko
Composant personnalisé pour Home Assistant permettant d'interagir avec les radiateurs connectés via Tiko, que ce soit via Tiko.fr ou Tiko.ch.

## Introduction
J'ai développé cette intégration car toutes les solutions existantes pour Tiko nécessitaient un composant additionnel en NodeJS ou en PHP pour gérer la communication avec l'API de Tiko.

Ce module est développé directement en tant que composant Home Assistant, offrant ainsi une intégration optimale et une configuration via l'interface utilisateur. Les requêtes GraphQL ont été optimisées pour ne solliciter que les données strictement nécessaires auprès de Tiko, améliorant ainsi les performances et réduisant l'impact réseau.

## Installation dans Home Assistant

#### Avec HACS

[![Ouvre votre instance Home Assistant et ajoute un dépôt dans la boutique communautaire Home Assistant.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=maxou44&repository=ha-tiko-component&category=integration)

Plus d'informations sur HACS [ici](https://hacs.xyz/).

#### Manuellement

Téléchargez l'[intégration Tiko](https://github.com/Maxou44/ha-tiko-component/archive/refs/heads/master.zip) et décompressez le dossier `custom_components/tiko` dans le dossier de configuration de Home Assistant. Ensuite, redémarrez votre Home Assistant.

## Configuration

Une fois le composant installé, rendez vous dans Paramètres > Appareils et services > Ajouter une intégration, puis sélectionnez Tiko, vous serez ensuite invités à rentrer votre email et votre mot de passe.

## Considérations
Les données sont récupérées toutes les 30 secondes auprès de l'API de Tiko. Elles sont également récupérées immédiatement à chaque changement d'état dans Home Assistant, garantissant ainsi une meilleure précision.

La consommation électrique est récupérée toutes les 5 minutes via l'API mais la donnée n'est mise à jour que toutes les 15 minutes de leur côté, il n'y a pas de temps réel.

Gardez à l'esprit que la détection de la chauffe n'est pas instantanée, même avec l'application officielle, il y a donc un délai lorsque vous augmentez le chauffage et le moment où le radiateur se déclenche.

Il est possible de conserver la planification de ses radiateurs sur l'application Tiko. Mais pour une utilisation optimale, il est recommandé de la désactiver car elle pourrait venir écraser vos automatisations Home Assistant.

## Entitées et capteurs
Pour chaque pièce disponible dans Tiko, le module créera :
- Un capteur "Current temperature" pour la température actuelle.
- Un capteur "Target temperature" pour la température cible.
- Un capteur "Current humidity" pour l'humidité actuelle.
- Un capteur "Energy Consumption" pour mesurer la consommation électrique
- Un capteur binaire "Battery" pour indiquer le niveau de batterie faible du capteur de température.
- Une entité thermostat pour la gestion du chauffage.

### L'entitée thermostat

Une entitée de type thermostat est mise à disposition pour chacun des radiateurs, vous permettant de contrôler la température et de définir les différents "presets" disponibles.

L'entité prend en charge les presets suivants :
- **Confort** 
- **Eco**
- **Nuit** : Correspond au mode "Sommeil"
- **Hors-Gel**

## Remerciements
Merci à @paulchartres, @noiwid, @BenoitAnastay, et @marvinroger pour leurs différentes recherches ayant permis le reverse engineering des API de Tiko.

<h1 style="text-align: center;"> Modifications apportées, problèmes rencontrés</h1>
<h2>Disclaimer</h2>
Ce projet a pour but de corriger et de reprendre les travaux de Valérie Zermatten afin de les adapter au nouveau jeu de données FLAIR-HUB de l'IGN. Les modifications sont classées par types de modification et/ou problèmes rencontrés au fur et à mesure.

Vous trouverez ci-dessous la liste des modifications apportées au dépot git original [RS-OVSS](https://github.com/eceo-epfl/RS-OVSS). Pour plus d'information sur l'original, se référer au README dans le dossier documentation.

<h2>Données ajoutées</h2>
<h3>Données FLAIR-HUB</h3>
Les deux csv FLAIR et FLAIR-HUB possédant des formats différents nous avons adapté le code en conséquence dans la classe FLAIRDataset du fichier dataset.py:

- ajout de la ligne 29 dans la fonction \_\_init__
- ajouts et modifications des lignes 96 à 100 dans la fonction \_\_getitem__

(les tests ont pour l'instant été éffectué sur les données FLAIR-HUB TOY)

Les données sont à télécharger sur [cette page](https://ignf.github.io/FLAIR/FLAIR-HUB/flairhub_fr.html).

<h2>Chemins</h2>
Les chemins sont à changer dans le fichier default.py.
Si utilisation de CLIPSeg, il faut aussi changer les chemins dans ce répertoire-là

<h2>Problèmes de drivers</h2>
Afin de régler ce problème, il suffit de modifier dans default.py la ligne 79

<h2>Problèmes de CPU avec Torch</h2>
Pour assurer la compatibilité du code avec des environnement "cpu-only", quelques modifications ont été apportés dans les fichiers suivants:

- main.py : ligne 263 
- SegformerModel.py : lignes 9 et 36
- DeepLabv3pModel.py : lignes 9 et 109 


<h2>Problèmes de fichiers innexistants</h2>
De nombreux fichiers ne semblaient pas coincider avec les noms des fichiers lu dans le code: voici une liste des modifications de noms de fichiers apportés:

- ajout des fichiers dlv-bcos_clip_des.yaml, dlv-bcos_clip_name.yaml et dlv-bcos_clip_syn.yaml afin de pouvoir effectuer les tests proposés dans le README.md du projet initial.
- certains noms de fichiers ne correspondent également pas à ceux appelés dans des fichiers ou aux commandes partagées dans le readme. Les bonnes commandes sont les suivantes:

```
# Train Segformer baseline model :
python3 main.py --cfg segformer-base

# Train DeepLabv3+ baseline model :
python3 main.py --cfg dlv-base

# Train TACOSS with the SegFormer visual backbone and the SentenceBERT text encoder : 
python3 main.py --cfg segformer_bcos_sbert_des_eda 

# Train TACOSS with the DeepLabv3+ backbone and CLIP text encoder :
python3 main.py --cfg dlv-bcos_clip_name

```
<h2>Tests sans entraînement</h2>
Pour lancer des tests sans entraînement, une fonction config a été ajouté au fichier main.py

<h2>Rappels utiles</h2>
<h3>Commandes</h3>
Il est possible de choisir soit même les configurations que l'on souhaite tester et entrainer avec la commande:

```
python main.py --cfg <config_name>
```


<h3>Lancement du projet</h3>
Il est possible de lancer les tests sans anaconda ni docker (bien que l'utilisation de l'un des deux soit conseillée). Pour cela, une commande bash a été ajouté pour l'import des librairies python : req.sh


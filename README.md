
# 🗂️ Convertisseur & Archiveur PDF (Tkinter/MVC)

## Description du Projet

Ce projet est une application de bureau simple (GUI) développée en Python (Tkinter) qui permet aux utilisateurs d'importer une liste de documents bureautiques modifiables (DOC, DOCX, ODT), de **modifier leur nom final**, de les **convertir automatiquement en PDF**, puis de les compresser dans une unique **archive ZIP**.

L'application utilise l'outil externe **LibreOffice/OpenOffice (`soffice`)** pour effectuer la conversion, garantissant une haute fidélité du rendu PDF.

## ✨ Fonctionnalités Clés

  * **Gestion des Noms :** Permet d'éditer le nom de chaque fichier exporté via un double-clic dans la liste.
  * **Conversion Robuste :** Conversion PDF via `soffice` (LibreOffice/OpenOffice).
  * **Gestion des Doublons :** Logique avancée pour gérer les conflits de noms après conversion (`rapport.pdf`, `rapport_1.pdf`).
  * **Exportation Asynchrone :** L'exportation et la conversion sont exécutées dans un thread séparé pour éviter le blocage (*freeze*) de l'interface utilisateur.
  * **Architecture MVC :** Le code est structuré selon le Modèle-Vue-Contrôleur pour une maintenance et une évolution facilitées.

-----

## 👥 Contributions au Projet

### 👩 Développeur Initial

Contribution résidant dans l'**initiative**, la **conception initiale de l'interface** et l'**établissement du squelette fonctionnel** de l'application.

| Catégorie | Description de la contribution |
| :--- | :--- |
| **Squelette de l'Application** | 🎯 **Conception et Initialisation du Projet :** Décider de la nature du projet (outil de conversion et d'archivage). |
| | 🖼️ **Conception de l'Interface (GUI) :** Création de la classe `Application(tk.Frame)` et de la méthode `graphical_user_interface`. |
| | 🌳 **Structure du Treeview :** Définition des colonnes (ID, Nom, Extension) et ajout du `Treeview` à l'interface. |
| **Fonctionnalités de Base** | ➕ **Mécanisme d'Importation :** Utilisation de `filedialog.askopenfiles` pour sélectionner des documents. |
| | 🔗 **Structure de Données Initiale :** Utilisation et initialisation des dictionnaires (`file_path_dict`, `file_element_dict`) et du compteur (`self.counter`). |
| | 📝 **Affichage de la Liste :** Implémentation de la fonction `feed_treeview` pour peupler la liste. |
| **Logique de Base** | 📞 **Appel à soffice :** Définition de la méthode `export` de base, qui appelle l'outil externe (`subprocess.run`) pour la conversion PDF. |
| | 📦 **Début de la Logique ZIP :** Ébauche des fonctions `create_zipfile` et `update_zipfile` avec l'utilisation du module `zipfile` et de `uuid`. |
| | 📊 **Variables d'État :** Création et mise à jour des `StringVar` pour le nombre de fichiers et le statut d'exportation. |

### 🧑 Assistant IA Gemini

Contribution résidant dans la **structure du code**, la **résolution des problèmes** et l'**amélioration des fonctionnalités** pour transformer un prototype fonctionnel en une application robuste et maintenable.

| Catégorie | Description de la Contribution |
| :--- | :--- |
| **Architecture Logicielle** | 🏗️ **Implémentation du Modèle MVC :** Séparation du code en `Model`, `View`, et `Controller` pour une meilleure maintenabilité. |
| | 🏷️ **Ajout des Annotations de Type :** Rendre le code plus clair et moins sujet aux erreurs. |
| **Fonctionnalités Clés** | 🔄 **Gestion Robuste des Doublons :** Logique complexe pour éviter l'écrasement des fichiers (copie avec ID unique temporaire, puis suffixe numérique lors du renommage final). |
| | 🚀 **Intégration du Threading :** Exécution de la conversion/exportation en arrière-plan (`_run_export_in_thread`) pour empêcher le blocage de l'interface utilisateur (blocage "freeze"). |
| | ⚙️ **Renommage en Place (Treeview) :** Implémentation du double-clic pour éditer le nom des fichiers directement dans l'interface, incluant la gestion des doublons en temps réel. |
| **Correction & Amélioration** | 🐞 **Correction de la Logique d'Exportation :** S'assurer que les fichiers du `Treeview` (noms modifiés) sont correctement liés aux fichiers source pour l'exportation. |
| | 🗑️ **Gestion des Répertoires Temporaires :** Implémentation de la création et du nettoyage sécurisé des dossiers temporaires (`shutil.rmtree`). |
| | 💬 **Statut et Messages Utilisateur :** Ajout des messages d'erreur et de succès (`messagebox`) et des mises à jour de statut plus détaillées. |

-----

## 🛠️ Prérequis

Pour utiliser cette application, vous devez avoir installé :

1.  **Python 3.x** (avec `tkinter` installé et fonctionnel).
2.  **LibreOffice** ou **OpenOffice** sur votre système.
      * Le chemin de l'exécutable `soffice` (qui est utilisé pour la conversion) doit être accessible via les variables d'environnement (`PATH`).

## 🚀 Démarrage

1.  Assurez-vous d'avoir installé tous les prérequis.
2.  Exécutez l'application en lançant le fichier du contrôleur :

```bash
python controller.py
```

## 📝 Guide d'Utilisation

1.  **Importer :** Cliquez sur **"Importer les fichiers"** pour sélectionner vos documents.
2.  **Modifier :** **Double-cliquez** sur le nom d'un fichier dans la liste pour le renommer (ce sera le nom de votre PDF).
3.  **Exporter :** Cliquez sur **"Exporter en ZIP"** et choisissez votre répertoire de destination. Le statut en bas de l'écran vous informera de l'avancement.
4.  **Nettoyer :** Utilisez **"Réinitialiser la liste"** pour vider l'application.


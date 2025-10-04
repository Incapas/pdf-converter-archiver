import pathlib
import subprocess
import shutil
import os
from typing import Dict, Set, Tuple, Callable, Any, Optional
from subprocess import CalledProcessError

# Définition du type pour un élément de fichier : (ID, Nom_Modifiable, Extension)
FileElement = Tuple[int, str, str]


class Model:
    """
    Gère les données de l'application (liste des fichiers importés) et la logique métier
    d'importation, de modification, de conversion PDF et d'archivage ZIP.
    """
    def __init__(self) -> None:
        # Structures de Données Centrales 
        
        # Dictionnaire pour stocker le chemin absolu du fichier original {ID: Chemin_Absolu}
        self.file_path_dict: Dict[int, str] = {}  
        
        # Dictionnaire pour stocker les éléments affichés/modifiés {ID: (ID, Nom_Modifiable, Extension)}
        self.file_element_dict: Dict[int, FileElement] = {} 
        
        # Ensemble pour assurer l'unicité des noms complets (Nom_Modifiable + Ext) dans la liste
        self.unique_file_names: Set[str] = set() 
        
        # Compteur pour attribuer un ID unique à chaque nouveau fichier importé
        self.counter: int = 1

    def add_file(self, 
                 absolute_path: str, 
                 file_stem: str, 
                 file_suffix: str, 
                 ask_confirm_func: Callable[[str], bool]) -> Optional[FileElement]:
        """
        Ajoute un fichier au modèle après vérification des doublons de chemin et de nom.
        :param absolute_path: Chemin absolu du fichier source.
        :param file_stem: Nom du fichier sans extension.
        :param file_suffix: Extension du fichier.
        :param ask_confirm_func: Fonction de rappel pour demander confirmation en cas de doublon de nom.
        :return: Le nouvel élément de fichier (FileElement) si ajouté, ou None.
        """
        # Vérifie si le fichier est déjà chargé via son chemin absolu
        if absolute_path in self.file_path_dict.values():
            return None

        file_full_name: str = file_stem + file_suffix
        
        # Vérifie l'unicité par Nom + Extension (même si le chemin est différent)
        if file_full_name in self.unique_file_names:
            # Demande confirmation via la fonction de rappel fournie par le Controller
            if not ask_confirm_func(file_full_name):
                return None

        current_id: int = self.counter
        
        # Ajout des données au modèle
        self.file_path_dict[current_id] = absolute_path 
        file_element: FileElement = (current_id, file_stem, file_suffix)
        self.file_element_dict[current_id] = file_element
        self.unique_file_names.add(file_full_name)
        
        # Incrémentation du compteur pour le prochain fichier
        self.counter += 1
        return file_element

    def update_file_stem(self, file_id: str, new_stem: str) -> Optional[FileElement]:
        """
        Met à jour le nom (stem) d'un fichier.
        :param file_id: ID unique du fichier (clé dans les dictionnaires).
        :param new_stem: Le nouveau nom sans extension.
        :return: Le tuple FileElement mis à jour, ou None si un conflit de nom est détecté.
        """
        file_id_int: int = int(file_id)
        
        # Récupère et copie les valeurs actuelles pour modification
        current_values: list[Any] = list(self.file_element_dict[file_id_int])
        old_stem: str = current_values[1]
        extension: str = current_values[2]
        
        old_full_name: str = old_stem + extension
        new_full_name: str = new_stem + extension
        
        # Vérifie si la modification crée un doublon
        if new_full_name != old_full_name and new_full_name in self.unique_file_names:
            return None 
        
        # Retire l'ancien nom de l'ensemble d'unicité et ajoute le nouveau
        if old_full_name in self.unique_file_names:
            self.unique_file_names.remove(old_full_name)
        self.unique_file_names.add(new_full_name)

        # Met à jour la valeur dans le dictionnaire central
        current_values[1] = new_stem
        self.file_element_dict[file_id_int] = tuple(current_values)
        return tuple(current_values)
        
    def get_file_count(self) -> int:
        """Retourne le nombre total de fichiers dans le modèle."""
        return len(self.file_path_dict)
        
    def reset(self) -> None:
        """Réinitialise toutes les structures de données du modèle."""
        self.file_path_dict.clear()
        self.file_element_dict.clear()
        self.unique_file_names.clear()
        self.counter = 1
        
    # Logique d'Exportation PDF (Exécutée en Thread) 
    
    def export(self, temp_outdir: pathlib.Path) -> None:
        """
        Convertit chaque fichier en PDF dans un répertoire temporaire.
        Utilise un nom de fichier temporaire unique basé sur l'ID pour éviter les conflits
        de nom lors de la conversion par soffice.
        :param temp_outdir: Chemin du répertoire temporaire pour la conversion.
        :raises CalledProcessError: Si soffice échoue à convertir un fichier.
        """
        # Crée le répertoire temporaire s'il n'existe pas
        temp_outdir.mkdir(parents=True, exist_ok=True)
        
        # Parcourt tous les fichiers à exporter
        for file_id, original_path in self.file_path_dict.items():
            
            # Récupère le nom modifié souhaité
            file_elements: FileElement = self.file_element_dict[file_id]
            new_pdf_name_stem: str = file_elements[1]
            
            original_file_path: pathlib.Path = pathlib.Path(original_path)
            
            # Construit un nom de fichier d'entrée temporaire UNIQUE (ID_nomoriginal.ext)
            temp_unique_original_name: str = f"{file_id}_{original_file_path.name}"
            temp_unique_original_path: pathlib.Path = temp_outdir / temp_unique_original_name
            
            # Copie le fichier original dans le répertoire temporaire (pour une entrée propre à soffice)
            shutil.copy(original_file_path, temp_unique_original_path)
            
            # Détermine le nom du PDF généré par soffice (basé sur le nom d'entrée temporaire)
            generated_pdf_name: str = f"{temp_unique_original_path.stem}.pdf"
            pdf_original_path: pathlib.Path = temp_outdir / generated_pdf_name
            
            try:
                # Exécute la commande soffice pour la conversion
                subprocess.run(
                    [
                        "soffice",
                        "--headless",
                        "--convert-to", "pdf",
                        "--outdir", str(temp_outdir),
                        str(temp_unique_original_path)
                    ],
                    check=True,  # Lève une exception si soffice échoue
                    capture_output=True 
                )
                
                # Détermine le chemin final souhaité (Nom_Modifié.pdf)
                pdf_new_path: pathlib.Path = temp_outdir / f"{new_pdf_name_stem}.pdf"
                
                # Gestion des Conflits de Nom PDF Final 
                counter: int = 1
                final_name_base: str = new_pdf_name_stem
                # Ajoute un suffixe numérique si le nom final existe déjà (dû à la modification utilisateur)
                while pdf_new_path.exists():
                    pdf_new_path = temp_outdir / f"{final_name_base}_{counter}.pdf"
                    counter += 1
                    
                # Renomme le PDF généré (nom unique) vers le nom final (modifié)
                if pdf_original_path.exists():
                     pdf_original_path.rename(pdf_new_path)
                
            except CalledProcessError:
                # Relève l'erreur pour que le Controller puisse la gérer et afficher un message d'erreur
                raise 
            finally:
                # Supprime toujours le fichier original temporaire (la copie) après la conversion
                if temp_unique_original_path.exists():
                    os.remove(temp_unique_original_path)

    def create_zip_archive(self, source_dir: pathlib.Path, dest_dir: str, zip_name: str) -> str:
        """
        Compresse le contenu d'un répertoire dans un fichier ZIP.
        :param source_dir: Répertoire contenant les PDF convertis.
        :param dest_dir: Répertoire de destination pour le fichier ZIP.
        :param zip_name: Nom de base du fichier ZIP.
        :return: Le chemin absolu du fichier ZIP créé.
        """
        zip_path: pathlib.Path = pathlib.Path(dest_dir) / zip_name
        
        # Crée l'archive ZIP à partir du contenu de source_dir
        shutil.make_archive(str(zip_path), 'zip', root_dir=str(source_dir))
        return str(zip_path.with_suffix('.zip'))
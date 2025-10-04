import tkinter as tk
from tkinter import filedialog, messagebox
import pathlib
import threading
import shutil
import uuid
from subprocess import CalledProcessError
from typing import Optional, Tuple, Any

# Importation des autres modules
from model import Model, FileElement
from view import View


class Controller:
    """
    Gère le flux de l'application, traduisant les actions de la Vue en commandes
    pour le Modèle et mettant à jour la Vue en fonction des changements du Modèle.
    """
    def __init__(self, master: tk.Tk) -> None:
        self.master: tk.Tk = master
        # Instanciation du Modèle (les données)
        self.model: Model = Model()
        # Instanciation de la Vue (l'interface), en lui injectant le contrôleur
        self.view: View = View(master, self)
        
    def start(self) -> None:
        """Initialise la Vue et lance la boucle principale Tkinter."""
        self.view.update_status(0, "Prêt")
        self.master.mainloop()

    # Handlers d'Actions Utilisateur (Appelés par la Vue) 

    def handle_import(self) -> None:
        """Gère le clic sur le bouton 'Importer les fichiers'."""
        files = filedialog.askopenfiles(
            title="Sélectionnez les documents à ajouter",
            filetypes=[("Documents Modifiables", ["*.doc", "*.docx", "*.odt"])]
        )
        
        if not files:
            return

        newly_imported_count: int = 0
        for file in files:
            f: pathlib.Path = pathlib.Path(file.name)
            absolute_path: str = str(f.absolute())
            
            # Définition de la fonction de dialogue pour gérer les doublons de nom (utilisée par le Modèle)
            def ask_confirm(file_full_name: str) -> bool:
                return messagebox.askyesno(
                    "Doublon Détecté", 
                    f"Un fichier nommé '{file_full_name}' est déjà dans la liste.\n"
                    "Voulez-vous quand même l'ajouter ?"
                )
                
            # Tente d'ajouter le fichier au Modèle
            file_element: Optional[FileElement] = self.model.add_file(
                absolute_path, f.stem, f.suffix, ask_confirm
            )

            if file_element:
                # Si ajouté au Modèle, met à jour la Vue
                self.view.add_treeview_item(file_element)
                newly_imported_count += 1
            
            file.close()

        total_count: int = self.model.get_file_count()
        # Met à jour les statuts de la Vue
        self.view.update_status(total_count, "Prêt à exporter" if total_count > 0 else "")
        
        # Affiche un message si aucun fichier n'a été ajouté (uniquement des doublons)
        if newly_imported_count == 0 and total_count > 0 and files:
             messagebox.showinfo("Information", "Aucun nouveau fichier ajouté. Les fichiers sélectionnés étaient déjà présents.")


    def handle_double_click(self, event: tk.Event) -> None:
        """Gère le double-clic sur le Treeview pour lancer l'édition."""
        iid, column_id = self.view.get_selected_cell_info(event)
        
        # Autorise l'édition uniquement sur la colonne du Nom (colonne #2)
        if not iid or column_id != '#2':
            return
            
        current_values: Tuple[Any] = self.view.tree.item(iid, 'values')
        old_stem: str = current_values[1]
        
        # Demande à la Vue d'afficher l'Entry et lui passe la fonction de rappel pour le résultat
        self.view.show_edit_entry(iid, column_id, old_stem, self._finish_edit_callback)

    def _finish_edit_callback(self, iid: str, new_stem: str) -> None:
        """Fonction de rappel appelée par la Vue après l'édition en place."""
        
        if not new_stem:
            messagebox.showerror("Erreur de saisie", "Le nom ne peut pas être vide.")
            return

        # Extrait l'ID du Modèle (stocké dans la colonne 1 du Treeview)
        file_id: str = str(self.view.tree.item(iid, 'values')[0])
        
        # Tente de mettre à jour le Modèle
        updated_values: Optional[FileElement] = self.model.update_file_stem(file_id, new_stem)
        
        if updated_values is None:
            # En cas de conflit de nom (doublon)
            extension: str = self.model.file_element_dict[int(file_id)][2]
            messagebox.showwarning("Doublon", f"Le nom '{new_stem + extension}' existe déjà. Modification annulée.")
        else:
            # Met à jour la ligne du Treeview dans la Vue
            self.view.update_treeview_item(iid, updated_values)

    def handle_reset(self) -> None:
        """Gère le clic sur le bouton 'Réinitialiser la liste'."""
        self.model.reset()
        self.view.clear_treeview()
        self.view.update_status(0, "")
        messagebox.showinfo("Réinitialisation", "La liste des fichiers a été réinitialisée.")

    # Logique d'Exportation et Threading 

    def handle_export(self) -> None:
        """Prépare et lance le processus d'exportation ZIP en arrière-plan."""
        if self.model.get_file_count() == 0:
            messagebox.showwarning("Attention", "Veuillez importer des fichiers avant d'exporter.")
            return

        # Demande à l'utilisateur de choisir le répertoire de destination
        directory: str = filedialog.askdirectory(title="Sélectionnez le répertoire de destination pour le fichier ZIP")
        if not directory:
            return
        
        # Mise à jour de l'état de l'interface avant le lancement du thread
        self.view.update_status(self.model.get_file_count(), "Initialisation de l'exportation...")
        self.view.set_control_states(enabled=False)
        
        # Crée et démarre le thread pour l'opération longue (conversion/zip)
        export_thread: threading.Thread = threading.Thread(
            target=self._run_export_in_thread,
            args=(directory,)
        )
        export_thread.start()

    def _run_export_in_thread(self, directory: str) -> None:
        """Fonction exécutée dans un thread séparé pour l'exportation."""
        temp_dir: Optional[pathlib.Path] = None
        try:
            # Crée un chemin pour le répertoire temporaire de travail
            temp_dir = pathlib.Path.cwd() / f"temp_pdf_export_{uuid.uuid4().hex}"
            
            # 1. Conversion PDF (appel au Modèle)
            self.view.update_status(self.model.get_file_count(), "Conversion PDF en cours...")
            self.model.export(temp_dir) 
            
            # 2. Création de l'archive ZIP (appel au Modèle)
            self.view.update_status(self.model.get_file_count(), "Création de l'archive ZIP...")
            zip_filename: str = f"Export_PDFs_{pathlib.Path(directory).name}_{uuid.uuid4().hex[:4]}"
            zip_file_path: str = self.model.create_zip_archive(temp_dir, directory, zip_filename)
            
            # Affichage du succès
            messagebox.showinfo("Exportation Terminée", f"Exportation réussie !\nFichier ZIP créé : {pathlib.Path(zip_file_path).name}\nDans : {directory}")
            
            # 3. Réinitialisation complète après succès
            self.handle_reset() 

        except CalledProcessError:
            # Gestion de l'échec de la conversion par soffice
            self.view.update_status(self.model.get_file_count(), "Échec de l'exportation PDF.")
        except Exception as e:
            # Gestion des autres erreurs (ZIP, I/O, etc.)
            self.view.update_status(self.model.get_file_count(), "Échec de l'exportation. Erreur fatale.")
            messagebox.showerror("Erreur Fatale d'Exportation", f"Une erreur inattendue est survenue : {e}")

        finally:
            # Nettoyage et Réactivation (exécuté même en cas d'erreur) 
            # Supprime le répertoire temporaire
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)
            # Réactive les boutons de l'interface
            self.view.set_control_states(enabled=True)


if __name__ == '__main__':
    # Initialisation de l'application
    root: tk.Tk = tk.Tk()
    root.geometry("650x400")
    root.minsize(width=650, height=400) 
    app: Controller = Controller(root)
    app.start()
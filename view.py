import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Tuple, Callable

# Type hinting pour éviter les importations circulaires (uniquement pour l'analyse statique)
if TYPE_CHECKING:
    from controller import Controller 

# Définition du type pour les valeurs des lignes du Treeview : (ID, Nom_Modifiable, Extension)
TreeviewValues = Tuple[int, str, str]


class View(tk.Frame):
    """
    Gère l'interface graphique Tkinter. Elle ne contient aucune logique métier
    et délègue toutes les actions utilisateur au Controller.
    """
    def __init__(self, master: tk.Tk, controller: 'Controller') -> None:
        super().__init__(master)
        self.master: tk.Tk = master
        # Référence au contrôleur injecté
        self.controller: 'Controller' = controller
        
        # Variables Tkinter pour les labels de statut
        self.number_files_imported: tk.StringVar = tk.StringVar(value="Fichier(s) importé(s) : 0")
        self.export_status: tk.StringVar = tk.StringVar(value="")

        # Déclaration des widgets principaux
        self.tree: ttk.Treeview
        self.btn_import: ttk.Button
        self.btn_export: ttk.Button
        self.btn_reset: ttk.Button

        self.pack()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Initialise tous les widgets de l'interface."""
        self.master.title("Convertisseur et Archiveur PDF")

        # Configuration du Treeview 
        self.tree = ttk.Treeview(self.master, columns=(1, 2, 3), show="headings")
        
        self.tree.heading(1, text="ID")
        self.tree.heading(2, text="Nom")
        self.tree.heading(3, text="Extension")

        # Configuration des largeurs de colonnes
        self.tree.column(1, width=50, stretch=tk.NO)
        self.tree.column(2, width=350, stretch=tk.YES)
        self.tree.column(3, width=90, stretch=tk.NO)
    
        self.tree.pack(expand=True, fill="both", padx=10, pady=(10, 5))
        
        # Liaison du double-clic à la méthode du contrôleur
        self.tree.bind('<Double-1>', self.controller.handle_double_click)

        # Labels de Statut 
        self.lbl_number_files_imported = ttk.Label(self.master, textvariable=self.number_files_imported)
        self.lbl_number_files_imported.pack(expand=True, fill="x", padx=9)
        self.lbl_export_status = ttk.Label(self.master, textvariable=self.export_status)
        self.lbl_export_status.pack(expand=True, fill="x", padx=9)

        # Conteneur des Boutons 
        self.btn_container = ttk.Frame(self.master)
        self.btn_container.pack(expand=True, fill="x", pady=(5, 10))

        # Liaison des boutons aux méthodes du contrôleur
        self.btn_import = ttk.Button(self.btn_container, text="Importer les fichiers", command=self.controller.handle_import, padding=10)
        self.btn_import.grid(column=1, row=1, padx=10, pady=5)
        self.btn_export = ttk.Button(self.btn_container, text="Exporter en PDF", command=self.controller.handle_export, padding=10)
        self.btn_export.grid(column=2, row=1, padx=10, pady=5)
        self.btn_reset = ttk.Button(self.btn_container, text="Réinitialiser la liste", command=self.controller.handle_reset, padding=10)
        self.btn_reset.grid(column=3, row=1, padx=10, pady=5)
        self.btn_container.columnconfigure((0, 4), weight=1)

    # Méthodes de Mise à Jour de l'Affichage 
    
    def update_status(self, total_count: int, export_status_text: str) -> None:
        """Met à jour les labels de statut de l'interface."""
        self.number_files_imported.set(f"Fichier(s) importé(s) : {total_count}")
        self.export_status.set(export_status_text)
        self.master.update_idletasks()

    def add_treeview_item(self, values: TreeviewValues) -> None:
        """Insère une nouvelle ligne dans le Treeview."""
        self.tree.insert("", "end", values=values)
        
    def clear_treeview(self) -> None:
        """Supprime toutes les lignes du Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
    def update_treeview_item(self, iid: str, new_values: TreeviewValues) -> None:
        """Met à jour les valeurs d'une ligne existante dans le Treeview."""
        self.tree.item(iid, values=new_values)
        
    def get_selected_cell_info(self, event: tk.Event) -> Tuple[str, str]:
        """Identifie la ligne (iid) et la colonne cliquée à partir de l'événement."""
        item_id: str = self.tree.identify_row(event.y)
        column_id: str = self.tree.identify_column(event.x)
        return item_id, column_id
        
    def set_control_states(self, enabled: bool = True) -> None:
        """Active ou désactive les boutons principaux (utile pendant l'exportation)."""
        state: str = tk.NORMAL if enabled else tk.DISABLED
        self.btn_import.config(state=state)
        self.btn_export.config(state=state)
        self.btn_reset.config(state=state)

    # Logique d'Édition en Place (UI) 

    def show_edit_entry(self, 
                        iid: str, 
                        column_id: str, 
                        old_value: str, 
                        callback: Callable[[str, str], None]) -> None:
        """
        Affiche le widget Entry (champ de saisie) directement sur la cellule cliquée
        pour l'édition en place.
        :param iid: L'identifiant interne de la ligne du Treeview.
        :param callback: Fonction du Controller à appeler après la saisie.
        """
        # Calcule les coordonnées et dimensions de la cellule
        x, y, width, height = self.tree.bbox(iid, column_id)

        # Crée l'Entry et le positionne
        entry: ttk.Entry = ttk.Entry(self.tree, width=width)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, old_value)
        entry.focus()
        entry.select_range(0, tk.END)

        def on_entry_finish(event: tk.Event) -> None:
            """Fonction appelée à la validation (Return ou FocusOut)."""
            new_stem: str = entry.get().strip()
            # Détruit l'Entry avant d'appeler le callback pour nettoyer l'interface
            entry.destroy()
            # Renvoie l'iid de la ligne et la nouvelle valeur au contrôleur
            callback(iid, new_stem) 
            
        # Bindings pour la validation et le nettoyage
        entry.bind('<Return>', on_entry_finish)
        entry.bind('<FocusOut>', on_entry_finish)
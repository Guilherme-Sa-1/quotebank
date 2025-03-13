import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from .database import QuoteDB  # Altere para 'from database import QuoteDB' se executar diretamente

class QuoteApp:
    def __init__(self, root):
        self.db = QuoteDB()
        self.root = root
        self.root.title("QuoteBank Pro")
        self.root.state('zoomed')
        
        self.style = ttk.Style()
        self._configure_styles()
        self.MAX_QUOTE_PREVIEW = 150
        self.current_full_quotes = {}

        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        self.load_quotes()

    def _configure_styles(self):
        # Usa o tema 'clam' para permitir maior customização
        self.style.theme_use('clam')
        
        # Definindo as cores base
        navy = "#001f3f"    # Azul marinho
        white = "#ffffff"   # Branco
        black = "#000000"   # Preto
        gray = "#808080"    # Cinza
        red = "#ff0000"     # Vermelho
        gold = "#ffd700"    # Dourado

        # Configuração dos frames e labels
        self.style.configure('TFrame', background=navy)
        self.style.configure('TLabel', background=navy, foreground=white, font=('Arial', 10))
        
        # Configuração dos campos de entrada
        self.style.configure('TEntry', foreground=black, font=('Arial', 10))
        
        # Configuração dos botões
        # OBS.: Botões arredondados não são suportados nativamente pelo ttk.
        # Se desejar botões com cantos arredondados, considere usar customtkinter ou imagens customizadas.
        self.style.configure('TButton',
                             background=gold,
                             foreground=navy,
                             font=('Arial', 10),
                             padding=5)
        self.style.map('TButton', 
                       background=[('active', red)],
                       relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Configuração da Treeview (lista de citações)
        self.style.configure('Treeview',
                             background=white,
                             foreground=black,
                             font=('Arial', 10),
                             rowheight=30)
        self.style.configure('Treeview.Heading', 
                             background=gray,
                             foreground=white,
                             font=('Arial', 10, 'bold'))
        self.style.map('Treeview', background=[('selected', red)])

    def _create_widgets(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.input_frame = ttk.LabelFrame(self.main_frame, text="Nova Citação")
        self._create_input_fields()

        self.search_frame = ttk.Frame(self.main_frame)
        self._create_search_fields()

        self.tree_frame = ttk.Frame(self.main_frame)
        self._create_treeview()

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="✏️ Editar", command=self.edit_quote)
        self.context_menu.add_command(label="🗑️ Excluir", command=self.delete_quote)

    def _setup_layout(self):
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        
        self.input_frame.grid(row=0, column=0, sticky='nsew', pady=5)
        self.search_frame.grid(row=1, column=0, sticky='ew', pady=5)
        self.tree_frame.grid(row=2, column=0, sticky='nsew')

        self.input_frame.columnconfigure(1, weight=1)
        self.search_frame.columnconfigure(0, weight=1)

    def _create_input_fields(self):
        fields = [
            ('Citação:', 70),
            ('Autor:', 30),
            ('Categoria:', 30),
            ('Fonte:', 30)
        ]

        self.entries = {}
        for row, (label, width) in enumerate(fields):
            ttk.Label(self.input_frame, text=label).grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            entry = ttk.Entry(self.input_frame, width=width)
            entry.grid(row=row, column=1, padx=5, pady=2, sticky='ew')
            self.entries[label] = entry

        # Se desejar botões arredondados, considere usar customtkinter.
        # Aqui, utilizamos o botão padrão do ttk.
        ttk.Button(self.input_frame, text="Adicionar", command=self.add_quote).grid(row=4, column=1, pady=5, sticky='e')

    def _create_search_fields(self):
        self.search_entry = ttk.Entry(self.search_frame)
        self.search_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        ttk.Button(self.search_frame, text="Buscar", command=self.search_quotes).pack(side='left', padx=5)
        ttk.Button(self.search_frame, text="Limpar", command=self.load_quotes).pack(side='left')

    def _create_treeview(self):
        self.tree = ttk.Treeview(self.tree_frame, 
                                 columns=('Citação', 'Autor', 'Categoria', 'Fonte', 'Data'),
                                 show='headings')

        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)

        headers = [
            ('Citação', 500),
            ('Autor', 150),
            ('Categoria', 150),
            ('Fonte', 200),
            ('Data', 120)
        ]

        for col, width in headers:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='w', stretch=True)

    def _bind_events(self):
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind('<Double-1>', self.show_quote_details)
        self.tree.bind('<Return>', self.show_quote_details_enter)
        self.tree.bind('<Enter>', self.show_full_quote)
        self.tree.bind('<Leave>', self.hide_tooltip)

    def show_quote_details_enter(self, event):
        selected = self.tree.selection()
        if selected:
            self._show_quote_details(item=selected[0])

    def show_quote_details(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self._show_quote_details(item)

    def _show_quote_details(self, item):
        quote_id = self.current_full_quotes[item]
        quote_data = self.db.get_quote(quote_id)
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Detalhes da Citação")
        detail_window.geometry("600x400")
        
        main_frame = ttk.Frame(detail_window, padding=20)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text="Autor:", font=('Arial', 12, 'bold')).pack(anchor='w')
        ttk.Label(main_frame, text=quote_data[2] or "Desconhecido", font=('Arial', 12)).pack(anchor='w', pady=(0, 15))

        source = quote_data[4] or "Fonte não especificada"
        year = datetime.strptime(quote_data[5], "%Y-%m-%d %H:%M:%S.%f").year
        ttk.Label(main_frame, text="Origem:", font=('Arial', 12, 'bold')).pack(anchor='w')
        ttk.Label(main_frame, text=f"{source} - {year}", font=('Arial', 12)).pack(anchor='w', pady=(0, 15))

        ttk.Label(main_frame, text="Citação:", font=('Arial', 12, 'bold')).pack(anchor='w')
        quote_frame = ttk.Frame(main_frame)
        quote_frame.pack(fill='both', expand=True)
        
        text_quote = tk.Text(quote_frame, wrap='word', font=('Arial', 12), padx=10, pady=10, height=8)
        text_quote.insert('end', quote_data[1])
        text_quote.config(state='disabled')
        
        vsb = ttk.Scrollbar(quote_frame, command=text_quote.yview)
        text_quote.configure(yscrollcommand=vsb.set)
        
        text_quote.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        ttk.Button(main_frame, text="Fechar", command=detail_window.destroy).pack(pady=(20, 0))

        detail_window.transient(self.root)
        detail_window.grab_set()

    def add_quote(self):
        data = (
            self.entries['Citação:'].get(),
            self.entries['Autor:'].get(),
            self.entries['Categoria:'].get(),
            self.entries['Fonte:'].get()
        )
        if not data[0]:
            messagebox.showwarning("Erro", "A citação não pode estar vazia!")
            return

        self.db.add_quote(*data)
        self.clear_entries()
        self.load_quotes()

    def edit_quote(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        quote_id = self.current_full_quotes[item]
        quote_data = self.db.get_quote(quote_id)

        edit_window = tk.Toplevel(self.root)
        edit_window.title("Editar Citação")
        
        entries = {}
        fields = ['Citação:', 'Autor:', 'Categoria:', 'Fonte:']
        for i, field in enumerate(fields):
            ttk.Label(edit_window, text=field).grid(row=i, column=0, sticky='w', padx=5, pady=2)
            entry = ttk.Entry(edit_window, width=70)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entry.insert(0, quote_data[i+1])
            entries[field] = entry

        def save_changes():
            new_data = (
                entries['Citação:'].get(),
                entries['Autor:'].get(),
                entries['Categoria:'].get(),
                entries['Fonte:'].get(),
                quote_id
            )
            self.db.update_quote(*new_data)
            edit_window.destroy()
            self.load_quotes()

        ttk.Button(edit_window, text="Salvar", command=save_changes).grid(row=4, column=1, pady=5, sticky='e')

    def delete_quote(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        if messagebox.askyesno("Confirmar", "Deseja realmente excluir esta citação?"):
            item = selected[0]
            quote_id = self.current_full_quotes[item]
            self.db.delete_quote(quote_id)
            self.load_quotes()

    def search_quotes(self):
        term = self.search_entry.get()
        results = self.db.search_quotes(term)
        self.update_tree(results)

    def load_quotes(self):
        self.update_tree(self.db.get_all_quotes())

    def update_tree(self, quotes):
        self.current_full_quotes.clear()
        self.tree.delete(*self.tree.get_children())
        
        for quote in quotes:
            preview = (quote[1][:self.MAX_QUOTE_PREVIEW] + '...') if len(quote[1]) > self.MAX_QUOTE_PREVIEW else quote[1]
            item = self.tree.insert('', 'end', values=(preview, quote[2], quote[3], quote[4], quote[5]))
            self.current_full_quotes[item] = quote[0]

    def clear_entries(self):
        for entry in self.entries.values():
            entry.delete(0, 'end')

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def show_full_quote(self, event):
        item = self.tree.identify_row(event.y)
        if item and len(self.tree.item(item)['values'][0]) > self.MAX_QUOTE_PREVIEW:
            x, y, _, _ = self.tree.bbox(item)
            self.tooltip = tk.Toplevel(self.root)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+20}+{event.y_root+10}")
            
            full_text = self.db.get_quote(self.current_full_quotes[item])[1]
            label = ttk.Label(self.tooltip, text=full_text, background="#ffffe0", relief='solid', padding=5, wraplength=600)
            label.pack()

    def hide_tooltip(self, event):
        if hasattr(self, 'tooltip') and self.tooltip.winfo_exists():
            self.tooltip.destroy()

    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if filename:
            self.db.export_csv(filename)
            messagebox.showinfo("Sucesso", f"Dados exportados para {filename}")

    def on_closing(self):
        self.db.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = QuoteApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

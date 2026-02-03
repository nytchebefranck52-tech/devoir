import wx, socket, pickle, base64, hashlib
from cryptography.fernet import Fernet
import matplotlib.pyplot as plt

# ===== CRYPTO =====
def key(password):
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def encrypt(password, obj):
    return Fernet(key(password)).encrypt(pickle.dumps(obj))

def decrypt(password, data):
    return pickle.loads(Fernet(key(password)).decrypt(data))

SERVER_IP = "192.168.136.38"
SERVER_PORT = 9999
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ===== SPLASH SCREEN =====
class Splash(wx.Frame):
    def __init__(self):
        super().__init__(None, size=(600,350), style=wx.NO_BORDER)
        panel = wx.Panel(self)
        panel.SetBackgroundColour("#84cc16")  # vert citron

        title = wx.StaticText(panel, label="GOOD GESTION")
        title.SetForegroundColour("#f97316")  # orange
        title.SetFont(wx.Font(34, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        quote = wx.StaticText(
            panel,
            label="“Pecunia si uti scis, ancilla est;\nsi nescis, domina.”"
        )
        quote.SetForegroundColour("#166534")
        quote.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))

        s = wx.BoxSizer(wx.VERTICAL)
        s.AddStretchSpacer()
        s.Add(title, 0, wx.CENTER)
        s.AddSpacer(20)
        s.Add(quote, 0, wx.CENTER)
        s.AddStretchSpacer()

        panel.SetSizer(s)
        self.Center()
        self.Show()

        wx.CallLater(5000, self.next)

    def next(self):
        self.Destroy()
        ProfileFrame()

# ===== PROFILE =====
class ProfileFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Création du profil", size=(420,420))
        panel = wx.Panel(self)
        panel.SetBackgroundColour("#ecfccb")

        self.name = wx.TextCtrl(panel)
        self.password = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        self.profession = wx.TextCtrl(panel)
        self.age = wx.TextCtrl(panel)

        btn = wx.Button(panel, label="Créer le profil")
        btn.SetBackgroundColour("#f97316")
        btn.Bind(wx.EVT_BUTTON, self.create)

        s = wx.BoxSizer(wx.VERTICAL)
        for lbl, field in [
            ("Nom", self.name),
            ("Mot de passe", self.password),
            ("Profession", self.profession),
            ("Âge", self.age)
        ]:
            s.Add(wx.StaticText(panel, label=lbl), 0, wx.ALL, 5)
            s.Add(field, 0, wx.EXPAND | wx.ALL, 5)

        s.Add(btn, 0, wx.CENTER | wx.ALL, 15)
        panel.SetSizer(s)
        self.Center()
        self.Show()

    def create(self, e):
        pwd = self.password.GetValue()
        sock.sendto(
            pwd.encode() + b"|" + encrypt(pwd, {
                "action": "PROFILE",
                "data": {
                    "name": self.name.GetValue(),
                    "profession": self.profession.GetValue(),
                    "age": self.age.GetValue()
                }
            }),
            (SERVER_IP, SERVER_PORT)
        )
        self.Destroy()
        ExpenseApp(pwd)

# ===== MAIN APP =====
class ExpenseApp(wx.Frame):
    def __init__(self, password):
        super().__init__(None, title="GOOD GESTION 💸", size=(900,700))
        self.password = password

        panel = wx.Panel(self)
        panel.SetBackgroundColour("#d9f99d")

        self.budget = wx.TextCtrl(panel)
        self.expense_name = wx.TextCtrl(panel)
        self.amount = wx.TextCtrl(panel)

        btn_budget = wx.Button(panel, label="Définir Budget (FCFA)")
        btn_add = wx.Button(panel, label="Ajouter Dépense")
        btn_graph = wx.Button(panel, label="Diagramme")

        btn_budget.SetBackgroundColour("#84cc16")
        btn_add.SetBackgroundColour("#f97316")
        btn_graph.SetBackgroundColour("#22c55e")

        btn_budget.Bind(wx.EVT_BUTTON, self.set_budget)
        btn_add.Bind(wx.EVT_BUTTON, self.add_expense)
        btn_graph.Bind(wx.EVT_BUTTON, self.graph)

        self.table = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.table.InsertColumn(0, "Nom de la dépense", width=420)
        self.table.InsertColumn(1, "Montant (FCFA)", width=200)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(wx.StaticText(panel, label="Budget mensuel (FCFA)"), 0, wx.ALL, 5)
        s.Add(self.budget, 0, wx.EXPAND | wx.ALL, 5)
        s.Add(btn_budget, 0, wx.ALL, 5)

        s.Add(wx.StaticText(panel, label="NOM DE LA DEPENSE"), 0, wx.ALL, 5)
        s.Add(self.expense_name, 0, wx.EXPAND | wx.ALL, 5)

        s.Add(wx.StaticText(panel, label="MONTANT"), 0, wx.ALL, 5)
        s.Add(self.amount, 0, wx.EXPAND | wx.ALL, 5)

        s.Add(btn_add, 0, wx.ALL, 5)
        s.Add(self.table, 1, wx.EXPAND | wx.ALL, 10)
        s.Add(btn_graph, 0, wx.CENTER | wx.ALL, 10)

        panel.SetSizer(s)
        self.Show()
        self.refresh()

    def send(self, obj):
        sock.sendto(
            self.password.encode() + b"|" + encrypt(self.password, obj),
            (SERVER_IP, SERVER_PORT)
        )
        data,_ = sock.recvfrom(8192)
        _, enc = data.split(b"|",1)
        return decrypt(self.password, enc)

    def set_budget(self, e):
        self.send({"action":"SET_BUDGET","budget":float(self.budget.GetValue())})
        self.refresh()

    def add_expense(self, e):
        data = self.send({
            "action":"ADD_EXPENSE",
            "expense":{
                "name": self.expense_name.GetValue(),
                "amount": float(self.amount.GetValue())
            }
        })
        remaining = data["budget"] - sum(x["amount"] for x in data["expenses"])
        wx.MessageBox(f"Budget restant : {remaining:,.0f} FCFA")

        self.refresh()

    def refresh(self):
        self.table.DeleteAllItems()
        data = self.send({"action":"GET"})
        for e in data["expenses"]:
            i = self.table.InsertItem(self.table.GetItemCount(), e["name"])
            self.table.SetItem(i, 1, f"{e['amount']:,.0f}")

    def graph(self, e):
        data = self.send({"action":"GET"})
        spent = sum(x["amount"] for x in data["expenses"])
        remaining = max(0, data["budget"] - spent)

        plt.pie(
            [spent, remaining],
            labels=["Dépensé","Restant"],
            colors=["#ef4444","#3b82f6"],
            autopct="%1.1f%%"
        )
        plt.title("Répartition du budget")
        plt.show()

if __name__ == "__main__":
    app = wx.App()
    Splash()
    app.MainLoop()

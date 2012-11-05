"""
Confronto tra ListCtrl "normali" e "virtuali".

Questo esempio mostra come usare un ListCtrl "virtuale" 
(con style=wx.LC_VIRTUAL) e la differenza con un ListCtrl normale. 
La classe DatabaseConnection gestisce la connessione con una tabella. 
Se il database non esiste, viene creato con dati casuali: quindi, 
la prima volta che si fa girare il codice, potrebbe volerci un po' di tempo.
DatabaseConnection viene istanziata a livello di wx.App, e pertato resa  
disponibile globalmente in tutta la gui. 
Al suo interno, i metodi "row_num" e "get_a_row" sono necessari per far 
funzionare il ListCtrl virtuale. 

NormalListFrame mostra il modo tradizionale di usare un ListCtrl: tutti i dati 
sono caricati e memorizzati insieme nella lista.  

VirtualListFrame mostra invece l'uso di un ListCtrl virtuale. La costruzione e' 
piu' semplice, perche' la lista vera e propria viene dichiarata in una classe 
separata, VirtualList, e qui basta richiamarla e impostare i titoli delle 
colonne.
VirtualList implementa il meccanismo specifico del ListCtrl virtuale. I punti 
fondamentali sono due: primo, occorre dire alla lista il _numero_ di righe che 
deve avere, con il metodo SetItemCount. Nel nostro caso bastera' farlo una 
volta sola, ma in generale bisogna farlo ogni volta che i dati cambiano.
Secondo, bisogna implementare il metodo "OnGetItemText", che ha il compito di 
restituire il valore di ogni singola cella. Il metodo e' usato internamente dal 
ListCtrl, e l'importante e' solo rispettarne l'api (in particolare, bisogna 
restituire un solo valore, non tutta la riga). 

La differenza tra il ListCtrl normale e quello virtuale e' notevole, come si 
puo' vedere da questo esempio, in cui cerchiamo di caricare una tabella di 
100mila righe.
"""

from sys import maxint    
from random import sample  
from string import ascii_letters  
import sqlite3
import wx  


class DatabaseConnection(object):  
    def __init__(self):  
        self.con = sqlite3.connect('test.sqlite', isolation_level=None,   
                                   detect_types=sqlite3.PARSE_DECLTYPES)  
        self.cur = self.con.cursor() 
        try:
            self.cur.execute('select 1 from test;')
        except sqlite3.OperationalError:  # table doesn't exist
            print 'creating database, please wait...'
            self.cur.execute("""CREATE TABLE test 
                                (f0 INTEGER PRIMARY KEY,  
                                 f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, f5 TEXT);""")  
            self.con.commit()  
            sql = """INSERT INTO test (f1, f2, f3, f4, f5)  
                     VALUES (?, ?, ?, ?, ?);"""  
            self.cur.execute('BEGIN;')  
            for i in xrange(100000):
                self.cur.execute(sql, [''.join(sample(ascii_letters, 10))]*5)  
            self.con.commit() 
      
    def row_num(self):  
        "Returns number of rows in table test."  
        self.cur.execute('SELECT count(f0) FROM test;')  
        return self.cur.fetchall()[0][0]  
      
    def get_a_row(self, id):  
        "Returns a row from table test."  
        sql = 'SELECT * FROM test WHERE f0=?;'  
        self.cur.execute(sql, (id,))  
        return self.cur.fetchall()[0]  
      
    def get_all_rows(self):  
        "Returns all rows from table test."  
        self.cur.execute('SELECT * from test;')  
        while True:  
            riga = self.cur.fetchone()  
            if not riga:  
                raise StopIteration  
            yield riga  
  
  
class NormalListFrame(wx.Frame):   
    def __init__(self, *args, **kwds):  
        wx.Frame.__init__(self, *args, **kwds)  
        list = wx.ListCtrl(self, -1, style=wx.LC_REPORT)  
        for n, c in enumerate(('field 0', 'field 1', 'field 2', 'field 3',   
                               'field 4', 'field 5')):   
            list.InsertColumn(n, c)  
            list.SetColumnWidth(n, 70)  
        # populate list
        for row in wx.GetApp().con.get_all_rows():  
            index = list.InsertStringItem(maxint, str(row[0]))  
            for col, val in enumerate(row[1:]):  
                list.SetStringItem(index, col+1, val)  
        list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select)
        self.list = list
        
    def on_select(self, evt):
        sel = self.list.GetFirstSelected()
        while sel != -1:
            print 'selected: ', sel
            sel = self.list.GetNextSelected(sel)
        print 
          

class VirtualList(wx.ListCtrl):  
    def __init__(self, parent):  
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL)
        self.SetItemCount(wx.GetApp().con.row_num()) 
          
    def OnGetItemText(self, row, col):  
        "Returns 'col' element from 'row' row."  
        data = wx.GetApp().con.get_a_row(row+1) # table's first id is 1
        return data[col]  
        
        
class VirtualListFrame(wx.Frame):   
    def __init__(self, *args, **kwds):  
        wx.Frame.__init__(self, *args, **kwds)  
        self.list = VirtualList(self)  
        for n, c in enumerate(('field 0', 'field 1', 'field 2', 'field 3',   
                               'field 4', 'field 5')): 
            self.list.InsertColumn(n, c)  
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select)
        
    def on_select(self, evt):
        sel = self.list.GetFirstSelected()
        while sel != -1:
            print 'selected: ', sel
            sel = self.list.GetNextSelected(sel)
        print 

  
class MainFrame(wx.Frame):   
    def __init__(self, *args, **kwds):  
        wx.Frame.__init__(self, *args, **kwds)  
        p = wx.Panel(self)  
        b1 = wx.Button(p, -1, 'See a NORMAL ListCtrl', pos=(20, 20))  
        b2 = wx.Button(p, -1, 'See a VIRTUAL LisCtrl', pos=(20, 50))  
        b1.Bind(wx.EVT_BUTTON, self.on_b1)  
        b2.Bind(wx.EVT_BUTTON, self.on_b2)  
          
    def on_b1(self, evt): NormalListFrame(self).Show()  
    def on_b2(self, evt): VirtualListFrame(self).Show()  
      

class App(wx.App):
    def OnInit(self):
        self.con = DatabaseConnection()
        return True
    

app = App(False)
MainFrame(None).Show()
app.MainLoop()

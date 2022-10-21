from IPython.display import display, Markdown, clear_output,Image,Javascript
import ipywidgets as widgets
import pickle
import base64
import ast
import re

#import unidecode

'''La classe QCM se construit à l'aide d'une liste de mots clés et d'un fichier pickle (qui a été dumpé depuis
un fichier txt par le fichier preparation.py.
elle construit un objet qui a des méthodes d'affichage et de correction.
Le nom de ces méthodes est le nom des questions à poser'''

def utf(ma_chaine):
    '''normalement, c'est unidecode qui fait le job :-)'''
    remplace={'à':'a','â':'a','ä':'a','é':'e','è':'e','ê':'e','ë':'e','ï':'i','î':'i','ô':'o','ö':'o','ù':'u','û':'u','ü':'u','ÿ':'y','ç':'c'}
    for cle,valeur in remplace.items():
        ma_chaine=ma_chaine.replace(cle,valeur)
    return ma_chaine

def create_code_cell(code='', where='below'):
    # https://github.com/ipython/ipython/issues/4983
    """Create a code cell in the IPython Notebook.

    Parameters
    code: unicode
        Code to fill the new code cell with.
    where: unicode
        Where to add the new code cell.
        Possible values include:
            at_bottom
            above
            below"""
    encoded_code = (base64.b64encode(str.encode(code))).decode()
    display(Javascript("""
        var code = IPython.notebook.insert_cell_{0}('code');
        code.set_text(atob("{1}"));
    """.format(where, encoded_code)))


def convertir_donnee(ma_chaine):
    # si ma_chaine commence par des guillemets, le type désiré est string de toute façon:
    if ma_chaine!='' and ma_chaine[0] in ['\'','\"']:
        if ma_chaine[-1] in ['\'','\"']:
            return ma_chaine[1:-1]
        else:
            return ma_chaine[1:] # en cas d'oubli du guillemet qui ferme
    try: # sinon, on essaie d'évaluer le type de ma_chaine
        #t=ast.literal_eval(ma_chaine)
        t=eval(ma_chaine)
        return t
    except :
        # La ou les réponses sont de type littéral. On retourne la liste des éléments saisis sans les espaces.
        return ma_chaine #.strip()

class Check():
    '''Pour créer les checkbox du QCM'''
    def __init__(self,lst_infos,multi):
        self.chk=[]
        self.a_afficher=[]

        for d in lst_infos:
            w=widgets.Checkbox(description='',value=False)
            w.layout.width='15ex'
            m=widgets.HTMLMath(value=d) # plus de conversion ici en théorie
            self.chk.append(w)
            h=widgets.HBox([w,m])
            self.a_afficher.append(h)
        self.chk[0].value=True
        self.n=len(self.chk)
        if not multi:# on rajoute le fait de de ne pouvoir cocher qu'une seule prop
            for check in self.chk:
                check.observe(self.changed,names=['value'])

    
    def changed(self,c):
        actuel=c['owner']
        if not c['old']: # le boutons n'était pas coché, on le coche et on décoche le reste
            for b in self.chk:
                if b!=actuel:
                    b.value=False
            #actuel.value=True
        autres=[b for b in self.chk if not b==actuel]
        deja_coches=[b for b in autres if b.value]
        if len(deja_coches)==0:
            actuel.value=True

                
    def affiche(self):
        display(widgets.VBox(self.a_afficher))
        

class Question():
    def __init__(self, dic_infos):
        self.infos=dic_infos
        self.mots=list(dic_infos.keys())

    def afficher(self):
        propositions=self.infos[self.mots[2]]
        self.n=len(propositions)
        #print(propositions)
        consigne=self.infos[self.mots[1]]
        #propositions=[convertir_html(chr(65+k)+'. '+ p) for p,k in zip(propositions,range(self.n))]
        self.coches=[]
        
        # Création des checkbox avec propositions
        c=Check(propositions,self.infos["multi"])
        self.coches=c.chk

        self.button = widgets.Button(description='CORRIGER')
        self.button.on_click(self.corriger)
        self.out=widgets.Output()
        
        if self.infos["multi"]:
            c.chk[0].value=False
        #consigne=convertir_html(consigne)
        display(Markdown(consigne))
        return widgets.VBox(c.a_afficher + [self.button, self.out])


    def corriger(self,*args):
        # On commence par déterminer si la ou les réponses sont bonnes :
        reponses=self.infos[self.mots[3]]
        self.button.disabled=True
        for element in self.coches:
            element.disabled=True
        valide = True

        for k in range(self.n):
            valide=valide and self.coches[k].value==reponses[k]



#         if self.infos[self.mots[4]][0]=='-':
#             correction+='\n'
#         correction+=self.infos[self.mots[4]]
        #correction='<br>● '+correction
        correction=self.infos[self.mots[4]]
        with self.out:
            # on nettoie la sortie
            clear_output()
            if valide:
                correction='<font color=green> '+correction+'</font>'
            else:
                correction='<font color=red>'+correction+'</font>'
           

            display(Markdown(correction))




class QCM():
    def __init__(self,dic_infos,lst_mots_cles):
        self.mots=lst_mots_cles
        self.infos=dic_infos
        self.creer_qcm()

    def creer_qcm(self):
        for dic in self.infos:
            self.__dict__[dic[self.mots[0]]] = Question(dic).afficher



class Solution():
    def __init__(self,dic_infos,lst_mots_cles):
        self.infos=dic_infos
        self.mots=lst_mots_cles
        self.creer_questions()
    

    def creer_questions(self):
        for dic in self.infos:
            self.__dict__[dic[self.mots[0]]] = Correction(dic,self.mots).afficher


class Correction():
    def __init__(self, dic_infos, mots):
        self.infos=dic_infos
        self.mots=mots
        self.montre_indic=False
        self.montre_correc=False
        
    # problème ici : si seul bouton réponse!
    def creer_boutons(self):
        clear_output()
        a_afficher=[]
        if self.infos[self.mots[1]]!='' and self.infos[self.mots[1]][0:2]!='#\n': # non affiché si # présent derrière indication
            
            self.bouton_indice = widgets.Button(description='INDICATION')
            self.bouton_indice.on_click(self.indice)
            a_afficher.append(self.bouton_indice)
            
        if self.infos[self.mots[2]]!='' and self.infos[self.mots[2]][0:2]!='#\n': # on rajoute le fait de pouvoir préparer sans afficher la réponse finale dans le cas où on écrit '#' après le mot clef rep_question
            self.bouton_rep = widgets.Button(description='REPONSE')
            self.bouton_rep.on_click(self.reponse)
            a_afficher.append(self.bouton_rep)       
        
        
        #display(self.bouton_indice, self.bouton_rep)
        display(widgets.VBox(a_afficher))
     
        

    def afficher(self):
        self.creer_boutons()
    
    def indice(self,*args):
        if not self.montre_indic:
            self.creer_boutons()
            contenu=self.infos[self.mots[1]]
            #contenu=convertir_html(contenu)
            display(Markdown(contenu))
            self.bouton_indice.description='CACHER'
            self.montre_indic=True
        
        else:
            #clear_output()
            self.creer_boutons()
            self.montre_indic=False
        
        
    def reponse(self,*args):
        contenu=self.infos[self.mots[2]]
        if self.infos['reponse_en_python']:# Si la réponse est de type code python, on crée une nouvelle cellule.
            self.creer_boutons()
            display(Markdown("Voici la correction :"))
            contenu = utf(contenu)
            create_code_cell(contenu)
            
            #display(Markdown(contenu))
        else: # la réponse n'est pas de type code python
            if not self.montre_correc:
                self.creer_boutons()
                try:
                    self.bouton_indice.description='INDICATION'
                    self.montre_indic=False
                except:
                    pass
                    
                
                contenu=self.infos[self.mots[2]]
                #contenu=convertir_html(contenu)
                display(Markdown(contenu))
                self.bouton_rep.description='CACHER'
                self.montre_correc=True
        
            else:
                self.creer_boutons()
                self.montre_correc=False
                self.creer_boutons()

class Img():
    def __init__(self, nom_image, mots):
        self.mots=mots
        self.mon_image=Image(filename=nom_image)
        self.montre_image=False
        self.new=False
        
    
    def creer_bouton(self):
        clear_output()
        self.bouton= widgets.Button(description=self.mots[0])
        self.bouton.on_click(self.afficher)
        display(self.bouton)
        
        
    def afficher(self,*args):
        if not self.montre_image:
            self.creer_bouton()
            self.bouton.description=self.mots[1]
            display(self.mon_image)
            self.montre_image=True
            
        else:
            clear_output()
            self.creer_bouton()
            self.montre_image=False
  

        
# class Montre():
#     
#     def __init__(self,lst_noms,lst_mots_cles):
#         self.noms=lst_noms
#         self.mots=lst_mots_cles
#         self.creer()
#     
#     def creer(self):
#         for nom in self.noms:
#             pos_point=nom.rfind('.') # on cherche l'index du dernier point du nom, celui qui précède l'extension
#             methode=nom[:pos_point]
#             mon_obj=Img(nom,self.mots)
#             self.__dict__[methode] = mon_obj.afficher

class Montre():
    
    def __init__(self,lst_noms,lst_mots_cles):
        self.noms=lst_noms
        self.mots=lst_mots_cles
        self.creer()
    
    def creer(self):
        for nom in self.noms:

            pos_point=nom.rfind('.') # on cherche l'index du dernier point du nom, celui qui précède l'extension
            # on cherche à présent la position du dernier slash, qui finit d'indiquer le chemin de l'image
            pos_dernier_slash = -1 # pas de slash par défaut
            if '/' in nom:
                pos_dernier_slash = nom.rfind('/')
            methode=nom[pos_dernier_slash+1:pos_point]
            mon_obj=Img(nom,self.mots)
            self.__dict__[methode] = mon_obj.afficher
    

class Question_ouverte():
    def __init__(self, dic_infos, dic_mot_clefs_graph,vocab="VALIDER"):
        self.infos=dic_infos
        self.mots=list(dic_infos.keys())
        self.mots_clefs_graph=dic_mot_clefs_graph
        self.vocab=vocab

    def afficher(self):
        consigne=self.infos[self.mots[1]]
        #consigne=convertir_html(consigne)
        
        # On construit ensuite le ou les éléments graphique permettant de saisir la réponse :
        self.vbox= [] # liste de widgets
        self.zones_reponses=[] # list de dicos, de clé : 'widget', et 'rep'
        #nb_zones_saisies=len(

        for element in self.infos[self.mots[2]]:
            dic=dict()
            #leg=convertir_html(conv(element[self.mots_clefs_graph['legende']])) # on commente le 06/10
            leg = element[self.mots_clefs_graph['legende']]      
            legende=widgets.HTMLMath(value=leg)

            

            #dic['rep']=element['rep']
            dic['rep']=element[self.mots_clefs_graph['reponse']]
            
            if element[self.mots_clefs_graph['type']].lower() in ['text','texte','input']:

                dic['widget']=widgets.Text(value='',description='')
            if element[self.mots_clefs_graph['type']].lower() in ['curseur','slide']:
                m=element[self.mots_clefs_graph['min']]
                M=element[self.mots_clefs_graph['max']]
                pas=1
                if element[self.mots_clefs_graph['step']]!='':
                    pas=element[self.mots_clefs_graph['step']]
                valeur=m
                # Une valeur a-t-elle été saisie?
                if element[self.mots_clefs_graph['valeur']]!='':
                    valeur=element[self.mots_clefs_graph['valeur']]
                orient_curseur='horizontal'
                if element[self.mots_clefs_graph['orientation_curseur']].lower() in ['v','vertical','verticale','colonne','column']:
                    orient_curseur='vertical'
                    
                # S'agit-il d'un intslider ou floatslider?
                if int(m)==m and int(M)==M and int(pas)==pas:
                    dic['widget']=widgets.IntSlider(value=valeur,min=m,max=M,step=pas,orientation=orient_curseur)
                else:
                    dic['widget']=widgets.FloatSlider(value=valeur,min=m,max=M,step=pas,orientation=orient_curseur)

            
            if element[self.mots_clefs_graph['type']].lower() in ['menu','list','liste','deroulant']:
               dic['widget']=widgets.Dropdown(options=element[self.mots_clefs_graph['contenu']],description='')
            
            orientation='row'
            alignement='center'
            
            if element[self.mots_clefs_graph['orientation']].lower() in ['v','vertical','verticale','colonne','column']:
                orientation='column'
                alignement='flex-start'
            # création du conteneur, avec disposition horizontale ou verticale de legende et saisie    
            box_layout = widgets.Layout(display='inline-flex',
                    flex_flow=orientation,
                    align_items=alignement,
                    width='100%')
                
               
            h=widgets.HBox([legende,dic['widget']],layout=box_layout)
            self.vbox.append(h)
            self.zones_reponses.append(dic)
            
                

        self.bouton = widgets.Button(description=self.vocab)
        self.bouton.on_click(self.corriger)
        display(Markdown(consigne),widgets.VBox(self.vbox),self.bouton)


    def corriger(self,*args):
        valide=True
        complet=not ('' in [dic['widget'].value for dic in self.zones_reponses])

        if complet:
        
            for dic in self.zones_reponses:
                rep=dic['widget'].value
                if isinstance(rep, str):
                    rep=rep.strip()
                    rep=convertir_donnee(rep)

                # modif 13/03/2021 : rep in dic 
                #valide=valide and rep==dic['rep']
                valide=valide and rep in dic['rep']
                dic['widget'].disabled=True
                
            self.bouton.disabled=True
            if valide :
                couleur='green'
            else:
                couleur='red'

            #correction=convertir_html(self.infos[self.mots[3]])
            correction=self.infos[self.mots[3]]
          
            correction=f'<font color={couleur}> {correction}</font> <br>'
            display(Markdown(correction))

class Ouvertes():
    def __init__(self,dic_infos,lst_mots_cles,lst_mots_clefs_graph):
        self.infos=dic_infos
        self.mots=lst_mots_cles
        self.mots_clefs_graph=lst_mots_clefs_graph
        self.creer_questions()
    

    def creer_questions(self):
        for dic in self.infos:
            self.__dict__[dic[self.mots[0]]] = Question_ouverte(dic,self.mots_clefs_graph).afficher
    

    
# A ce stade, le fichier file doit déjà avoir été crée via preparation.py et les différents fichiers text
dic_infos=pickle.load(open('file', 'rb'))
if 'qcm' in dic_infos.keys():
    qcm=QCM(dic_infos['qcm'],dic_infos['mots_clefs_qcm'])

if 'correction' in dic_infos.keys():
    solution=Solution(dic_infos['correction'],dic_infos['mots_clefs_correction'])

if 'images' in dic_infos.keys():
    montre=Montre(dic_infos['images'],dic_infos['mots_clefs_images'])

if 'ouvertes' in dic_infos.keys():
    question=Ouvertes(dic_infos['ouvertes'],dic_infos['mots_clefs_ouvertes'],dic_infos['mots_clefs_graph'])




        

        

    
    
        
        

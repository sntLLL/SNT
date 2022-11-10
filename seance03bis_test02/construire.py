import sys
# On définit l'emplacement du ficier preparation :
new = "..\\preparation"
#new = "..//preparation"
sys.path.append(new)
# puis on l'importe
from prep import*
# on lance la construction du notebook
construire('seance03bis.txt')

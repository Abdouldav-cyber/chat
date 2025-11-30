import re

def nettoyer_whatsapp(infile, outfile):
    with open(infile, 'r', encoding='utf-8') as f:
        txt = f.read()
    # supprimer timestamps et numÃ©ros basiques
    txt = re.sub(r'\d{2}/\d{2}/\d{4}.*?- ', '', txt)
    txt = re.sub(r'\+?\d{1,3} ?\d{2}(?: \d{2}){3,4}', '', txt)
    txt = txt.replace('<MÃ©dias omis>', '')
    lignes = [l.strip() for l in txt.split('\\n') if len(l.strip())>10]
    with open(outfile, 'w', encoding='utf-8') as f:
        for l in lignes:
            f.write(l + '\\n')

if __name__ == '__main__':
    nettoyer_whatsapp('Discussion WhatsApp avec Professionnels des RH.txt', 'dataset/whatsapp_clean.txt')

from csv import reader


def num1():
    with open('books-en.csv', 'r') as csvfile:
            tabel=reader(csvfile, delimiter=';')
            cnt=0
            for row in tabel:
              
                if len(row[1])>30:
                    cnt+=1
    print(cnt)
#num1()

def num2():

    def author_search(tabel,author):
        cnt=0
        flag=False
        for row in tabel:
            if author in row[2]:
                cnt+=1
                flag=True
                print(cnt,"--",row)
        if not flag:
            print("Author not found :(")
    
    while True:
        author = input("Введите автора: ")
        if author=="" or author=="0":
            break
        try:
            with open('books-en.csv', 'r') as csvfile:
                tabel=reader(csvfile, delimiter=';')
                author_search(tabel,author)
        except FileNotFoundError:
             print("File not found :(")

#num2()

def num3():
    import random as rnd
    try:
        with open('books-en.csv', 'r') as csvfile:
            tabel=reader(csvfile, delimiter=';')
            file=[i for i in tabel]
            output=open("res.txt", 'w')
            for _ in range(20):
                rnd_row=rnd.randint(1,9410)
                row=file[rnd_row]
                output.write(f'{row[2]}. {row[1]} - {row[3]}\n')
            output.close()
    except FileNotFoundError:
            print("File not found :(")

#num3()
    

def num4():
    import xml.etree.ElementTree as ET
    tree = ET.parse('currency.xml')
    root = tree.getroot()

    Char_Code=[]
    Value=[]
    for elem in root.iter():
        if elem.tag=="CharCode":
            Char_Code.append(elem.text)
        if elem.tag=="Value":
            Value.append(float(elem.text.replace(",",".")))

    print(Value)
    print(Char_Code)
    
#num4()

def num4_var2():
    from xml.dom import minidom

    with open('currency.xml', 'r', encoding='cp1251') as f:
        content = f.read()
    dom = minidom.parseString(content.encode('cp1251'))

    valutes = dom.getElementsByTagName('Valute')

    for valute in valutes:
        char_code = valute.getElementsByTagName('CharCode')[0].firstChild.nodeValue
        value = valute.getElementsByTagName('Value')[0].firstChild.nodeValue
        print(f"Code: {char_code}, Value: {value}")

#num4_var2()

def additional_num1():
    with open('books-en.csv', 'r') as csvfile:
        tabel=reader(csvfile, delimiter=';')
        Publisher=[]
        for row in tabel:
            if row[-3] not in Publisher and row[-3]!="Publisher":
                Publisher.append(row[-3])
        print(len(Publisher),Publisher)

#additional_num1()

def additional_num2():

    with open('books-en.csv', 'r') as csvfile:
        tabel=reader(csvfile, delimiter=';')
        sort_tabel=[row for row in tabel]
        nontags=sorted([[int(row[-2]),row[0]] for row in sort_tabel if row[-2]!="Downloads"])
        
        tags=[nontags[i][1] for i in range(-1,-21,-1)]
        cnt=0
        for row in sort_tabel:
            
            if row[0] in tags:
                cnt+=1
                print(cnt, " -- ", row)
        
            
               
#additional_num2()
import time
import math
#num1
def flag():
    #colors
    yellow ='\u001b[43;1m'
    red ='\u001b[41;1m'
    green ='\u001b[42;1m'
    #functions
    Reset ='\u001b[0m'


    #parameters
    height = 8
    lenght = height
    line = ' '*4

    for i in range(height):
        if i < height // 3:
            print(f'{yellow}{line * (lenght)}{Reset}')
        elif height // 3 < i< height * 2 // 3:
            print(f'{green}{line * (lenght)}{Reset}')
        elif i > height * 2 // 3:
            print(f'{red}{line * (lenght)}{Reset}')
#flag()




#num2
def pattern():
    # графики функций |y|**0.5 <= x <= (|y|+1)**0.5 и const-(|y|+1)**0.5 <= x <= const-|y|**0.5 при x<=0

    Reset ='\u001b[0m'
    def draw_line(x1=0,lenght=1,x2=0): #рисуем по переданным координатам построчно
        line = ' ' * lenght
        ln=f'{" " * x1}\x1b[48;5;{220}m{line}{Reset}' 
        ln2=f'{" " * (x2-len(ln))}\x1b[48;5;{9}m{line}{Reset}'
        print(ln,ln2)


    def draw():

        net_y=10 #кол-во строк (координата  y)
        net_x=76 #сдвиг по координате x
        scale=90 #масштаб графика
        

        x1=0 
        x2=0
        lenght=0
        

        for y in range(net_y):
            x1=int(math.sqrt(scale*abs(y))) #задаем 1ю половину рисунка
            x2=-int(math.sqrt(scale*abs(y)))+net_x #задаем 2ю половину рисунка
            lenght=int(math.sqrt(scale*abs(y)+scale))-x1 #считаем ширину для каждой строчки
            draw_line(x1,lenght,x2-lenght)

    draw()
#pattern()



#num3
def function(xin,yin): #задаем размеры координатной сетки (любые разумные) 
    x0=xin*2 #для симетрии
    y0=yin*2

    lasty=len(str(-1*y0//2)) #считаем размер 1 символа 

    coordinates=[]
    '''
    for y1 in range(int(y0//2)+1): #задем точки функции со смещением в центр координат через Y
        coordinates.append([-(int(y1))+x0//2,-y1+y0])
        coordinates.append([int(y1)+x0//2,-y1+y0])
    '''
    
    for x1 in range(-1*int(xin), int(xin)+1): #задем точки функции со смещением в центр координат через X
        if  abs(int(x1))<=yin :
            coordinates.append([x1+x0//2,-1*(abs(int(x1)))+y0])
    grid = [[" "*lasty for _ in range(x0+1)] for _ in range(int(y0//2+1))] #создаем поле
    
 
    for couple in coordinates: #рисуем график
        x,y=couple[0],couple[1]
        grid[y-y0//2-1][x]=" "*(lasty//2)+"*"+" "*(lasty//2)

    for cord_y in range(len(grid)): #рисуем координатную сетку
        grid[cord_y][0]=" "*(lasty-len(str(y0//2-cord_y)))+str(y0//2-cord_y)
    for cord_x in range(x0):
        grid[int(y0//2)][cord_x]=" "*(lasty-len(str(cord_x-x0//2)))+str(cord_x-x0//2)
        

    
    grid[-1][-1]=" " 

    for i in grid: #выводим
        print(''.join(i))
#function(10,10) 


#num4
def chart():
    f=[float(i) for i in open("sequence.txt")]


    chet_num=[]
    nechet_num=[]
    for i in range(0,len(f)-1,2):
        chet_num.append(abs(f[i]))
        nechet_num.append(abs(f[i+1]))

    mod_chet=sum(chet_num)/len(chet_num)
    mod_nechet=sum(nechet_num)/len(nechet_num)



    Reset ='\u001b[0m'
    def draw_line(x,lenght=0,color=220,word=''): 
        line = ' ' * lenght
        ln=f'\x1b[48;5;{color}m{line}{Reset}'

        if lenght!=0: 
            print(f'{word} - {ln} {x}%')

    draw_line(round((mod_chet/(mod_chet+mod_nechet)*100),3),int(mod_chet*10),220,"Четные позиции  ")
    print("")
    draw_line(round((mod_nechet/(mod_chet+mod_nechet)*100),3),int(mod_nechet*10),1,"Нечетные позиции")
#chart()


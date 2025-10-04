
yellow='\u001b[43;1m'
red='\u001b[41;1m'
green='\u001b[42;1m'
Reset='\u001b[0m'



height=8
lenght=height
line=' '*4

for i in range(height):
    if i<height//3:
        print(f'{yellow}{line * (lenght)}{Reset}')
    elif height//3<i<height*2//3:
        print(f'{green}{line * (lenght)}{Reset}')
    elif i>height*2//3:
        print(f'{red}{line * (lenght)}{Reset}')
import cv2


min_area = 100        
max_area = 6000      
min_ar = 0.5 
max_ar = 2.0 
indent = 70


picture = cv2.imread('fly64.png', cv2.IMREAD_UNCHANGED)

picture_h, picture_w = picture.shape[:2]

def overlay(background, img1, x, y, alpha=1.0):
    h, w = img1.shape[:2]
    

    if x + w > background.shape[1]: w = background.shape[1] - x
    if y + h > background.shape[0]: h = background.shape[0] - y
    if x < 0 or y < 0: return background
    

    roi = background[y:y+h, x:x+w]
    

    mask = img1[:, :, 3] / 255.0 * alpha
    

    for c in range(3):
        roi[:, :, c] = roi[:, :, c] * (1 - mask) + img1[:, :, c] * mask
    
    background[y:y+h, x:x+w] = roi
    return background

def video():
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        y_size = frame.shape[0]
        x_size = frame.shape[1]

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        ret, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

        cont, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if len(cont) > 0:
            cont = sorted(cont, key=cv2.contourArea, reverse=True)
            
            for c in cont:
                area = cv2.contourArea(c)
                
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(c)
                    ar = w / float(h)
                
                    if min_ar < ar < max_ar:
                        cx = x + w // 2
                        cy = y + h // 2
                      
                        color = (0, 255, 0)  
                        cv2.circle(frame, (cx, cy), 8, color, -1)
                        cv2.putText(frame, f"Center: {cx},{cy}", (cx - 40, cy - 25), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                        x1 = cx - picture_w // 2
                        y1 = cy - picture_h // 2
                        
                        if (x1 >= 0 and x1 + picture_w <= x_size and 
                            y1 >= 0 and y1 + picture_h <= y_size):
                            frame = overlay(frame, picture, x1, y1, alpha=1.0)
                        break  

        cv2.imshow('cam', frame)
        cv2.imshow('threshold', thresh)
        
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

video()

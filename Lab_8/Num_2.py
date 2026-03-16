import cv2
import numpy as np

min_area = 100        
max_area = 6000      
min_ar = 0.5 
max_ar = 2.0 
indent = 70

overlay = cv2.imread('fly64.png')


def video():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        y_size = frame.shape[0]
        x_size = frame.shape[1]

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21,21), 0)
        ret, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

        cont, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if len(cont) > 0:
            c = max(cont, key = cv2.contourArea)
            cont = sorted(cont, key=cv2.contourArea, reverse=True)
            
            for c in cont:
                area = cv2.contourArea(c)
                
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(c)
                    ar = w / float(h)
                
                    if min_ar < ar < max_ar:
                        cx = x + w // 2
                        cy = y + h // 2

                        if cx < indent and cy < indent:
                            cv2.circle(frame, (cx, cy), 8, (255, 0, 0), -1)
                            cv2.putText(frame, f"Center: {cx},{cy}", (cx - 40, cy - 15), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                        elif x_size - cx < indent and y_size - cy < indent:
                            cv2.circle(frame, (cx, cy), 8, (0, 0, 255), -1)
                            cv2.putText(frame, f"Center: {cx},{cy}", (cx - 40, cy - 15), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        else:
                            cv2.circle(frame, (cx, cy), 8, (0, 255, 0), -1)
                            cv2.putText(frame, f"Center: {cx},{cy}", (cx - 40, cy - 15), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                        
                        break  

        cv2.imshow('cam', frame)
        cv2.imshow('threshold', thresh)
        
        if cv2.waitKey(1) & 0xFF == 27:
            break


    cap.release()


video()
cv2.waitKey(0)
cv2.destroyAllWindows()
# -*- encoding: utf-8 -*-

# import the necessary packages
import numpy as np
import cv2
import serial

def open_port():
    ser = serial.Serial('COM12', 9600)

    return ser


def close_port(port):
    port.close()


def servo1_send(port, posicion): # el servo que controla phi (plano xy)
    direccion = 1 # conector del driver al que esta conectado el motor
    port.write(bytearray([255, direccion, posicion]))

def servo2_send(port, posicion): # el servo que controla theta (respecto al eje z)
    direccion = 2 # conector del driver al que esta conectado el motor
    port.write(bytearray([255, direccion, posicion]))

def adjust_coord(handx, handy, w1, y1, n_pasos):


	# Chequeo de fronteras de control
	if handx<0:
		handx = 0
	if handy<0:
		handy = 0
	if handx > 2*w1:
		handx = 2*w1
	if handy > 2*h1:
		handy = 2*h1
	# Conversion a pasos del motor

	paso_theta = int(handy/(n_pasos*2))*n_pasos
	paso_phi = int(handx/(n_pasos*2))*n_pasos

	return paso_theta, paso_phi


# define the upper and lower boundaries of the HSV pixel
# intensities to be considered 'skin'
lower = np.array([100, 50, 50], dtype = "uint8")
upper = np.array([120, 255, 255], dtype = "uint8")

cap = cv2.VideoCapture(0)
bgSubThreshold = 50
bgModel = cv2.createBackgroundSubtractorMOG2(0, bgSubThreshold)
last_paso_theta , last_paso_phi = 145, 192 #centro
call = 0




# Datos de motores calibrados
phi_0 =228
phi_180 = 36
phi_resol = (phi_180-phi_0+1)/180.0

theta_0 = 245
theta_90 = 131
theta_max = 100  # minimo angulo sin que el motor choque con la base
theta_resol = (theta_90-theta_0 +1)/90.0

port = open_port()
servo1_send(port, phi_180 )
while True:



	grabbed, frame = cap.read()
	frame = cv2.flip(frame, 1)
	w , h = frame.shape[1], frame.shape[0]
	centerx = int(round(w/2))
	centery = int(round(h/2))

	#print("W= {}, H={}".format(w, h))


	# if we are viewing a video and we did not grab a
	# frame, then we have reached the end of the video

	# resize the frame, convert it to the HSV color space,
	# and determine the HSV pixel intensities that fall into
	# the speicifed upper and lower boundaries
	#frame = imutils.resize(frame, width = 400)
	converted = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	skinMask = cv2.inRange(converted, lower, upper)

	# apply a series of erosions and dilations to the mask
	# using an elliptical kernel
	# kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
	# skinMask = cv2.erode(skinMask, kernel, iterations = 2)
	# skinMask = cv2.dilate(skinMask, kernel, iterations = 2)
	kernel = np.ones((5,5), np.uint8)

	# skinMask = cv2.morphologyEx(skinMask, cv2.MORPH_OPEN, kernel)
	#skinMask = cv2.erode(skinMask, kernel, iterations=1)
	# blur the mask to help remove noise, then apply the
	# mask to the frame
	#skinMask = cv2.GaussianBlur(skinMask, (3, 3), 0)
	skinMask= cv2.medianBlur(skinMask, 9)

	img = frame
	thresh1 = skinMask

	im3, contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	drawing = np.zeros(img.shape, np.uint8)
	max_area = 0
	ci = 0
	if len(contours)>0:
		for i in range(len(contours)):
			cnt = contours[i]
			area = cv2.contourArea(cnt)
			if (area > max_area):
				max_area = area
				ci = i
		cnt = contours[ci]
		hull = cv2.convexHull(cnt)
		moments = cv2.moments(cnt)
		if moments['m00'] != 0:
			cx = int(moments['m10'] / moments['m00'])  # cx = M10/M00
			cy = int(moments['m01'] / moments['m00'])  # cy = M01/M00

		centr = (cx, cy)

		cv2.circle(img, centr, 5, [0, 0, 255], 2)
		cv2.drawContours(drawing, [cnt], 0, (0, 255, 0), 2)
		cv2.drawContours(drawing, [hull], 0, (0, 0, 255), 2)

		cnt = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
		hull = cv2.convexHull(cnt, returnPoints=False)

		if (1):
			defects = cv2.convexityDefects(cnt, hull)
			mind = 0
			maxd = 0
			if type(defects)!= type(None):
				for i in range(defects.shape[0]):
					s, e, f, d = defects[i, 0]
					start = tuple(cnt[s][0])
					end = tuple(cnt[e][0])
					far = tuple(cnt[f][0])
					dist = cv2.pointPolygonTest(cnt, centr, True)
					cv2.line(img, start, end, [0, 255, 0], 2)

					cv2.circle(img, far, 5, [0, 0, 255], -1)
			#print(i)
			i = 0
		w1, h1 = 192, 145, #int(round(7/20*w)), int(round(7/20*h))
		cv2.rectangle(img, (centerx-w1, centery-h1), (centerx+w1, centery+h1), (255,0, 0), 3)
		handx = centerx+w1-cx
		handy = cy-(centery-h1)
		paso_theta, paso_phi = adjust_coord(handx, handy,w1, h1, 4)
		# No quemar los motores: permitir solo pasos pequeños en caso de fallo en deteccion de mano
		if call == 0:
			call = 1
			last_paso_theta, last_paso_phi = paso_theta, last_paso_phi

		if np.abs(paso_theta-last_paso_theta)>4:
			paso_theta = last_paso_theta
		else:
			servo2_send(port, -paso_theta+theta_0)
			print("theta {}, phi {}".format(paso_theta, paso_phi))

		if np.abs(paso_phi-last_paso_phi)>4:
			paso_phi = last_paso_phi
		else:
			servo1_send(port, -paso_phi+phi_0)
			print("theta {}, phi {}".format(paso_theta*90/145, paso_phi*180/192))

		last_paso_theta, last_paso_phi = paso_theta, paso_phi



	# show the skin in the image along with the mask0
	cv2.imshow("Draw", drawing)
	cv2.imshow("Image", frame)
	cv2.imshow("MOG2", skinMask)
	# if the 'q' key is pressed, stop the loop
	if cv2.waitKey(1) & 0xFF == ord("q"):
		close_port(port)
		break

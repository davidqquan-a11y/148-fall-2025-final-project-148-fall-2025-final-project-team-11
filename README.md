# Autonomous Targeting System (ATS)
## MAE 148 Final Project - Team 11 Fall 2025
<img width="1371" height="321" alt="JSOElogo" src="https://github.com/user-attachments/assets/406e5140-232f-4706-923a-b325d50a7a29" />

![IMG_7566](https://github.com/user-attachments/assets/3a2fe580-732b-4d61-b3eb-991e242663ce)

## Team Members
- Matthew Hwang - Mechanical Engineering
- Andrea Galliano - Aerospace Engineering
- David Quan - Mechanical Engineering
- Jose Umana -  Electrical Engineering

## Purpose
The goal of this project is to develop a targeting system using OpenCV that scans, labels, and locks onto targets of interest, then allows for manual selection of a target. 
A two degree-of-freedom (DOF) gimbal mechanism with PID control allows for the accurate following of selected targets to keep them in frame at all times, constantly ready to fire a rocket engine.

## What We Delievered
- OpenCV with OAK-D camera for objection detection and tracking
- Dual servo motor control for object following
- Target selection system

## Nice to Haves
- Implementing created rockets engines  
- LIDAR and/or OAK-D camera depth mechanisms to access objects as potential targets from far away 
- Adding an autonomous driving feature to allow the ATS to access and be within accurate firing distance of objects out of range
- Integration of prototyped ignition system for firing rocket engines

## Demonstration (Video)




https://github.com/user-attachments/assets/16eb97ce-2f67-4ed8-98f5-33ec005cf2fc
## Smart-Cam Feature
- A feature that was added to increase efficiency and effectiveness of our project was our Smart-Cam implementation. Smart-Cam enables our PID ontrolled gimbal to move the camera in response to a moving target. The speeds of the tracking can be adjusted within the Python scripts. Additionally, Smart-Cam is able to recall the direction a target was before it left the field of view of the camera. By recalling this information, it is able to make smart decisions such as automatically scanning for the object again in the direction of where the target has last left.

## Mode Explanations
- Mode 1 [Scan Surrounding]: Gimbal pans 180 degreees horizontally to look for targets. If a potential target is found, the system will take 3 seconds to the object as a target in order to avoid false detections. After a target is registered, the target will have a number ID, their stationary position is registered, and their hitbox will turn yellow.
  
- Mode 2 [Choose Target]: Once a target is registered from mode 1, the user can manually lock on a target based on their remembered position. Their target ID can be pressed and the gimbal will instantly center to camera towards the desired target.

- Mode 3 [Fire Rocket]: Before the fire command is used, a target should be chosen from mode 2. When the fire command is pressed, a 5 second countdown will begin on the top right corner. Once the countdown reaches 0, their hitbox turns red. This mode represents when our created ignition system would have activated to fire our rocket engine at the desired target.

## CAD Model Assemblies
- Final Car Assembly
<img width="621" height="491" alt="FinalAssemblySetup" src="https://github.com/user-attachments/assets/223e0eef-5dad-4fe7-b09d-e404ce696717" />

- Initial Car Assembly
<img width="827" height="584" alt="EarlyQuarterSetup" src="https://github.com/user-attachments/assets/3c7b90da-147a-4233-a5c1-3a7fbd690cf8" />

## Challenges
- On the softtware side, some challenges we faced were implementing our RoboFlow model to detect our targets (waterbottles) accurately. Because of the quick timeline of this course, we had only trained our models with around one hundred photos. While this model was able to detect waterbottles, it occasionally detected a watch, laptop screen, or bottle-shaped objects for a split second due to the lack of training. Although this was seemingly fine, this issue quickly became a problem when we tried to associate a target with a position, resulting in these objects being remembered as targets. The first solution that came to our minds were to develop a better model. While it would take a substantial amonut of time to add and re-train our model, it would result in targets detected being more accurate. However, an ingenous solution that we arrived at was the 3 second lock-on duration, where objects that were not water bottles could appear quickly, but would not be identified as an object due to being undetected as targets a short moment after.

- On the hardware side, one challenge that was faced was the design of the gimbal's servo to servo connectors. During the designing process of the mount, the mounting holes' geometry was simply projected onto the new mount. The issue with this process was that 3D fillaments are generally weak and the geometry of the holes allowed for a high stress concentration on one of its side, leaving the 3D printed connectors to snap very easily. The solution to this issue was to create a hole that had support on both sides and extrude slightly more on the sides for additional support, resulting in the servo to servo connector being quite resilient. 

## Hardware Highlights

| Part         | CAD Design |
|-------------|-----------|
| Adjustable Camera Mount |<img width="545" height="436" alt="Screenshot 2025-12-13 at 5 35 42 PM" src="https://github.com/user-attachments/assets/5734923e-6ba5-4278-931e-4d4078264ca6" />|
| Interchangeable Camera Mount Arm Lengths |<img width="363" height="422" alt="Screenshot 2025-12-13 at 5 37 57 PM" src="https://github.com/user-attachments/assets/d98ec355-16e5-4737-a554-a2ab3b9a6f64" />|
| Adjustable Camera Mount Base |<img width="575" height="396" alt="Screenshot 2025-12-13 at 5 39 02 PM" src="https://github.com/user-attachments/assets/1ad46079-766e-4b5d-9ba4-69bf05af3c5e" />|
| Gimbal Base | <img width="553" height="468" alt="Screenshot 2025-12-13 at 5 32 34 PM" src="https://github.com/user-attachments/assets/a92b7a30-d7df-42e8-b302-735a6af822b7" />|
| Gimbal Servo to Servo Connectors |<img width="426" height="388" alt="Screenshot 2025-12-13 at 5 33 54 PM" src="https://github.com/user-attachments/assets/4468494d-6b1c-42cd-a146-dc42c4f554dc" />|
| Gimbal Arm & Camera Mount|<img width="579" height="534" alt="Screenshot 2025-12-13 at 5 34 29 PM" src="https://github.com/user-attachments/assets/491fe772-8ed3-48c9-96fa-414a245f629c" />|
| Universal Mounting Plate |<img width="866" height="512" alt="Screenshot 2025-12-13 at 6 26 37 PM" src="https://github.com/user-attachments/assets/1d2d927b-80d8-4b86-ad2c-dda433aa1175" />|

## Ignition Systems Schematic
<img width="593" height="396" alt="Ignition system" src="https://github.com/user-attachments/assets/844c7042-6406-4b19-8649-8dae65aab2ba" />

## Electric Diagram
<img width="727" height="414" alt="electrical diagram" src="https://github.com/user-attachments/assets/838ac5c9-671a-4e54-a26b-feed91f9b829" />


## Early Quarter Achievements
- Donkey Car Autonomous Laps:
- Donkey Car GPS Laps: 

## Acknowledgements
Special thanks to Professor Silberman, our (very overworked) TA's Aryan & Winston, and the countless peers who have offered us helpful inisght, motivation, and good company throughout the countless hours and late nights spent on our autonomous car.

## Contact Information
| Team Member    | Email | 
|-------------|-----------|
| Andrea Galliano | andrea.galliano@tum.de |
| David Quan | davidqquan@gmail.com |
| Jose Umana | jaumana@ucsd.edu |
| Matthew Hwang | matthew.hwang97@gmail.com |

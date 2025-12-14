# Autonomous Targeting System
## MAE 148 Final Project
### Team 11 Fall 2025

## Team Members
- Matthew Hwang - Mechanical Engineering
- Andrea Galliano - Aerospace Engineering
- David Quan - Mechanical Engineering
- Jose Umana -  Electrical Engineering 

(insert an image of our car)
(insert image of JSOE and UCSD logos somewhere as well)

## Abstract
The goal of this project is to develop a targeting system using OpenCV that scans, labels, and locks onto targets of interest, then allows for manual selection of a target. 
A two degree-of-freedom (DOF) gimbal mechanism accurately follows the selected target to keep it in frame at all times, constantly ready to fire a rocket engine.

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

## Mode Explanations
- Scanning: Servo pans 180 degreees horizontally to look for targets. System locks onto an object for 3 seconds to identify it as a target, then creates a yellow hitbox around it.
- Choose: User input determines which target will be targeted (among many targets detected by camera from scanning mode).
- Fire: 5 second cooldown, target is locked, hitbox turns red. Theroetically, after 5 seconds the ignition system is activated and a rocket engine fires at target. 

## CAD Model Assemblies
Final Car Assembly
<img width="621" height="491" alt="FinalAssemblySetup" src="https://github.com/user-attachments/assets/223e0eef-5dad-4fe7-b09d-e404ce696717" />

Initial Car Assembly
<img width="827" height="584" alt="EarlyQuarterSetup" src="https://github.com/user-attachments/assets/3c7b90da-147a-4233-a5c1-3a7fbd690cf8" />

## Ignition Systems Schematic
<img width="593" height="396" alt="Ignition system" src="https://github.com/user-attachments/assets/844c7042-6406-4b19-8649-8dae65aab2ba" />

## Electric Diagram
<img width="727" height="414" alt="electrical diagram" src="https://github.com/user-attachments/assets/838ac5c9-671a-4e54-a26b-feed91f9b829" />
al 

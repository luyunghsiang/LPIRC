# LPIRC
Low-Power Image Recognition Challenge

If you have any questions or suggestions, please send email to lpirc@ecn.purdue.edu. Thank you.

## Requirements
1. Python v2.7.3
2. Flask - Microframework for Python

## Relevant Files

## Usage

## Referee Program
Referee program performs the following operations:

- Communicate with competing client devices and log results.
- Communicate with power meter and log power readings.
- Perform post processing to declare winner.

### Server
#### Web framework
A Python microframework - Flask is used to implement the server functions. The framework
provides the 
#### Configure host server
#### Perform client login/authentication
#### Send test images
#### Log test results

### Power Meter
### Matlab Post-Processing

### Sample Client
Sample Client performs the following operations:

- POSTS username and password to start a session with the server
- POSTS the bounding box information to the server.
- Requests for the images and stores locally.

Additional Notes: 

-Sample Client uses a file "golden_output.csv" which contains list of 
bounding box information corresponding to the test images in the server.
This file is being used to simulate the recognition program the
participant will have during the competition. This is just sample data
to check if the interface with the server is working properly.
The participant should generate this data by running the recognition software
on the images sent by the server. 

-client/temp is temporary directory.
Images are buffered in this directory, and removed immediately after that.

## References

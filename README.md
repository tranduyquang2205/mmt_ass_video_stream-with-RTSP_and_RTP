# mmt_streaming_video_with_RTSP_and_RTP
Implementing a streaming video server and client that communicate using the Real-Time Streaming Protocol (RTSP) and send data using the Real-time Transfer Protocol (RTP).

Running the code: \
First, we need to start the server: \
 #python Server.py server_port\
 (The standard RTSP port is 554, but you will need to choose a port number greater than 1024.)\
Then, start the client with the command:\
 #python ClientLauncher.py server_host server_port RTP_port video_file \
, where server_host is the name of the machine where the server is running, server_port is the port
where the server is listening on, RTP_port is the port where the RTP packets are received, and video_file is
the name of the video file you want to request (we have provided one example file movie.Mjpeg).

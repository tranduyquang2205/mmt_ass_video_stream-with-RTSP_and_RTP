Open a terminal:
    python Server.py 1025

Open another terminal:
    python ClientLauncher.py 127.0.0.1 1025 5008 video.mjpeg
    
@ Client.py
    # SETUP function
    # PLAY function
    # PAUSE function
    # TEARDOWN function
@ RtpPacket.py
    # Set the RTP-version filed(V) = 2
    # Set padding(P), extension(X), # of contributing sources(CC), and marker(M) fields => all to 0
    # Set payload type field(PT). we use MJPEG type, type number is 26
    # Set sequence number.(frameNbr argument)
    # Set timestamp (via Python time module)
    # Set source identifier(SSRC)(identifies the server,pick an ID you like)
    # We have no other contributing sources(field CC == 0), the CSRC-field does not exist. The packet header is 12 bytes

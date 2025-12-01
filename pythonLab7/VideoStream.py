class VideoStream:
    """Reads frames from a Motion JPEG file."""
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'rb')
        self.frameNum = 0

    def nextFrame(self):
        """Return the next frame in the video stream.
           We assume each frame is a JPEG image terminated by 0xFFD9."""
        data = b''
        while True:
            byte = self.file.read(1)
            if not byte:
                # End of file
                return None
            data += byte
            if data[-2:] == b'\xff\xd9':  # end of JPEG marker
                break

        self.frameNum += 1
        return data

    def frameNbr(self):
        return self.frameNum

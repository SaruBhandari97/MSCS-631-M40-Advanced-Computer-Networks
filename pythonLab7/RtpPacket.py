class RtpPacket:
    HEADER_SIZE = 12

    def __init__(self):
        self.header = bytearray()
        self.payload = bytes()

    def encode(self, version, padding, extension, cc,
               seqnum, marker, pt, ssrc, payload):
        """Encode the RTP packet with header fields and payload."""
        self.header = bytearray(self.HEADER_SIZE)

        # Byte 0: V P X CC
        self.header[0] = (version << 6) | (padding << 5) | (extension << 4) | (cc & 0x0F)

        # Byte 1: M PT
        self.header[1] = (marker << 7) | (pt & 0x7F)

        # Bytes 2-3: sequence number
        self.header[2] = (seqnum >> 8) & 0xFF
        self.header[3] = seqnum & 0xFF

        # Bytes 4-7: timestamp (for this lab we don't really use it – set to seqnum)
        timestamp = seqnum
        self.header[4] = (timestamp >> 24) & 0xFF
        self.header[5] = (timestamp >> 16) & 0xFF
        self.header[6] = (timestamp >> 8) & 0xFF
        self.header[7] = timestamp & 0xFF

        # Bytes 8-11: SSRC
        self.header[8] = (ssrc >> 24) & 0xFF
        self.header[9] = (ssrc >> 16) & 0xFF
        self.header[10] = (ssrc >> 8) & 0xFF
        self.header[11] = ssrc & 0xFF

        # payload
        self.payload = payload

    def decode(self, byteStream):
        """Decode the RTP packet."""
        self.header = bytearray(byteStream[:self.HEADER_SIZE])
        self.payload = byteStream[self.HEADER_SIZE:]

    def version(self):
        return (self.header[0] >> 6) & 0x03

    def seqNum(self):
        return (self.header[2] << 8) | self.header[3]

    def timestamp(self):
        return (self.header[4] << 24) | (self.header[5] << 16) | (self.header[6] << 8) | self.header[7]

    def payloadType(self):
        return self.header[1] & 0x7F

    def getPayload(self):
        return self.payload

    def getPacket(self):
        return self.header + self.payload

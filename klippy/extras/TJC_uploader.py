
import time, struct, math

class TJCUpdater:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')

        self.printer.register_event_handler('klippy:ready', self.handle_ready)
        
        bridge = config.get('serial_bridge')
        self.serial_bridge = self.printer.lookup_object('serial_bridge %s' %(bridge))
        self.serial_bridge.register_callback(self.handleResponse)

        self.serial_response = b''

        self.gcode.register_command("UPDATE_DISPLAY", self.cmd_UPDATE_DISPLAY, desc="Upload a new TFT firmware file to the display")

    def send(self, str):
        self.serial_bridge.send_text(str)

    def send_bytes(self, data):
        self.serial_bridge.send_serial(data)

    def handle_ready(self):
        self.send_bytes(b"DRAKJHSUYDGBNCJHGJKSHBDN\xff\xff\xffconnect\xff\xff\xff\xff\xffconnect\xff\xff\xff")

    def handleResponse(self, data):
        self.serial_response += bytearray(data)

    def getFileSizee(self, filepath):
        with open(filepath, 'rb') as f:
            f.seek(0x3c)
            rawSize = f.read(struct.calcsize("<I"))
        fileSize = struct.unpack("<I", rawSize)[0]
        return fileSize


    def cmd_UPDATE_DISPLAY(self, gcmd):
        path = gcmd.get('FILEPATH')

        self.send('bs=42')
        self.send('dims=100')
        self.send('sleep=0')

        filesize = self.getFileSizee(path)

        cmd = 'whmi-wris'
        self.send(f'whmi-wris {filesize},115200,1')

        time.sleep(2)

        self.serial_response = bytearray()

        blockSize = 4096
        remainingBlocks = math.ceil(filesize / blockSize)
        blocksSent, lastProgress, lastEta = 0, 0, 0
        with open(path, 'rb') as f:
            while remainingBlocks:
                self.send_bytes(f.read(blockSize))
                remainingBlocks -= 1
                blocksSent += 1

                proceed = hex(self.serial_response.pop(0))[2:]
                if proceed == '08':
                    offset = self.serial_response[:4]
                    self.serial_response = self.serial_response[4:]
                    if len(offset) != 4:
                        raise Exception("Incomplete offset for skip command")
                    offset = struct.unpack("<I", offset)[0]
                    if (offset):
                        jumpSize = offset - f.tell()
                        f.seek(offset)
                        remainingBlocks = math.ceil((filesize - offset) / blockSize)



            


    


def load_config(config):
    return TJCUpdater(config)
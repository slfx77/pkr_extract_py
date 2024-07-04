FILE_COMPRESSED = 0x00000002
FILE_UNCOMPRESSED = 0xFFFFFFFE


class PKR3File:
    def __init__(self, magic, dir_offset):
        self.magic = magic
        self.dir_offset = dir_offset


class PKRDirHeader:
    def __init__(self, unk, num_dirs, num_files):
        self.unk = unk
        self.num_dirs = num_dirs
        self.num_files = num_files


class PKRDir:
    def __init__(self, name, unk, num_files):
        self.name = name
        self.unk = unk
        self.num_files = num_files


class PKRFile:
    def __init__(self, name, crc, compressed, file_offset, uncompressed_size, compressed_size):
        self.name = name
        self.crc = crc
        self.compressed = compressed
        self.file_offset = file_offset
        self.uncompressed_size = uncompressed_size
        self.compressed_size = compressed_size

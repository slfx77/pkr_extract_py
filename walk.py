import os
import struct

from pkr_header import PKR3File, PKRDir, PKRDirHeader
from extract import extract_dir


def setup_pkr_dirs(fp):
    pkr = get_file_header(fp)
    if not pkr:
        return None, None  # Return None for both pkr_dirs and pkr_dir_header if the file header is invalid

    pkr_dir_header = get_pkr_dirs_header(fp, pkr)
    if not pkr_dir_header:
        print("Failed to get directory headers")
        return None, None

    try:
        # Prepare to store directory data
        pkr_dirs = [PKRDir("", 0, 0) for _ in range(pkr_dir_header.num_dirs)]  # Placeholder for actual directory data
    except Exception as e:
        print(f"Couldn't allocate space for the dirs: {str(e)}")
        return None, None

    if not load_directories(fp, pkr_dirs, pkr_dir_header):
        return None, None

    return pkr_dirs, pkr_dir_header


def get_file_header(fp):
    # Define the format string for struct.unpack to read the PKR3File structure
    # Assume PKR3File has a uint32 for magic and dirOffset (magic is 4-byte ASCII string)
    try:
        # Read binary data from file
        data = fp.read(struct.calcsize("4sI"))  # '4s' for 4-byte string, 'I' for unsigned int
        if not data:
            print("Error reading the file.")
            return None

        # Unpack data according to the specified format
        magic_bytes, dir_offset = struct.unpack("4sI", data)

        # Decode and strip null characters from the magic_bytes to compare with the magic string
        magic_str = magic_bytes.decode("ascii").strip("\x00")
        if magic_str != "PKR3":
            print("Invalid PKR3 Header.")
            return None

        # Return an instance of PKR3File if successful
        return PKR3File(magic_str, dir_offset)
    except Exception as e:
        print(f"Failed to read file header: {str(e)}")
        return None


def get_pkr_dirs_header(fp, pkr):
    # Move the file pointer to the directory offset
    fp.seek(pkr.dir_offset, 0)  # `0` denotes `SEEK_SET` in Python

    # Define the format string to read the PKRDirHeader structure
    # Assuming PKRDirHeader has three uint32_t: unk, numDirs, numFiles
    try:
        # Read the binary data from file
        data = fp.read(struct.calcsize("III"))  # 'III' for three unsigned ints
        if not data:
            print("Couldn't get the dirs of PKR")
            return None

        # Unpack data according to the specified format
        unk, num_dirs, num_files = struct.unpack("III", data)

        # Print the directory and file information
        print(f"There are {num_dirs} dirs and {num_files} files")

        # Return an instance of PKRDirHeader if successful
        return PKRDirHeader(unk, num_dirs, num_files)
    except Exception as e:
        print(f"Failed to read directory header: {str(e)}")
        return None


def load_directories(fp, pkr_dirs, pkr_dir_header):
    # Define the format string for reading each PKRDir structure
    # Assuming PKRDir has a 32-byte name, a uint32 unk, and a uint32 numFiles
    dir_format = "32sII"
    dir_size = struct.calcsize(dir_format)

    # Read the binary data for all directories at once
    data = fp.read(dir_size * pkr_dir_header.num_dirs)
    if len(data) != dir_size * pkr_dir_header.num_dirs:
        print(f"Could only read {len(data) // dir_size} dirs.")
        return False

    # Unpack and store each directory's information into pkr_dirs list
    for i in range(pkr_dir_header.num_dirs):
        offset = i * dir_size
        name_bytes, unk, num_files = struct.unpack_from(dir_format, data, offset)
        name = name_bytes.decode("ascii").strip("\x00")  # Decode and strip null characters from the name
        pkr_dirs[i].name = name
        pkr_dirs[i].unk = unk
        pkr_dirs[i].num_files = num_files
        print(f"{name} has {num_files} files")

    return True


def extract_dirs(fp, pkr_dirs, pkr_dir_header):
    # Create a directory to store extracted files if it does not exist
    try:
        os.makedirs("extracted", exist_ok=True)
    except Exception as e:
        print(f"An error occurred creating extracted dir: {str(e)}")
        return

    # Loop over each directory in pkr_dirs to extract it
    for i in range(pkr_dir_header.num_dirs):
        dir_name = pkr_dirs[i].name
        print(f"Extracting {dir_name}")

        if not extract_dir(fp, pkr_dirs[i]):
            print("An error occurred")
            return

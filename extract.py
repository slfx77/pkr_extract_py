import errno
import os
import struct
import zlib

from pkr_header import FILE_COMPRESSED, FILE_UNCOMPRESSED, PKRFile

EXTRACT_BUF_SIZE = 0xFFFF


def get_pkr_file(fp, file):
    # Define the format string to read the PKRFile structure from the file
    # Assuming PKRFile has the following structure: name (32 bytes), crc (uint32), compressed (uint32), file_offset (uint32), uncompressed_size (uint32), compressed_size (uint32)
    file_format = "32sIIIII"

    # Calculate the size of the PKRFile structure based on the format string
    size = struct.calcsize(file_format)

    # Read binary data from file
    data = fp.read(size)

    if len(data) == size:
        # Unpack the data according to the specified format
        file.name, file.crc, file.compressed, file.file_offset, file.uncompressed_size, file.compressed_size = struct.unpack(file_format, data)
        return True
    else:
        # If data read does not match the size expected, return False indicating failure
        return False


def extract_dir(fp, cur_dir):
    # Construct the path where files will be extracted
    extracted_path = os.path.join("extracted", cur_dir.name)

    # Print the directory being extracted
    print(f"Extracting {cur_dir.name}")

    # Try creating the directory, handle errors appropriately
    try:
        os.makedirs(extracted_path, exist_ok=True)
    except OSError as e:
        if e.errno != errno.EEXIST:
            print(f"An error occurred while creating the directory: {os.strerror(e.errno)} ({e.errno:08X})")
            return False
        else:
            print("The directory does not seem to be created yet... Creating")

    # Iterate over files in the current directory
    for _ in range(cur_dir.num_files):
        extracted = PKRFile("", 0, 0, 0, 0, 0)  # Placeholder for actual file retrieval logic
        if not get_pkr_file(fp, extracted):
            print("Error reading file...")
            return False

        # Handle the file based on its compression flag
        if extracted.compressed == FILE_COMPRESSED:
            if not extract_compressed(fp, extracted, extracted_path):
                return False
        elif extracted.compressed == FILE_UNCOMPRESSED:
            if not extract_uncompressed(fp, extracted, extracted_path):
                return False
        else:
            print(f"Unknown compression type: {extracted.compressed:08X}... Quitting")
            return False

    return True


def extract_uncompressed(fp, file, path):
    # Check if the file has already been extracted
    if check_already_extracted(file, path):
        return True

    # Get the file data from the archive or source
    if not get_file(fp, file):
        return False

    # Write the data to disk
    return write_file_to_disk(file, file.data, path)


def extract_compressed(fp, file, path):
    # Check if the file has already been extracted
    if check_already_extracted(file, path):
        return True

    # Get the file data from the archive or source
    if not get_file(fp, file):
        return False

    # Decompress the file data
    decompressed_data = decompress_file(file)
    if decompressed_data is None:
        return False

    # Write the decompressed data to disk
    return write_file_to_disk(file, decompressed_data, path)


def get_file(fp, file):
    try:
        # Save original offset so it can keep reading the files
        original_fp = fp.tell()

        # Seek to the file offset
        fp.seek(file.file_offset)

        # Determine the file size
        file_size = file.uncompressed_size if file.compressed == FILE_UNCOMPRESSED else file.compressed_size

        # Choose the buffer based on the file size
        if file_size > EXTRACT_BUF_SIZE:
            aux_extract_buf = bytearray(file_size)
            cur_ext_buf = aux_extract_buf
        else:
            cur_ext_buf = bytearray(EXTRACT_BUF_SIZE)

        # Read the file data into the buffer
        data = fp.read(file_size)
        if len(data) != file_size:
            print(f"Could not read file {file.name}")
            return False

        # Store the data in the appropriate buffer
        cur_ext_buf[:file_size] = data

        # Rewind to the original file offset
        fp.seek(original_fp)

        # Store the buffer in the file object for further use
        file.data = cur_ext_buf[:file_size]

        return True
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def write_file_to_disk(file, data, path):
    try:
        # Construct the full file path
        full_path = os.path.join(path, file.name.decode("utf-8").strip("\x00"))

        # Open the file for writing in binary mode
        with open(full_path, "wb") as out:
            # CRC Check
            if not calculate_extracted_crc(file, data):
                print(f"Invalid CRC for {file.name}")
                return False

            # Write the data to the file
            out.write(data)

        return True
    except IOError as e:
        print(f"Could not create the extracted file <{full_path}>\n{str(e)}")
        return False


def check_already_extracted(file, path):
    # Construct the full file path using the directory path and the file name
    full_path = os.path.join(path, file.name.decode("utf-8").strip("\x00"))

    # Check if the file exists at the specified path
    if os.path.isfile(full_path):
        return True
    return False


def decompress_file(file):
    try:
        # Decompress the data
        final_size = file.uncompressed_size
        decompressed_data = zlib.decompress(file.data, bufsize=file.uncompressed_size)

        if len(decompressed_data) != final_size:
            print("Error decompressing the file :(")
            return None

        return decompressed_data
    except MemoryError:
        print("Could not allocate space for output buffer")
        return None
    except zlib.error as e:
        print(f"Error decompressing the file: {str(e)}")
        return None


def calculate_extracted_crc(file, data):
    # Calculate the CRC32 checksum of the extracted data
    crc = zlib.crc32(data) & 0xFFFFFFFF  # Ensure unsigned 32-bit result
    return crc == file.crc

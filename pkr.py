import sys
from walk import setup_pkr_dirs, extract_dirs


def main():
    if len(sys.argv) != 2:
        print("Please specify file name")
        return 1

    file_name = sys.argv[1]
    try:
        with open(file_name, "rb") as fp:
            pkr_dirs, pkr_dir_header = setup_pkr_dirs(fp)
            if pkr_dirs and pkr_dir_header:
                extract_dirs(fp, pkr_dirs, pkr_dir_header)
            else:
                return 1  # Return an error if the setup was not successful
    except FileNotFoundError:
        print(f"Couldn't open file {file_name}")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())

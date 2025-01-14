from osxphotos import PhotosDB

def inspect_albums_structure():
    # Initialize the PhotosDB
    photosdb = PhotosDB()

    # Retrieve albums as a dictionary
    albums_dict = photosdb.albums_as_dict
    print("Albums available:")

    # Print the type and contents of each key-value pair in the dictionary
    for album_title in albums_dict.items():
        print(f"Album Title: {album_title}")
        print("---")

if __name__ == "__main__":
    inspect_albums_structure()

#!/usr/bin/env python3

from cryptography.fernet import Fernet
from Utility.FileUtility import read_from_file, write_content_to_file

from Utility.Logging.ApiToolLogging import ApiToolLog


class crypto:
    def create_key(self, path):
        """
        Generates a key and save it into a file
        """
        key = Fernet.generate_key()
        write_content_to_file(path, key, "wb")
        return key

    def load_key(self, path):
        """
        Loads the key from the specified file
        """
        return open(path, "rb").read()

    def encryptFile(self, filename, key):
        """
        Given a filename (str) and key (bytes), it encrypts the file and write it
        """
        f = Fernet(key)
        # read all file data
        file_data = read_from_file(filename, "rb")
        # encrypt data
        encrypted_data = f.encrypt(file_data)
        # write the encrypted file
        write_content_to_file(filename, encrypted_data, "wb")

    def encryptToFile(self, file_data, filename, key):
        """
        Given file data and key (bytes), it encrypts the file and write it to filename (str)
        """
        f = Fernet(key)
        # encrypt data
        if type(file_data) != bytes:
            file_data = bytes(file_data)
        encrypted_data = f.encrypt(file_data)
        # write the encrypted file
        write_content_to_file(filename, encrypted_data, "wb")

    def isFileDecrypt(self, filename, key):
        f = Fernet(key)
        # read the encrypted data
        encrypted_data = read_from_file(filename, "rb")

        if encrypted_data:
            try:
                # decrypt data
                f.decrypt(encrypted_data)
                return False
            except:
                pass
        return True

    def isFileEncrypt(self, filename, key):
        f = Fernet(key)
        # read the encrypted data
        encrypted_data = read_from_file(filename, "rb")

        if encrypted_data:
            try:
                # decrypt data
                f.decrypt(encrypted_data)
                return True
            except:
                pass
        return False

    def decrypt(self, filename, key, writeDecrypt=False):
        """
        Given a filename (str) and key (bytes), it decrypts the file and write it
        """
        f = Fernet(key)
        # read the encrypted data
        encrypted_data = read_from_file(filename, "rb")

        decrypted_data = None
        try:
            # decrypt data
            decrypted_data = f.decrypt(encrypted_data)
        except Exception as e:
            ApiToolLog().LogError(e)

        if writeDecrypt and decrypted_data:
            # write the original file
            write_content_to_file(filename, decrypted_data, "wb")

        return decrypted_data

#!/usr/bin/env python3

from cryptography.fernet import Fernet
from Utility.Logging.ApiToolLogging import ApiToolLog


class crypto:
    def create_key(self, path):
        """
        Generates a key and save it into a file
        """
        key = Fernet.generate_key()
        with open(path, "wb") as key_file:
            key_file.write(key)
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
        with open(filename, "rb") as file:
            # read all file data
            file_data = file.read()
        # encrypt data
        encrypted_data = f.encrypt(file_data)
        # write the encrypted file
        with open(filename, "wb") as file:
            file.write(encrypted_data)

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
        with open(filename, "wb") as file:
            file.write(encrypted_data)

    def isFileDecrypt(self, filename, key):
        f = Fernet(key)
        encrypted_data = None
        with open(filename, "rb") as file:
            # read the encrypted data
            encrypted_data = file.read()

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
        encrypted_data = None
        with open(filename, "rb") as file:
            # read the encrypted data
            encrypted_data = file.read()

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
        with open(filename, "rb") as file:
            # read the encrypted data
            encrypted_data = file.read()

        decrypted_data = None
        try:
            # decrypt data
            decrypted_data = f.decrypt(encrypted_data)
        except Exception as e:
            ApiToolLog().LogError(e)

        if writeDecrypt and decrypted_data:
            # write the original file
            with open(filename, "wb") as file:
                file.write(decrypted_data)

        return decrypted_data

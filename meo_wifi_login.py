#!/usr/bin/python

import os
import sys
import getopt
import getpass

import requests
import json

import hashlib, base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend

# Pad a message to a 128 bit multiple using PKCS7
def padding(message):
    padder = PKCS7(128).padder()
    return padder.update(message.encode("utf8")) + padder.finalize()

# Encrypt the password like their Javascript code does
def encrypt_password(ip, password):
    # Salt for PBKDF2
    salt = bytearray.fromhex("77232469666931323429396D656F3938574946")
    # Initialization vector for CBC
    iv = bytes(bytearray.fromhex("72c4721ae01ae0e8e84bd64ad66060c4"))
    
    # Generate key from IP address
    key = hashlib.pbkdf2_hmac("sha1", ip.encode("utf8"), salt, 100, dklen=32)
    
    # Encrypt password
    cipher = Cipher(algorithms.AES(key),
                    modes.CBC(iv),
                    backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padding(password)) + encryptor.finalize()
    
    # Encode to Base64
    ciphertext_b64 = base64.b64encode(ciphertext)
    
    return ciphertext_b64


# Read a jsonp string.
def read_jsonp(jsonp):
  jsonp_stripped = jsonp[ jsonp.index("(")+1 : jsonp.rindex(")") ]
  return json.loads(jsonp_stripped)

# Get the state of the connection from the server
def get_state():
  url = 'https://servicoswifi.apps.meo.pt/HotspotConnection.asmx/GetState?callback=foo&mobile=false&pagePath=foo'
  response = requests.get(url)
  state = read_jsonp(response.content.decode(response.encoding))
  return state

# Get our LAN IP address
def get_ip():
  # It's included in the connection state. That's where the web interface gets it, too.
  state = get_state()
  return state["FrammedIp"]

# Make a GET request with the required data to login to a MEO Wifi Premium Hotspot
def meo_wifi_login(username, password):
  ip = get_ip()
  encrypted_password = encrypt_password(ip, password)
  url ='https://servicoswifi.apps.meo.pt/HotspotConnection.asmx/Login?username=' + username+ '&password=' + encrypted_password + '&navigatorLang=pt&callback=foo'
  response = requests.get(url)

  return response

# Make a GET request to logoff from a MEO Wifi Premium Hotspot
def meo_wifi_logoff():
  url = 'https://servicoswifi.apps.meo.pt/HotspotConnection.asmx/Logoff?callback=foo'
  response = requests.get(url)

  return response

def main():
  # Retrieve environment variables
  user=os.getenv('MEO_WIFI_USER', '')
  passwd=os.getenv('MEO_WIFI_PASSWORD', '')

  # Parse the arguments
  opts, args = getopt.getopt(sys.argv[1:], "hxu:p:")
  for (opt, arg) in opts:
    if opt == '-h':
      print sys.argv[0] + '-u <login user> -p <login password>'
      sys.exit()
    elif opt == '-x':
      print 'Logging off...'
      print meo_wifi_logoff()
      sys.exit()
    elif opt == '-u':
      user = arg
    elif opt == '-p':
      passwd = arg

  # Determine if user and passwords were specified (and ask for them if not)
  if not user:
    user=raw_input('Introduza o e-mail Cliente MEO: ')
  if not passwd:
    passwd=getpass.getpass('Introduza a password Cliente MEO (' + user + '): ')

  # After gathering the necessary data, execute the request
  print meo_wifi_login(user,passwd)

if __name__ == '__main__':
  main()

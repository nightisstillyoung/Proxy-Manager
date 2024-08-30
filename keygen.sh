#!/usr/bin/bash

# from src
KEYDIR='src/auth_jwt/keys/'

# make dir
mkdir ${KEYDIR} || true

# generate an RSA private key
openssl genrsa -out ${KEYDIR}jwt-private.pem 2048

# generate an RSA public key
openssl rsa -in ${KEYDIR}jwt-private.pem -outform PEM -pubout -out ${KEYDIR}jwt-public.pem

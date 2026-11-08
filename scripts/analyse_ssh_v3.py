#!/usr/bin/env python3
# analyse_ssh_v3.py - échecs SSH par IP, énumération, force brute et détection de compromission
# Auteur : Patrick Kassi - Parcours Analyste SOC

FICHIER = "auth.log"

echecs = {}        # IP -> nombre d'échecs
inexistants = {}   # compte inexistant -> nombre d'essais
existants = {}     # compte existant -> nombre d'essais
succes = []        # liste des connexions réussies : (horodatage, compte, ip)

for ligne in open(FICHIER):
    if "sshd" in ligne and "Failed password" in ligne:
        mots = ligne.split()
        ip = mots[-4]
        echecs[ip] = echecs.get(ip, 0) + 1

        if "invalid user" in ligne:
            compte = mots[mots.index("user") + 1]
            inexistants[compte] = inexistants.get(compte, 0) + 1
        else:
            compte = mots[mots.index("for") + 1]
            existants[compte] = existants.get(compte, 0) + 1
    if "sshd" in ligne and "Accepted" in ligne:
        mots = ligne.split()
        horodatage =  mots[0]
        compte = mots[mots.index("for") + 1]
        ip =  mots[-4]
        succes.append((horodatage, compte, ip))

print("=== Échecs SSH par IP source ===")
for ip in sorted(echecs, key=echecs.get, reverse=True):
    print(ip, ":", echecs[ip], "échec(s)")

print()
print("=== Comptes INEXISTANTS visés (énumération) ===")
for compte in sorted(inexistants, key=inexistants.get, reverse=True):
    print(compte, ":", inexistants[compte], "essai(s)")

print()
print("=== Comptes EXISTANTS visés (force brute) ===")
for compte in sorted(existants, key=existants.get, reverse=True):
    print(compte, ":", existants[compte], "essai(s)")

print()
print("=== Connexions RÉUSSIES ===")
for horodatage, compte, ip in succes:
    if ip in echecs:
        print("ALERTE : compte", compte, "compromis depuis", ip, "à", horodatage, "après", echecs[ip], "échec(s)")
    else:
        print("OK :", horodatage, compte, "depuis", ip)
